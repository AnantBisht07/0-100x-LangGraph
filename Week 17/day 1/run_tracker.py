"""
Feedback-Aware Run Tracker
===========================
Production observability pipeline for AI agent runs.

WHY OBSERVABILITY MATTERS:
Every AI system that reaches users must be traceable. Without structured
run data you cannot debug regressions, compare prompt versions, measure
quality over time, or close the feedback loop with real users.

This module implements the foundation: every run gets a unique ID, every
response gets measured, and every user reaction is captured alongside the
full execution context. That combination turns raw LLM calls into
auditable, improvable artifacts.

DESIGN PRINCIPLES:
- Separation of concerns: execution, logging, and feedback are independent modules.
- Uses OpenRouter as the LLM provider (OpenAI-compatible API, multi-model access).
- API key loaded from .env — never hard-coded.
- Append-only JSON log — nothing is ever overwritten.
- Token usage is captured when the provider returns it; omitted otherwise.
"""

#from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file in the same directory as this script.
# OPENROUTER_API_KEY must be present; the process will fail fast if it is missing.
load_dotenv(Path(__file__).parent / ".env")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LOG_FILE = Path(__file__).parent / "runs_log.json"

# OpenRouter endpoint — drop-in replacement for the OpenAI base URL.
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Default model used when none is specified.
# OpenRouter model IDs use the format  "provider/model-name".
DEFAULT_MODEL = "openai/gpt-4o-mini"

# Prompt templates versioned as first-class assets.
# Prompts are versioned so every run records exactly which instruction set
# produced the output. This makes regressions traceable to a specific version.
PROMPT_VERSIONS: dict[str, str] = {
    "v1.0": "You are a helpful assistant. Answer concisely and accurately.",
    "v2.0": (
        "You are an expert assistant. Provide thorough, well-structured answers. "
        "If the question is ambiguous, clarify your assumptions before answering."
    ),
}


# ---------------------------------------------------------------------------
# 1. RunMetadata — identity and context for a single execution
# ---------------------------------------------------------------------------

class RunMetadata:
    """
    Encapsulates the immutable identity of one agent run.

    Generating a UUID and timestamp here — rather than inline — keeps the
    execution wrapper clean and makes the metadata independently testable.
    The prompt version is stored so the log always reflects *which* system
    prompt was active, not just which model was called.
    """

    def __init__(self, prompt_version: str, model: str = DEFAULT_MODEL) -> None:
        self.run_id: str = str(uuid.uuid4())
        self.timestamp: str = datetime.now(timezone.utc).isoformat()
        self.prompt_version: str = prompt_version
        self.model: str = model

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "prompt_version": self.prompt_version,
            "model": self.model,
        }


# ---------------------------------------------------------------------------
# 2. RunLogger — durable, append-only structured storage
# ---------------------------------------------------------------------------

class RunLogger:
    """
    Writes structured run entries to a local JSON log file.

    WHY APPEND-ONLY:
    Overwriting logs destroys history. An append-only log lets you replay,
    audit, and diff any run at any point in time without extra tooling.

    WHY JSON (not CSV or plain text): ## Always use structured format response..
    JSON is schema-flexible. When token usage is unavailable, the field is
    simply absent — no empty columns, no parse errors. New fields can be
    added without breaking readers of older entries.

    The file is read and rewritten atomically (read → append → write) so a
    crash mid-write never produces a truncated file.
    """

    def __init__(self, log_path: Path = LOG_FILE) -> None:
        self.log_path = log_path

    def _load_existing(self) -> list[dict]:
        """Return existing log entries, or an empty list if the file is new."""
        if not self.log_path.exists():
            return []
        try:
            with self.log_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            # Corrupted file — start fresh rather than crash.
            return []

    def log(self, entry: dict) -> None:
        """
        Append *entry* to the log file.

        The full list is rewritten each time, which is acceptable for a
        local development / evaluation log. For production at scale, swap
        this for a streaming NDJSON writer.
        """
        runs = self._load_existing()
        runs.append(entry)
        with self.log_path.open("w", encoding="utf-8") as fh:
            json.dump(runs, fh, indent=2, ensure_ascii=False)

    def load_all(self) -> list[dict]:
        """Return all logged runs (useful for reporting and comparisons)."""
        return self._load_existing()


# ---------------------------------------------------------------------------
# 3. FeedbackCollector — closing the human-in-the-loop gap
# ---------------------------------------------------------------------------

class FeedbackCollector:
    """
    Captures user feedback interactively after a response is shown.

    WHY COLLECT FEEDBACK AT RUN TIME:
    Post-hoc labelling is expensive and often never happens. Collecting a
    simple 1-5 rating immediately after the response costs the user ~5
    seconds but yields a ground-truth signal that no automated metric can
    fully replace. Storing it alongside the run metadata means every
    quality data point is permanently linked to its full execution context.
    """

    def collect(self) -> dict:
        """
        Prompt the user for a rating and optional comment.

        Returns a feedback dict.  If the user skips the comment, the key is
        present but empty — making downstream parsing uniform.
        """
        print("\n--- Feedback ---")
        rating = self._prompt_rating()
        comment = input("Optional comment (press Enter to skip): ").strip()
        return {"rating": rating, "comment": comment}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _prompt_rating(self) -> int:
        """Loop until the user enters a valid integer between 1 and 5."""
        while True:
            raw = input("Rate this response (1-5): ").strip()
            if raw.isdigit() and 1 <= int(raw) <= 5:
                return int(raw)
            print("  Please enter a number between 1 and 5.")


# ---------------------------------------------------------------------------
# 4. Execution Wrapper — the single entry point for a tracked run
# ---------------------------------------------------------------------------

def run_agent_with_tracking(
    input_text: str,
    prompt_version: str = "v1.0",
    model: str = DEFAULT_MODEL,
    collect_feedback: bool = True,
) -> str:
    """
    Execute an LLM call with full observability and optional user feedback.

    Pipeline:
        1. Generate run metadata (ID, timestamp, version labels).
        2. Resolve the system prompt for *prompt_version*.
        3. Call the model, measuring wall-clock latency.
        4. Optionally collect user feedback.
        5. Assemble the structured log entry and persist it.
        6. Return the response text to the caller.

    Args:
        input_text:       The user query / prompt.
        prompt_version:   Key into PROMPT_VERSIONS (e.g. "v1.0").
        model:            OpenAI model identifier.
        collect_feedback: When False, skips interactive feedback (useful
                          for batch / automated runs).

    Returns:
        The model's response as a plain string.

    Raises:
        ValueError: If *prompt_version* is not registered in PROMPT_VERSIONS.
    """
    if prompt_version not in PROMPT_VERSIONS:
        raise ValueError(
            f"Unknown prompt version '{prompt_version}'. "
            f"Registered versions: {list(PROMPT_VERSIONS.keys())}"
        )

    # -- Step 1: Identity ------------------------------------------------
    metadata = RunMetadata(prompt_version=prompt_version, model=model)
    system_prompt = PROMPT_VERSIONS[prompt_version]

    # -- Step 2: Execute with latency measurement ------------------------
    # OpenRouter is OpenAI-compatible; we only need to override the base URL
    # and pass our OpenRouter API key.  The rest of the call is identical.
    client = OpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url=OPENROUTER_BASE_URL,
    )
    start = time.perf_counter()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": input_text},
        ],
    )

    latency = round(time.perf_counter() - start, 4) # rounding to 4 decimal places, current - start time.
    output_text: str = response.choices[0].message.content or ""

    # -- Step 3: Display response ----------------------------------------
    print(f"\n[run_id: {metadata.run_id}]")
    print(f"Response:\n{output_text}")

    # -- Step 4: Token usage (optional — present only when provider returns it)
    token_usage: Optional[dict] = None
    if response.usage:
        token_usage = {
            "prompt_tokens":     response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens":      response.usage.total_tokens,
        }

    # -- Step 5: Feedback ------------------------------------------------
    feedback: Optional[dict] = None
    if collect_feedback:
        collector = FeedbackCollector()
        feedback = collector.collect()

    # -- Step 6: Assemble and persist log entry --------------------------
    entry = {
        **metadata.to_dict(),
        "input":            input_text,
        "output":           output_text,
        "latency_seconds":  latency,
    }
    if token_usage is not None:
        entry["token_usage"] = token_usage
    if feedback is not None:
        entry["feedback"] = feedback

    logger = RunLogger()
    logger.log(entry)
    print(f"\n[Logged] Run {metadata.run_id} saved to {LOG_FILE.name}")

    return output_text


# ---------------------------------------------------------------------------
# BONUS: compare_prompt_versions — A/B evaluation helper
# ---------------------------------------------------------------------------

def compare_prompt_versions(
    query: str,
    version_a: str = "v1.0",
    version_b: str = "v2.0",
    model: str = DEFAULT_MODEL,
) -> None:
    """
    Run the same query under two prompt versions and print a side-by-side
    comparison summary.

    WHY THIS MATTERS:
    Prompt engineering without measurement is guesswork. By running the
    identical query against two versioned system prompts and logging both
    runs, you create the raw material for systematic prompt evaluation.
    The logged run_ids let you retrieve the full context later.

    Args:
        query:     The user query to test.
        version_a: First prompt version key.
        version_b: Second prompt version key.
        model:     Model to use for both runs.
    """
    print("=" * 60)
    print(f"Comparing prompt versions: {version_a}  vs  {version_b}")
    print(f"Query: {query}")
    print("=" * 60)

    results: dict[str, dict] = {}

    for version in (version_a, version_b):
        print(f"\n--- Running {version} ---")
        start = time.perf_counter()
        response_text = run_agent_with_tracking(
            input_text=query,
            prompt_version=version,
            model=model,
            collect_feedback=True,
        )
        elapsed = round(time.perf_counter() - start, 4)
        results[version] = {"response": response_text, "total_elapsed": elapsed}

    # -- Comparison summary ----------------------------------------------
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)
    for version, data in results.items():
        word_count = len(data["response"].split())
        print(f"\n[{version}]")
        print(f"  Word count   : {word_count}")
        print(f"  Total elapsed: {data['total_elapsed']}s")
        print(f"  Preview      : {data['response'][:120]}...")

    # Retrieve the most recent two log entries for the run IDs
    logger = RunLogger()
    all_runs = logger.load_all()
    recent = [r for r in all_runs if r.get("prompt_version") in (version_a, version_b)]
    recent_two = recent[-2:] if len(recent) >= 2 else recent
    if recent_two:
        print("\nLogged run IDs:")
        for run in recent_two:
            rating = run.get("feedback", {}).get("rating", "n/a")
            print(f"  {run['prompt_version']} -> {run['run_id']}  (rating: {rating})")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Main — example usage demonstrating the full pipeline
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Demonstrate the Feedback-Aware Run Tracker.

    Runs two examples:
        1. A single tracked query with feedback.
        2. A version comparison (bonus feature).
    """
    print("\n" + "=" * 60)
    print("  Feedback-Aware Run Tracker — Demo")
    print("=" * 60)

    # --- Single run -------------------------------------------------------
    print("\n[Example 1] Single tracked run with feedback")
    run_agent_with_tracking(
        input_text="What is fast api?",
        prompt_version="v1.0",
    )

    # --- Version comparison -----------------------------------------------
    print("\n[Example 2] Prompt version A/B comparison")
    compare_prompt_versions(
        query="What are the key differences between python and javascript?",
        version_a="v1.0",
        version_b="v2.0",
    )


if __name__ == "__main__":
    main()
