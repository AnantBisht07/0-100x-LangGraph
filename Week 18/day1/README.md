# Feedback-Aware Evaluation Pipeline

A modular pipeline that executes an LLM call, captures user feedback, and stores everything in a structured append-only JSON log. Designed as the foundation for evaluation loops and prompt optimization.

---

## File Structure

```
Week 18/day1/
├── main.py               ← Entry point. Collects user input and runs the pipeline.
├── agent_executor.py     ← Orchestrates the full run: LLM call, feedback, logging.
├── run_metadata.py       ← Generates run_id, timestamp, prompt_version, model_name.
├── run_logger.py         ← Appends structured entries to runs_log.json.
├── feedback_collector.py ← Collects and validates a 1–5 rating + comment.
├── requirements.txt      ← openai, python-dotenv
├── .env                  ← API keys (not committed to version control)
└── runs_log.json         ← Auto-created on first run. Append-only log.
```

---

## How to Run

```bash
pip install -r requirements.txt
python main.py
```

---

## Pipeline Flow

```
┌────────────────────────────────────────────────────────────────┐
│                          main.py                               │
│   User enters query + selects prompt version (v1.0/v2.0/v3.0) │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                     agent_executor.py                          │
│                                                                │
│   1. Validates prompt_version against PROMPT_VERSIONS dict     │
│   2. Reads API key from .env via os.getenv()                   │
│        │                                                        │
│        ▼                                                        │
│   3. run_metadata.py                                           │
│      └─ Generates run_id (UUID), timestamp (UTC)               │
│         stores prompt_version + model_name                     │
│        │                                                        │
│        ▼                                                        │
│   4. OpenAI client call (via OpenRouter)                       │
│      └─ Measures latency with time.perf_counter()              │
│      └─ Extracts output text + token usage                     │
│        │                                                        │
│        ▼                                                        │
│   5. feedback_collector.py                                     │
│      └─ Prompts user for rating (1–5) + optional comment       │
│        │                                                        │
│        ▼                                                        │
│   6. Assembles full log entry dict                             │
│      └─ Merges metadata + input/output + latency + tokens      │
│      └─ Conditionally adds token_usage and feedback fields     │
│        │                                                        │
│        ▼                                                        │
│   7. run_logger.py                                             │
│      └─ Loads existing runs_log.json                           │
│      └─ Appends new entry                                      │
│      └─ Rewrites full file                                     │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                       runs_log.json                            │
│   Append-only array of structured run records                  │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│           compute_average_rating()  (optional)                 │
│   Groups all logged runs by prompt_version                     │
│   Computes average rating per version                          │
│   → This is the start of an evaluation loop                    │
└────────────────────────────────────────────────────────────────┘
```

---

## Log Entry Structure

```json
{
  "run_id": "3f7a2c91-...",
  "timestamp": "2026-02-27T10:45:00+00:00",
  "prompt_version": "v1.0",
  "model": "openai/gpt-4o-mini",
  "input": "Explain what a context window is",
  "output": "A context window is the maximum amount of text...",
  "latency_seconds": 1.2341,
  "token_usage": {
    "prompt_tokens": 45,
    "completion_tokens": 87,
    "total_tokens": 132
  },
  "feedback": {
    "rating": 4,
    "comment": "Clear and concise"
  }
}
```

---

## Prompt Versions

| Version | System Prompt |
|---------|--------------|
| v1.0 | You are a concise assistant. |
| v2.0 | You are a detailed, structured assistant. |
| v3.0 | You are an expert-level assistant with reasoning clarity. |

---

## Evaluation Loop Concept

Every run writes a complete, self-contained record. Once enough runs are logged, `compute_average_rating()` groups them by prompt version and computes average user ratings — giving you a measurable, data-driven way to compare which system prompt performs best.

```
Prompt v1.0  →  avg rating: 3.4  (n=12 runs)
Prompt v2.0  →  avg rating: 4.1  (n=9 runs)
Prompt v3.0  →  avg rating: 4.6  (n=7 runs)
```

This is how prompt optimization begins: not by guessing, but by measuring.
