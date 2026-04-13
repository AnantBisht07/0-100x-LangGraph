# Architecture — Feedback-Aware Run Tracker

---

## System Overview

The Feedback-Aware Run Tracker is a **linear pipeline** with four independent
components. Each component owns exactly one responsibility. They communicate
only through plain Python data types (strings, dicts) — no shared state,
no global variables, no side effects outside their own scope.

```
User Input
    │
    ▼
┌─────────────────────────────────────────────────┐
│           run_agent_with_tracking()             │  <-- Entry point
│                                                 │
│  ┌──────────────┐                               │
│  │ RunMetadata  │  Generate run_id + timestamp  │
│  └──────────────┘                               │
│         │                                       │
│         ▼                                       │
│  ┌──────────────┐                               │
│  │  OpenRouter  │  LLM call (measured)          │
│  │   API Call   │                               │
│  └──────────────┘                               │
│         │                                       │
│         ▼                                       │
│  ┌──────────────────┐                           │
│  │FeedbackCollector │  Rating + comment         │
│  └──────────────────┘                           │
│         │                                       │
│         ▼                                       │
│  ┌──────────────┐                               │
│  │  RunLogger   │  Append to runs_log.json      │
│  └──────────────┘                               │
└─────────────────────────────────────────────────┘
    │
    ▼
Return response text to caller
```

---

## Component Map

```
run_tracker.py
│
├── RunMetadata                    (Class)
│   ├── run_id       → uuid.uuid4()
│   ├── timestamp    → datetime.now(UTC).isoformat()
│   ├── prompt_version
│   ├── model
│   └── to_dict()    → converts to plain dict for JSON
│
├── RunLogger                      (Class)
│   ├── _load_existing()  → read runs_log.json (or [] if missing)
│   ├── log(entry)        → append entry, rewrite file
│   └── load_all()        → return all logged runs
│
├── FeedbackCollector              (Class)
│   ├── collect()         → ask rating + comment, return dict
│   └── _prompt_rating()  → loop until valid 1-5 integer
│
├── run_agent_with_tracking()      (Function — main pipeline)
│   ├── Step 1: Build RunMetadata
│   ├── Step 2: Create OpenAI client (OpenRouter)
│   ├── Step 3: Execute LLM call + measure latency
│   ├── Step 4: Extract token usage (if available)
│   ├── Step 5: Collect feedback (FeedbackCollector)
│   ├── Step 6: Assemble entry dict
│   └── Step 7: RunLogger.log(entry)
│
├── compare_prompt_versions()      (Function — A/B helper)
│   ├── Calls run_agent_with_tracking() twice (version_a, version_b)
│   ├── Records latency + word count
│   └── Prints comparison summary + logged run IDs
│
└── main()                         (Demo entry point)
    ├── Example 1: single run
    └── Example 2: A/B comparison
```

---

## Data Flow

```
INPUT                    PROCESSING                       OUTPUT
─────                    ──────────                       ──────

input_text ──────────►  RunMetadata.run_id               ──►  runs_log.json
prompt_version ───────►  RunMetadata.timestamp           ──►  (append-only)
model ────────────────►  RunMetadata.prompt_version      ──►
                         RunMetadata.model
                              │
                              ▼
                         OpenRouter API
                         (system prompt + user input)
                              │
                              ▼
                         response.choices[0].message.content
                         response.usage.prompt_tokens
                         response.usage.completion_tokens
                         perf_counter() delta = latency
                              │
                              ▼
                         FeedbackCollector
                         (rating 1-5, comment)
                              │
                              ▼
                         entry = {
                           run_id, timestamp,
                           prompt_version, model,
                           input, output, latency,
                           token_usage (optional),
                           feedback (optional)
                         }
                              │
                              ▼
                         RunLogger.log(entry)
                         runs_log.json ◄──── appended
```

---

## Separation of Concerns

This is the most important design decision in the system.

```
┌─────────────────────────────────────────────────────────────┐
│  CONCERN              │  OWNER               │  ISOLATION   │
├─────────────────────────────────────────────────────────────┤
│  Identity (who, when) │  RunMetadata         │  Class       │
│  Storage (write/read) │  RunLogger           │  Class       │
│  User feedback        │  FeedbackCollector   │  Class       │
│  Execution + wiring   │  run_agent_with...() │  Function    │
│  Configuration        │  Module-level consts │  Top of file │
│  Secrets (API key)    │  .env + os.environ   │  External    │
└─────────────────────────────────────────────────────────────┘
```

**Why this matters:**

If tomorrow you want to store logs in PostgreSQL instead of JSON,
you change only `RunLogger`. Nothing else touches storage logic.

If you want to collect feedback via a web form instead of terminal input,
you change only `FeedbackCollector`. The pipeline does not care how
feedback is collected — only that it returns a dict with `rating` and `comment`.

---

## The Log File Structure

`runs_log.json` is an **append-only JSON array**. Every entry is one run.

```
runs_log.json
│
└── [ array of run entries ]
    │
    ├── entry 0  { run_id, timestamp, prompt_version, model,
    │              input, output, latency, token_usage, feedback }
    │
    ├── entry 1  { ... }
    │
    └── entry N  { ... }
```

Fields per entry:

```
FIELD               TYPE        REQUIRED    SOURCE
─────               ────        ────────    ──────
run_id              string      yes         uuid.uuid4()
timestamp           string      yes         datetime.now(UTC)
prompt_version      string      yes         caller argument
model               string      yes         caller argument / DEFAULT_MODEL
input               string      yes         caller argument
output              string      yes         LLM response
latency_seconds     float       yes         perf_counter delta
token_usage         dict        optional    response.usage (if provider returns it)
  prompt_tokens     int         optional
  completion_tokens int         optional
  total_tokens      int         optional
feedback            dict        optional    FeedbackCollector (if collect_feedback=True)
  rating            int (1-5)   optional
  comment           string      optional
```

---

## External Dependencies

```
┌──────────────────────────────────────────────────────┐
│                    run_tracker.py                    │
│                                                      │
│  Standard Library        Third-Party                 │
│  ───────────────         ───────────                 │
│  json                    openai (SDK)                │
│  os                      python-dotenv               │
│  time                                                │
│  uuid                    OpenRouter API (network)    │
│  datetime                  └─ Base URL:              │
│  pathlib                      https://openrouter.ai  │
│  typing                       /api/v1                │
└──────────────────────────────────────────────────────┘
```

No databases. No external observability services. No message queues.
Everything runs locally except the LLM call itself.

---

## Prompt Version Registry

Prompts are stored as a **versioned dictionary** — a first-class registry,
not strings buried in function calls.

```python
PROMPT_VERSIONS = {
    "v1.0": "...",
    "v2.0": "...",
}
```

```
PROMPT_VERSIONS (registry)
│
├── "v1.0"  ──►  "You are a helpful assistant. Answer concisely..."
│
└── "v2.0"  ──►  "You are an expert assistant. Provide thorough..."

Every run entry records WHICH version produced the output.
This makes every response traceable back to its exact instructions.
```

Adding a new prompt version is a one-line change to the registry.
The rest of the system picks it up automatically.

---

## OpenRouter Integration

OpenRouter is an OpenAI-compatible API gateway. The integration requires
only two overrides from a standard OpenAI client:

```python
client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],   # OpenRouter key, not OpenAI
    base_url="https://openrouter.ai/api/v1",    # OpenRouter endpoint
)
```

Everything else — `chat.completions.create()`, message format, response
structure, token usage — is identical to the OpenAI SDK.

```
Your Script
    │
    │  openai.OpenAI(base_url=openrouter)
    ▼
OpenRouter Gateway ──►  GPT-4o-mini  (openai/gpt-4o-mini)
                   ──►  Claude Haiku (anthropic/claude-3-haiku)
                   ──►  Llama 3      (meta-llama/llama-3-8b-instruct)
                   ──►  Gemini Flash (google/gemini-flash-1.5)
                   ──►  200+ models
```

Swap the model ID in one place. The rest of the code is unchanged.

---

## Error Handling Strategy

```
FAILURE POINT              HANDLING
─────────────              ────────
Missing .env file          load_dotenv() silently continues;
                           os.environ["KEY"] raises KeyError at call time.
                           Fast, clear failure.

Unknown prompt version     Guard clause at top of run_agent_with_tracking().
                           ValueError before any API call is made.

Corrupted runs_log.json    _load_existing() catches JSONDecodeError.
                           Returns empty list. Log starts fresh.

Missing runs_log.json      _load_existing() checks .exists() first.
                           Returns empty list. File created on first write.

API call failure           Not caught — propagates to caller.
                           Intentional: network errors should be visible.

Invalid feedback input     _prompt_rating() loops until valid 1-5 integer.
                           Never crashes on bad input.
```

---

## Key Design Patterns Used

```
PATTERN                  WHERE USED              WHY
───────                  ──────────              ───
Single Responsibility    Each class / function   Easy to swap, test, and
                                                 understand in isolation

Fail Fast (guard clause) run_agent_with...()     Catch bad input before
                                                 expensive operations

Append-Only Log          RunLogger               History is never destroyed

Optional fields          token_usage, feedback   JSON stays clean when
                                                 data is unavailable

Dictionary Unpacking     entry = {**metadata...} DRY — define once in
(**kwargs pattern)                               to_dict(), reuse everywhere

Monotonic timer          time.perf_counter()     Safe latency measurement
                                                 (won't go backward)

UTC timestamps           datetime.now(UTC)       Timezone-safe across all
                                                 machines and regions

Private methods (_name)  _load_existing()        Signal: internal use only
                         _prompt_rating()
```

---

## Production Upgrade Path

This architecture is designed to scale. Each component maps directly to
a production equivalent:

```
THIS PROJECT              PRODUCTION EQUIVALENT
────────────              ─────────────────────
runs_log.json        →    PostgreSQL / BigQuery / DynamoDB
Terminal input()     →    In-app thumbs up/down, async survey
PROMPT_VERSIONS dict →    Prompt management service (DB-backed)
No alerting          →    Alert if avg_rating < 3.5 or latency > 10s
No dashboard         →    Grafana / Metabase / custom analytics UI
Single file          →    Microservice or LangGraph node
```

The component boundaries stay the same. Only the implementations change.

---

