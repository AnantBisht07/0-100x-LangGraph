# Feedback-Aware Run Tracker

> Production observability pipeline for AI agent runs.
> Every call is traced. Every response is rated. Every run is logged.

---
# what is python - me(anant) 

# what is fastapi

# what is langchain

# what is ai agents

## What Is This?

When you call an AI model, three things happen and then disappear forever:

1. A prompt was sent
2. A response came back
3. The user had a reaction to it

Without a system in place, you cannot answer:
- Which version of the prompt produced that answer?
- How long did it take?
- Did the user find it useful?
- Which model performed better?

The **Feedback-Aware Run Tracker** captures all of that — automatically,
every single time — and stores it as structured JSON you can query, compare,
and build evaluations on top of.

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add your OpenRouter API key
cp .env.example .env
# then open .env and paste your key

# 3. Run the demo
python run_tracker.py
```

Get your OpenRouter key at: https://openrouter.ai/keys

---

## What Happens When You Run It

```
============================================================
  Feedback-Aware Run Tracker — Demo
============================================================

[Example 1] Single tracked run with feedback

[run_id: 03249b6f-8db6-4fb3-9a09-f8d34e8acfc4]
Response:
Observability is the ability to infer the internal state of a system...

--- Feedback ---
Rate this response (1-5): 4
Optional comment (press Enter to skip): Good, but brief

[Logged] Run 03249b6f saved to runs_log.json

[Example 2] Prompt version A/B comparison
...
```

Every run produces a structured JSON entry saved to `runs_log.json`:

```json
{
  "run_id": "03249b6f-8db6-4fb3-9a09-f8d34e8acfc4",
  "timestamp": "2026-02-21T10:30:00+00:00",
  "prompt_version": "v1.0",
  "model": "openai/gpt-4o-mini",
  "input": "Explain observability in three sentences.",
  "output": "Observability is the ability to infer...",
  "latency_seconds": 1.2347,
  "token_usage": {
    "prompt_tokens": 45,
    "completion_tokens": 87,
    "total_tokens": 132
  },
  "feedback": {
    "rating": 4,
    "comment": "Good, but brief"
  }
}
```

---

## Features

| Feature | Description |
|---------|-------------|
| Unique run IDs | Every run gets a UUID — globally traceable forever |
| Prompt versioning | System prompts tracked as `v1.0`, `v2.0`, etc. |
| Latency tracking | Wall-clock time measured with `perf_counter` |
| Token usage | Prompt, completion, and total tokens logged per run |
| User feedback | 1-5 rating + optional comment captured after each response |
| Append-only log | `runs_log.json` — nothing is ever overwritten |
| A/B comparison | Run the same query under two prompt versions, compare side-by-side |




## Components

```
RunMetadata          Generates run_id (UUID), timestamp (UTC),
                     stores prompt version and model name.

RunLogger            Reads runs_log.json → appends new entry →
                     rewrites file. Safe, append-only.

FeedbackCollector    Interactive 1-5 rating + optional comment
                     captured immediately after the response.

run_agent_with_tracking()
                     The single entry point that ties all four
                     components together into one pipeline call.

compare_prompt_versions()
                     Runs the same query under two prompt versions,
                     logs both, prints a side-by-side summary.
```

---

## Prompt Versions

Prompts are treated as versioned assets — not raw strings buried in code.

```python
PROMPT_VERSIONS = {
    "v1.0": "You are a helpful assistant. Answer concisely and accurately.",
    "v2.0": "You are an expert assistant. Provide thorough, well-structured answers...",
}
```

To add a new version:

```python
"v3.0": "You are a specialist in [domain]. Always cite your reasoning..."
```

Then run an A/B comparison:

```python
compare_prompt_versions(
    query="Your question here",
    version_a="v2.0",
    version_b="v3.0",
)
```

---

## Switching Models

Any OpenRouter model works — change one line:

```python
run_agent_with_tracking(
    input_text="Your question",
    model="anthropic/claude-3-haiku",      # or any OpenRouter model ID
)
```

Popular models on OpenRouter:

```
openai/gpt-4o-mini
openai/gpt-4o
anthropic/claude-3-haiku
anthropic/claude-3.5-sonnet
meta-llama/llama-3-8b-instruct
google/gemini-flash-1.5
```

---

## Reading Your Logs

Open `runs_log.json` in any text editor or parse it in Python:

```python
import json

with open("runs_log.json") as f:
    runs = json.load(f)

for run in runs:
    print(f"{run['run_id']}  |  {run['prompt_version']}  |  rating: {run.get('feedback', {}).get('rating', 'n/a')}")
```

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `openai` | >= 1.0.0 | OpenAI-compatible SDK (used for OpenRouter) |
| `python-dotenv` | latest | Load API key from `.env` file |

---

## What This Is NOT

- Not a database — data lives in a local JSON file
- Not an external observability tool (no LangSmith, no Weights & Biases)
- Not a production-scale system — designed for learning and local evaluation

This is the **foundation**. The same structure (run_id, metadata, feedback)
is what every serious AI evaluation system is built on top of.

---

## Next Steps

This project is **Step 1** of a full AI evaluation pipeline:

```
Step 1 (This project) — Collect runs + feedback
Step 2              — Score runs with LLM-as-judge
Step 3              — Compare prompt versions statistically
Step 4              — Build a quality dashboard
Step 5              — Integrate into a LangGraph pipeline
```
