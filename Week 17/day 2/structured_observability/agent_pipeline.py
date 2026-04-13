"""
agent_pipeline.py — 3-Step AI Agent Pipeline with Step-Level Observability
===========================================================================

PIPELINE SHAPE:
    User Input
        |
    router_step     — decides the intent: "search" or "explain"
        |
    tool_step       — mock external API call (runs only on "search")
        |
    llm_step        — LLM generates the final response with optional context
        |
    Final Output

WHY STEPS ARE INDEPENDENTLY LOGGED:
Each step is a discrete unit of work. If the pipeline fails at step 2,
step 1's log entry already exists with status "success" and its output.
You can reconstruct exactly what state was handed to the failing step —
without rerunning anything.

This is the core value of step-level observability: full trace reconstruction
from structured logs alone.

DEBUGGING FLAG:
    BREAK_ROUTER = False   (normal operation)
    BREAK_ROUTER = True    (forces router to return a wrong label)

Use BREAK_ROUTER = True to intentionally corrupt the routing decision,
then inspect step_logs.json to see exactly which step produced bad output
and what it received as input.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

from run_logger import RunLogger

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

load_dotenv(Path(__file__).parent / ".env")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# OpenRouter base URL — drop-in replacement for the OpenAI endpoint.
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Default model. Any OpenRouter model ID works here.
DEFAULT_MODEL = "openai/gpt-4o-mini"

# ---------------------------------------------------------------------------
# DEBUGGING FLAG
# ---------------------------------------------------------------------------
# Set BREAK_ROUTER = True to inject a routing fault.
# The router will return "search" regardless of query content.
# Inspect step_logs.json to trace where the pipeline reasoning broke.
BREAK_ROUTER: bool = False


# ---------------------------------------------------------------------------
# Step 1 — Router
# ---------------------------------------------------------------------------

def router_step(logger: RunLogger, query: str) -> str:
    """
    Inspect the user query and decide which processing route to take.

    Routes:
        "search"  — query contains the word "search" (needs external data)
        "explain" — all other queries (LLM answers from its own knowledge)

    WHY LOG THIS STEP:
    Routing is the first decision in the pipeline. If the wrong route is
    chosen, every downstream step operates on a false premise. Logging the
    router's input and decision makes this the easiest failure to diagnose.

    Args:
        logger: Shared RunLogger for this pipeline run.
        query:  The raw user query string.

    Returns:
        Route label: "search" or "explain".

    Raises:
        Exception: Any unexpected error is logged then re-raised.
    """
    start = time.perf_counter()
    step = "router"

    try:
        # Intentional fault injection point for debugging drills.
        if BREAK_ROUTER:
            # Return a hardcoded wrong label regardless of query.
            # Useful for demonstrating how a routing bug propagates through logs.
            decision = "search"
        else:
            decision = "search" if "search" in query.lower() else "explain"

        latency = time.perf_counter() - start
        logger.log_step(
            step_name=step,
            input_data={"query": query},
            output_data={"decision": decision, "break_router_active": BREAK_ROUTER},
            latency_seconds=latency,
            status="success",
        )
        return decision

    except Exception as exc:
        latency = time.perf_counter() - start
        logger.log_step(
            step_name=step,
            input_data={"query": query},
            output_data=None,
            latency_seconds=latency,
            status="error",
            error=str(exc),
        )
        raise


# ---------------------------------------------------------------------------
# Step 2 — Tool Step (Mock External API)
# ---------------------------------------------------------------------------

def tool_step(logger: RunLogger, route: str, query: str) -> Optional[str]:
    """
    Simulate an external API call when the route is "search".

    WHY SIMULATE LATENCY:
    Real external tools (search APIs, databases, web scrapers) have
    non-trivial latency. The 0.5s sleep here makes the latency log entry
    realistic and teaches students to look for slow steps in the trace.

    WHY LOG BOTH ROUTE AND QUERY:
    The tool step receives two inputs: what it was told to do (route) and
    what the user originally asked (query). Logging both allows you to
    verify that the route matched the query intent when debugging.

    Args:
        logger: Shared RunLogger for this pipeline run.
        route:  Decision from the router ("search" or "explain").
        query:  The original user query (passed through for context logging).

    Returns:
        Mock API response string if route == "search", else None.

    Raises:
        Exception: Any unexpected error is logged then re-raised.
    """
    start = time.perf_counter()
    step = "tool_call"

    try:
        if route == "search":
            # Simulate external API latency.
            time.sleep(0.5)
            tool_output = (
                f"[Mock Search API] Top result for '{query}': "
                "According to recent sources, this topic covers key concepts "
                "including definitions, use cases, and best practices. "
                "Source: mock-search-engine.example.com"
            )
        else:
            # No external tool needed for "explain" route.
            tool_output = None

        latency = time.perf_counter() - start
        logger.log_step(
            step_name=step,
            input_data={"route": route, "query": query},
            output_data={"tool_response": tool_output},
            latency_seconds=latency,
            status="success",
        )
        return tool_output

    except Exception as exc:
        latency = time.perf_counter() - start
        logger.log_step(
            step_name=step,
            input_data={"route": route, "query": query},
            output_data=None,
            latency_seconds=latency,
            status="error",
            error=str(exc),
        )
        raise


# ---------------------------------------------------------------------------
# Step 3 — LLM Step
# ---------------------------------------------------------------------------

def llm_step(
    logger: RunLogger,
    query: str,
    tool_output: Optional[str],
) -> str:
    """
    Call the LLM to generate the final response.

    The system prompt is fixed. If tool_output is available (search route),
    it is injected into the user message as context so the LLM can ground
    its answer in the retrieved data.

    WHY LOG THE SYSTEM PROMPT:
    The system prompt is part of every LLM call's inputs. Logging it means
    every response is traceable back to exactly which instructions the model
    received. When a response is wrong, you can verify whether the fault was
    in the instructions, the context, or the model itself.

    Args:
        logger:      Shared RunLogger for this pipeline run.
        query:       The original user query.
        tool_output: Retrieved context from tool_step, or None.

    Returns:
        The LLM's response text as a plain string.

    Raises:
        Exception: Any unexpected error is logged then re-raised.
    """
    start = time.perf_counter()
    step = "llm"

    system_prompt = (
        "You are a clear and concise assistant. "
        "Answer the user's question directly. "
        "If context is provided, use it to ground your answer."
    )

    # Build user message — inject tool context when available.
    if tool_output:
        user_message = (
            f"Question: {query}\n\n"
            f"Context from search:\n{tool_output}\n\n"
            "Please answer the question using the context above."
        )
    else:
        user_message = query

    try:
        client = OpenAI(
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url=OPENROUTER_BASE_URL,
        )

        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
        )

        output_text: str = response.choices[0].message.content or ""
        latency = time.perf_counter() - start

        # Token usage is optional — present only when the provider returns it.
        token_usage = None
        if response.usage:
            token_usage = {
                "prompt_tokens":     response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens":      response.usage.total_tokens,
            }

        logger.log_step(
            step_name=step,
            input_data={
                "system_prompt": system_prompt,
                "user_message":  user_message,
                "tool_context_present": tool_output is not None,
            },
            output_data={
                "response":    output_text,
                "token_usage": token_usage,
            },
            latency_seconds=latency,
            status="success",
        )
        return output_text

    except Exception as exc:
        latency = time.perf_counter() - start
        logger.log_step(
            step_name=step,
            input_data={
                "system_prompt": system_prompt,
                "user_message":  user_message,
            },
            output_data=None,
            latency_seconds=latency,
            status="error",
            error=str(exc),
        )
        raise


# ---------------------------------------------------------------------------
# Pipeline Runner
# ---------------------------------------------------------------------------

def run_pipeline(query: str) -> dict:
    """
    Execute the full 3-step pipeline for a given user query.

    Each step shares the same RunLogger instance, which means they all
    share the same run_id. This is the thread that ties the full trace
    together: filter step_logs.json by run_id to see every step of
    exactly this execution.

    Args:
        query: The user's input string.

    Returns:
        A dict containing:
            run_id   — the trace ID for this execution
            output   — the final LLM response
            status   — "success" or "error"
            error    — error message if status is "error", else None

    Raises:
        Nothing — all exceptions are caught, logged, and returned in the dict.
    """
    logger = RunLogger()

    try:
        # Step 1 — Route the query.
        route = router_step(logger, query)

        # Step 2 — Optionally call the external tool.
        tool_output = tool_step(logger, route, query)

        # Step 3 — Generate the final LLM response.
        final_output = llm_step(logger, query, tool_output)

        return {
            "run_id": logger.run_id,
            "output": final_output,
            "status": "success",
            "error":  None,
        }

    except Exception as exc:
        # Pipeline-level catch: the failing step already logged itself.
        # This entry records that the pipeline as a whole did not complete.
        return {
            "run_id": logger.run_id,
            "output": None,
            "status": "error",
            "error":  str(exc),
        }
