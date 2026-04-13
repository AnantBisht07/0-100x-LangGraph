"""
main.py — CLI Entry Point + Trace Visualiser
=============================================

This is the user-facing entry point for the Structured Observability Pipeline.

It does two things:
    1. Runs the pipeline for a user query and prints the result.
    2. Provides print_trace_for_run() — a trace visualiser that reconstructs
       the full step-by-step execution history for any run_id.

WHY A TRACE VISUALISER:
step_logs.json grows across many runs. print_trace_for_run() filters it to
a single run and prints the steps in order — simulating what a real
observability platform (Jaeger, Honeycomb, LangSmith) would show you.
The difference is: you built this yourself with zero external dependencies.
"""

from __future__ import annotations

import json
from pathlib import Path

from agent_pipeline import run_pipeline, BREAK_ROUTER
from run_logger import LOG_FILE


# ---------------------------------------------------------------------------
# BONUS: Trace Visualiser
# ---------------------------------------------------------------------------

def print_trace_for_run(run_id: str) -> None:
    """
    Read step_logs.json, filter by run_id, and print an ordered step trace.

    This simulates trace reconstruction — the core feature of any
    observability platform. Given only a run_id (e.g. from a bug report),
    you can see exactly what happened, step by step, with inputs, outputs,
    latency, and errors.

    Args:
        run_id: The UUID of the pipeline run to inspect.
    """
    if not LOG_FILE.exists():
        print("[trace] No log file found. Run the pipeline first.")
        return

    try:
        with LOG_FILE.open("r", encoding="utf-8") as fh:
            all_entries: list[dict] = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[trace] Could not read log file: {exc}")
        return

    # Filter to this run's steps only.
    run_entries = [e for e in all_entries if e.get("run_id") == run_id]

    if not run_entries:
        print(f"[trace] No entries found for run_id: {run_id}")
        return

    # ---------------------------------------------------------------------------
    # Print the trace
    # ---------------------------------------------------------------------------
    divider = "=" * 64
    print(f"\n{divider}")
    print(f"  TRACE: {run_id}")
    print(f"  Steps: {len(run_entries)}")
    print(divider)

    for i, entry in enumerate(run_entries, start=1):
        status_label = "[OK]   " if entry["status"] == "success" else "[FAIL] "
        print(f"\nStep {i} — {status_label}{entry['step_name'].upper()}")
        print(f"  Timestamp : {entry['timestamp']}")
        print(f"  Latency   : {entry['latency_seconds']}s")
        print(f"  Status    : {entry['status']}")

        # Input — pretty print if it's a dict, else raw
        inp = entry.get("input")
        if isinstance(inp, dict):
            for k, v in inp.items():
                # Truncate long values for readability
                val_str = str(v)
                if len(val_str) > 120:
                    val_str = val_str[:120] + "..."
                print(f"  Input.{k:<14}: {val_str}")
        else:
            print(f"  Input     : {inp}")

        # Output — same treatment
        out = entry.get("output")
        if isinstance(out, dict):
            for k, v in out.items():
                val_str = str(v)
                if len(val_str) > 120:
                    val_str = val_str[:120] + "..."
                print(f"  Output.{k:<13}: {val_str}")
        else:
            print(f"  Output    : {out}")

        # Error — only shown when present
        if entry.get("error"):
            print(f"  [ERROR]   : {entry['error']}")

    print(f"\n{divider}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """
    CLI entry point.

    Prompts the user for a query, runs the full pipeline, prints the
    final response, and then prints the complete step trace for that run.

    The trace is printed automatically after every run so students can
    immediately see what was logged at each step without manually
    opening step_logs.json.
    """
    divider = "=" * 64
    print(f"\n{divider}")
    print("  Structured Observability Pipeline")
    print(f"{divider}")

    if BREAK_ROUTER:
        print("\n[WARNING] BREAK_ROUTER is active — router will return wrong label.")
        print("          Inspect the trace to see how the fault propagates.\n")

    query = input("Enter your query: ").strip()
    if not query:
        print("[error] Query cannot be empty.")
        return

    print(f"\n[pipeline] Running... (run will be traced to step_logs.json)")

    result = run_pipeline(query)

    print(f"\n{divider}")
    if result["status"] == "success":
        print("RESPONSE:")
        print(result["output"])
    else:
        print(f"[PIPELINE ERROR]: {result['error']}")
    print(divider)

    print(f"\nRun ID : {result['run_id']}")
    print(f"Status : {result['status']}")
    print(f"Log    : step_logs.json")

    # Automatically print the trace for this run.
    print_trace_for_run(result["run_id"])


if __name__ == "__main__":
    main()
