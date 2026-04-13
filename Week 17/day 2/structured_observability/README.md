# Structured Observability Pipeline

> A multi-step AI agent pipeline with step-level execution tracing.
> Every step is logged. Every failure is captured. Every run is fully reconstructable.

---

## What Is This?

Most AI pipelines are black boxes. You send a query in, an answer comes out,
and if something goes wrong you have no idea which step failed, what it received
as input, or how long it ran before breaking.

This pipeline solves that. Every step — router, tool call, LLM — writes a
structured log entry the moment it completes. If the pipeline breaks at step 2,
step 1's log already exists with `status: "success"` and its full output.
You can reconstruct the exact state that was handed to the failing step
without rerunning anything.

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add your OpenRouter API key
copy .env.example .env
# open .env and paste your key

# 3. Run
python main.py
```

---

## What Happens When You Run It

```
================================================================
  Structured Observability Pipeline
================================================================
Enter your query: search for machine learning basics

[pipeline] Running...

================================================================
RESPONSE:
Machine learning is a subset of AI that enables systems to learn...
================================================================

Run ID : a3f1b2c4-7d8e-4f9a-b0c1-d2e3f4a5b6c7
Status : success
Log    : step_logs.json

================================================================
  TRACE: a3f1b2c4-7d8e-4f9a-b0c1-d2e3f4a5b6c7
  Steps: 3
================================================================

Step 1 — [OK]   ROUTER
  Timestamp : 2026-02-21T10:30:00+00:00
  Latency   : 0.0001s
  Input.query          : search for machine learning basics
  Output.decision      : search

Step 2 — [OK]   TOOL_CALL
  Timestamp : 2026-02-21T10:30:00+00:00
  Latency   : 0.5021s
  Input.route          : search
  Output.tool_response : [Mock Search API] Top result for '...'

Step 3 — [OK]   LLM
  Timestamp : 2026-02-21T10:30:02+00:00
  Latency   : 1.8734s
  Input.tool_context_present : True
  Output.response      : Machine learning is a subset of AI...
```

---

## Pipeline Steps

```
User Input
    |
    v
[Step 1] router_step     — keyword detection: "search" or "explain" # intent detection
    |
    v
[Step 2] tool_step       — mock external API (runs only on "search" route)
    |
    v
[Step 3] llm_step        — LLM call with optional tool context injected
    |
    v
Final Output + Step Trace
```

### Step 1 — Router

Reads the query. If it contains `"search"` → routes to `"search"`.
Otherwise → routes to `"explain"`. Logs the input query and decision.

### Step 2 — Tool Call

If route is `"search"`: simulates an external API call with a 0.5s delay
and returns mock search results. If route is `"explain"`: returns `None`
immediately. Logs route, query, and API response.

### Step 3 — LLM

Calls the LLM via OpenRouter. If tool output is available, it is injected
into the user message as grounding context. Logs the system prompt, full
user message, response, and token usage.

---

## Log Format

Every step writes one entry to `step_logs.json`:

**Success entry:**
```json
{
  "run_id": "a3f1b2c4-...",
  "step_name": "router",
  "input": { "query": "search for ML basics" },
  "output": { "decision": "search", "break_router_active": false },
  "latency_seconds": 0.0001,
  "status": "success",
  "error": null,
  "timestamp": "2026-02-21T10:30:00+00:00"
}
```

**Error entry:**
```json
{
  "run_id": "a3f1b2c4-...",
  "step_name": "tool_call",
  "input": { "route": "search", "query": "..." },
  "output": null,
  "latency_seconds": 0.012,
  "status": "error",
  "error": "Connection timeout",
  "timestamp": "2026-02-21T10:30:01+00:00"
}
```

---

## Debugging: Inject a Fault

Open [agent_pipeline.py](agent_pipeline.py) and flip:

```python
BREAK_ROUTER = True
```

The router now returns `"search"` for every query — even ones that
should go to `"explain"`. Run the pipeline, then open `step_logs.json`
and look at the router entry. The field `"break_router_active": true`
tells you the fault was injected. The tool step fires unnecessarily.
The LLM receives irrelevant search context.

This is a controlled way to practice trace-based debugging:
find the fault, identify which step propagated it, and understand
the downstream impact — all from the log file alone.

Set `BREAK_ROUTER = False` to restore normal operation.

---

## Trace Reconstruction

`print_trace_for_run(run_id)` is called automatically after every run.
You can also call it manually from Python:

```python
from main import print_trace_for_run
print_trace_for_run("a3f1b2c4-7d8e-4f9a-b0c1-d2e3f4a5b6c7")
```

Or query the log file directly:

```python
import json

with open("step_logs.json") as f:
    logs = json.load(f)

run_id = "a3f1b2c4-..."
steps = [e for e in logs if e["run_id"] == run_id]
for step in steps:
    print(step["step_name"], step["status"], step["latency_seconds"])
```

---

## Switching Models

Any OpenRouter model ID works:

```python
# in agent_pipeline.py
DEFAULT_MODEL = "anthropic/claude-3-haiku"
DEFAULT_MODEL = "meta-llama/llama-3-8b-instruct"
DEFAULT_MODEL = "openai/gpt-4o"
```

---

## Project Structure

```
structured_observability/
├── run_logger.py       Step-level logger — RunLogger class
├── agent_pipeline.py   3-step pipeline — router, tool, LLM
├── main.py             CLI entry point + trace visualiser
├── step_logs.json      Auto-created append-only trace log
├── requirements.txt    openai, python-dotenv
├── .env                Your API key (never commit)
└── .env.example        Key name template
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `openai` | OpenAI-compatible SDK — used with OpenRouter |
| `python-dotenv` | Load `OPENROUTER_API_KEY` from `.env` |
