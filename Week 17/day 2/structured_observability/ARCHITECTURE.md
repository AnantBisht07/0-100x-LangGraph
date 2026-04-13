# Architecture — Structured Observability Pipeline

---

## System Overview

The pipeline is a **linear, sequential chain** of three steps. One `RunLogger`
instance is created at the start of each pipeline run and passed into every
step. This shared instance carries the `run_id` that binds all step entries
together into a single traceable execution record.

```
                        User Input (query string)
                               |
                               v
                    ┌─────────────────────┐
                    │     run_pipeline()  │  ← creates RunLogger (run_id)
                    └──────────┬──────────┘
                               |
              ┌────────────────▼────────────────┐
              │          router_step()           │
              │  Input : query                   │
              │  Output: "search" | "explain"    │
              │  Logs  : decision + latency       │
              └────────────────┬────────────────┘
                               |
              ┌────────────────▼────────────────┐
              │           tool_step()            │
              │  Input : route + query           │
              │  Output: mock API result | None  │
              │  Logs  : response + latency      │
              └────────────────┬────────────────┘
                               |
              ┌────────────────▼────────────────┐
              │            llm_step()            │
              │  Input : query + tool_output     │
              │  Output: LLM response text       │
              │  Logs  : prompt + output + tokens│
              └────────────────┬────────────────┘
                               |
                               v
                    ┌─────────────────────┐
                    │  { run_id, output,  │
                    │    status, error }  │
                    └─────────────────────┘
                               |
                               v
                    step_logs.json  (appended)
```

---

## File Responsibilities

```
structured_observability/
│
├── run_logger.py
│   └── RunLogger class
│       ├── __init__()         generates run_id (UUID), sets log path
│       ├── log_step()         builds entry dict, calls _append()
│       ├── load_all()         returns all entries from log file
│       ├── load_run()         filters entries by run_id
│       ├── _load_existing()   reads JSON file safely
│       └── _append()          read → add → rewrite log file
│
├── agent_pipeline.py
│   ├── BREAK_ROUTER           fault injection flag (bool)
│   ├── router_step()          keyword-based intent router
│   ├── tool_step()            mock external API call
│   ├── llm_step()             OpenRouter LLM call
│   └── run_pipeline()         orchestrates all three steps
│
└── main.py
    ├── print_trace_for_run()  reads log, filters by run_id, prints trace
    └── main()                 CLI — prompt → pipeline → print result + trace
```

---

## The RunLogger — Shared Identity Across Steps

The key design decision is that **one RunLogger is created per pipeline run**
and passed into every step function.

```python
# run_pipeline() creates it once
logger = RunLogger()            # run_id = "a3f1b2c4-..."

# Every step receives the same logger
router_step(logger, query)      # logs with run_id "a3f1b2c4-..."
tool_step(logger, route, query) # logs with run_id "a3f1b2c4-..."
llm_step(logger, query, output) # logs with run_id "a3f1b2c4-..."
```

Because all three steps log to the same `run_id`, you can reconstruct the
entire execution by filtering `step_logs.json` for that single ID.

---

## Step Entry Schema

Every step — regardless of success or failure — writes an entry with
this exact shape. No field is ever missing from the schema.

```
FIELD              TYPE        ALWAYS PRESENT    VALUE WHEN ERROR
─────              ────        ──────────────    ────────────────
run_id             string      yes               same as success
step_name          string      yes               same as success
input              any         yes               last known input
output             any/null    yes               null
latency_seconds    float       yes               time until exception
status             string      yes               "error"
error              string/null yes               exception message
timestamp          string      yes               UTC ISO-8601
```

---

## Data Flow Through the Pipeline

```
QUERY: "search for machine learning"
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ router_step                                              │
│                                                          │
│  Receives: {"query": "search for machine learning"}      │
│  Decision: "search" in query.lower() → "search"         │
│  Logs:     input={query}, output={decision}, status=ok  │
│  Returns:  "search"                                      │
└──────────────────────────┬──────────────────────────────┘
                           │  route = "search"
                           ▼
┌─────────────────────────────────────────────────────────┐
│ tool_step                                                │
│                                                          │
│  Receives: route="search", query="search for ML..."     │
│  Action  : time.sleep(0.5) + build mock API string      │
│  Logs:     input={route, query}, output={tool_response} │
│  Returns:  "[Mock Search API] Top result for..."        │
└──────────────────────────┬──────────────────────────────┘
                           │  tool_output = "[Mock Search API]..."
                           ▼
┌─────────────────────────────────────────────────────────┐
│ llm_step                                                 │
│                                                          │
│  Receives: query, tool_output                            │
│  Builds  : user_message = query + "\nContext:\n" + tool │
│  Calls   : OpenRouter API                               │
│  Logs:     system_prompt, user_message, response, tokens│
│  Returns:  "Machine learning is a subset of AI..."      │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
              run_pipeline() returns:
              {
                "run_id": "a3f1b2c4-...",
                "output": "Machine learning is...",
                "status": "success",
                "error":  null
              }
```

---

## Error Handling Model

Every step function uses the same pattern:

```
start = perf_counter()
try:
    ... do the work ...
    logger.log_step(..., status="success")
    return result
except Exception as exc:
    logger.log_step(..., status="error", error=str(exc))
    raise   ← re-raise so run_pipeline() knows it failed
```

`run_pipeline()` wraps the entire chain in its own `try/except`:

```
try:
    router_step(...)    ← if this raises, steps below never run
    tool_step(...)      ← if this raises, llm_step never runs
    llm_step(...)
except Exception as exc:
    return {"status": "error", "error": str(exc), ...}
```

**Result:** The failing step writes its own log entry before raising.
`run_pipeline()` catches the re-raised exception and returns a clean
error dict to the caller. The log file always has a complete record
of everything that ran, including what was logged just before failure.

---

## Fault Injection — BREAK_ROUTER

```python
BREAK_ROUTER: bool = False   # default — normal operation
```

When set to `True`:

```python
if BREAK_ROUTER:
    decision = "search"      # always returns "search"
else:
    decision = "search" if "search" in query.lower() else "explain"
```

The router log entry records this:

```json
"output": {
  "decision": "search",
  "break_router_active": true
}
```

This makes the injected fault **visible in the trace** — you can see
the router returned the wrong decision and exactly why (the flag was on).
Every downstream step then operates on a corrupted premise, and the trace
shows the full propagation path.

---

## Log File — Append-Only JSON Array

`step_logs.json` grows across all runs. Structure:

```
[
  { run_id: "run-A", step_name: "router",    ... },
  { run_id: "run-A", step_name: "tool_call", ... },
  { run_id: "run-A", step_name: "llm",       ... },
  { run_id: "run-B", step_name: "router",    ... },
  { run_id: "run-B", step_name: "tool_call", ... },
  ...
]
```

Write strategy — `_append()` in `RunLogger`:

```
1. Read entire file into list  (or [] if file missing)
2. Append new entry to list
3. Write entire list back
```

This keeps the file a valid JSON array at all times.
A process crash between steps 2 and 3 would lose that one entry —
acceptable for a local log. For production, use a database or NDJSON.

---

## Trace Visualiser — print_trace_for_run()

`print_trace_for_run(run_id)` in `main.py`:

```
1. Open step_logs.json
2. Filter entries where entry["run_id"] == run_id
3. Print each entry in step order with:
   - Step number and name
   - Status label [OK] or [FAIL]
   - Timestamp and latency
   - All input key-value pairs (truncated at 120 chars)
   - All output key-value pairs (truncated at 120 chars)
   - Error message (only if present)
```

This is a zero-dependency local equivalent of what observability platforms
like Jaeger or LangSmith provide in their trace views.

---

## OpenRouter Integration

```python
client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)
```

OpenRouter is an OpenAI-compatible gateway. Only the base URL and key
change. The rest of the `chat.completions.create()` call is identical
to calling OpenAI directly. Any model on OpenRouter can be substituted
by changing `DEFAULT_MODEL`.

---

## Separation of Concerns

```
CONCERN                    FILE                   ISOLATED TO
──────────────────────     ──────────────────     ───────────────────
Run identity (run_id)      run_logger.py          RunLogger.__init__
Persistent storage         run_logger.py          RunLogger._append
Step execution             agent_pipeline.py      Each step function
Routing logic              agent_pipeline.py      router_step()
External tool calls        agent_pipeline.py      tool_step()
LLM calls                  agent_pipeline.py      llm_step()
Pipeline orchestration     agent_pipeline.py      run_pipeline()
User interface (CLI)       main.py                main()
Trace display              main.py                print_trace_for_run()
Configuration / secrets    .env + constants       module-level only
```

Changing storage from JSON to PostgreSQL requires modifying only
`RunLogger._append` and `RunLogger._load_existing` — nothing else changes.

---

## Key Patterns

| Pattern | Where Applied | Purpose |
|---------|--------------|---------|
| Single Responsibility | Each file, each function | Swap or test any part independently |
| Shared logger instance | `run_pipeline()` → all steps | One run_id binds all step entries |
| Log-then-raise | Every step's except block | Step logs itself before propagating error |
| Fail fast | `run_pipeline()` try/except | Pipeline stops at first failure, returns clean dict |
| Append-only log | `RunLogger._append()` | History is never destroyed |
| Fault injection flag | `BREAK_ROUTER` | Controlled debugging without changing business logic |
| Monotonic latency | `time.perf_counter()` | Safe duration measurement |
| UTC timestamps | `datetime.now(timezone.utc)` | Timezone-safe across all machines |
