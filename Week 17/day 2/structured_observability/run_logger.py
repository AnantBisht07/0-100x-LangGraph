"""
run_logger.py — Step-Level Structured Logger
=============================================

WHY STEP-LEVEL LOGGING MATTERS:
A single run_id tells you that something happened.
Step-level logs tell you exactly WHERE, WHEN, and WHY it happened.

In a multi-step pipeline, the question is never just "did it fail?" —
it is "which step failed, what was its input, and how long did it run
before failing?" Without step-level traces you are debugging blindly.

This module owns one responsibility: write structured, append-only,
step-level log entries to a JSON file. Nothing else.

DESIGN DECISIONS:
- run_id is generated once per pipeline run, shared across all steps.
- Each step gets its own timestamped entry — steps are individually queryable.
- Error fields are always present in the schema (null when no error).
- Log file is read → appended → rewritten to maintain valid JSON array.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Default location: same folder as this file.
# Caller may override by passing a custom log_path to RunLogger.
LOG_FILE = Path(__file__).parent / "step_logs.json"


class RunLogger:
    """
    Generates a unique run_id and writes structured step entries to disk.

    One RunLogger instance should be created per pipeline run.
    Pass the same instance to every step so they all share the same run_id.

    Usage:
        logger = RunLogger()
        logger.log_step("router", input_data="...", output_data="...", ...)
    """

    def __init__(
        self,
        run_id: Optional[str] = None,  # 2 patterns here -> 1). you provide your own run_id.. 2). auto generate the run_id.
        log_path: Path = LOG_FILE,
    ) -> None:
        # Accept an external run_id (useful for tests) or generate a fresh one.
        self.run_id: str = run_id or str(uuid.uuid4())
        self.log_path = log_path

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def log_step(
        self,
        step_name: str, # router/tool call/llm
        input_data: Any, # query
        output_data: Any, # final answer
        latency_seconds: float, 
        status: str,
        error: Optional[str] = None,
    ) -> dict:
        """
        Write one structured step entry and return it.

        Args:
            step_name:        Human-readable name of the pipeline step
                              (e.g. "router", "tool_call", "llm").
            input_data:       The input received by this step.
                              Can be any JSON-serialisable value.
            output_data:      The output produced by this step.
                              None when the step errored before producing output.
            latency_seconds:  Wall-clock time measured with perf_counter.
            status:           "success" or "error".
            error:            Error message string if status is "error", else None.

        Returns:
            The entry dict that was written to disk.
        """
        entry = {
            "run_id":           self.run_id,
            "step_name":        step_name,
            "input":            input_data,
            "output":           output_data,
            "latency_seconds":  round(latency_seconds, 4),
            "status":           status,
            "error":            error,
            "timestamp":        datetime.now(timezone.utc).isoformat(),
        }
        self._append(entry)
        return entry

    def load_all(self) -> list[dict]:
        """Return every logged entry across all runs."""
        return self._load_existing()

    def load_run(self, run_id: Optional[str] = None) -> list[dict]:
        """
        Return all step entries for a specific run_id.
        Defaults to this logger's own run_id.
        """
        target = run_id or self.run_id
        return [e for e in self._load_existing() if e.get("run_id") == target]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_existing(self) -> list[dict]:
        """Read the log file and return its contents as a list."""
        if not self.log_path.exists():
            return []
        try:
            with self.log_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            # Corrupted file — return empty rather than crash.
            return []

    def _append(self, entry: dict) -> None:
        """
        Read existing entries, append the new one, rewrite the file.

        WHY NOT A SIMPLE FILE APPEND?
        JSON requires the file to be a valid array [...].
        A raw append would break the structure. Read-modify-write keeps
        the file always valid and readable by any JSON parser.
        """
        entries = self._load_existing()
        entries.append(entry)
        with self.log_path.open("w", encoding="utf-8") as fh:
            json.dump(entries, fh, indent=2, ensure_ascii=False)
