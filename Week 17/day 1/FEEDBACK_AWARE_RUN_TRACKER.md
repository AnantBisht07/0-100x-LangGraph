# Feedback-Aware Run Tracker

## What Is This?

Every time you call an LLM, three things happen and then disappear:

1. A prompt was sent
2. A response came back
3. The user had a reaction to it

Without a system in place, all three are **gone forever**. You cannot go back and ask:
- Which version of the prompt produced that answer?
- How long did it take?
- Did the user find it useful?

The **Feedback-Aware Run Tracker** is a structured observability pipeline that captures all of this, every single time, automatically.

---

## What Is Actually Happening — Step by Step

Using the run we just executed as a concrete example:

```
python run_tracker.py
```

### Step 1 — Run Identity is Created

Before any LLM call is made, the system generates:

```json
{
  "run_id":        "03249b6f-8db6-4fb3-9a09-f8d34e8acfc4",
  "timestamp":     "2026-02-21T10:30:00+00:00",
  "prompt_version": "v1.0",
  "model":          "openai/gpt-4o-mini"
}
```

- `run_id` is a UUID — globally unique, forever traceable
- `timestamp` is UTC — timezone-safe for distributed systems
- `prompt_version` is a label — not the text itself, but which version of instructions was used
- `model` is recorded — so you know exactly which model produced which output

### Step 2 — The LLM Call is Executed and Measured

```python
start = time.perf_counter()
response = client.chat.completions.create(...)
latency = round(time.perf_counter() - start, 4)
```

The wall-clock time is measured with `perf_counter` — the highest resolution timer
available in Python. The result in our run was:

```
latency_seconds: 1.23
```

This is not just a number. Over time, latency data tells you:
- Is the model getting slower?
- Does a longer prompt cause slower responses?
- Is there a performance difference between models?

### Step 3 — Token Usage is Captured (if available)

OpenRouter returns token counts from the provider:

```json
"token_usage": {
  "prompt_tokens": 45,
  "completion_tokens": 120,
  "total_tokens": 165
}
```

This is **cost intelligence**. Every token costs money. If you are not tracking tokens
per run, you are flying blind on your API spend.

### Step 4 — User Feedback is Collected Immediately

After the response is shown, the user is asked:

```
Rate this response (1-5): 3
Optional comment (press Enter to skip):
```

In our actual run above, the user rated:
- Example 1 (observability explanation): **3/5**
- Example 2 v1.0 (RAG vs fine-tuning, concise): **2/5**
- Example 2 v2.0 (RAG vs fine-tuning, detailed): **1/5**

This is **ground truth**. No automated metric can replace a real human rating attached
to the exact run that produced it.

### Step 5 — Everything is Written to a Structured Log

All of the above is assembled into one JSON object and appended to `runs_log.json`:

```json
{
  "run_id": "03249b6f-8db6-4fb3-9a09-f8d34e8acfc4",
  "timestamp": "2026-02-21T10:30:00+00:00",
  "prompt_version": "v1.0",
  "model": "openai/gpt-4o-mini",
  "input": "Explain the concept of observability in three sentences.",
  "output": "Observability is the ability to infer the internal state...",
  "latency_seconds": 1.23,
  "token_usage": {
    "prompt_tokens": 45,
    "completion_tokens": 87,
    "total_tokens": 132
  },
  "feedback": {
    "rating": 3,
    "comment": ""
  }
}
```

Nothing is deleted. Nothing is overwritten. Every run is permanent.

---

## What the Comparison Run Showed Us

The `compare_prompt_versions()` function ran the **same query** under two different
system prompts and produced this summary:

```
[v1.0]
  Word count   : 217
  Total elapsed: 54.6s

[v2.0]
  Word count   : 634
  Total elapsed: 21.5s
```

### What this tells us

| Signal | Meaning |
|--------|---------|
| v2.0 was 3x longer (634 words vs 217) | The "thorough" prompt did what it said |
| v2.0 was faster overall (21s vs 54s) | Counterintuitive — likely a cold cache on v1.0 |
| User rated v1.0 lower (2/5) than expected | More concise doesn't mean more useful |
| User rated v2.0 even lower (1/5) | Too verbose — the user wanted something in between |

**Without the tracker, this insight is invisible.** With it, you have a logged,
timestamped, rated record of exactly what each version produced.

---

## Why This Matters — The Core Advantages

### 1. Prompts Are Versioned Assets, Not Strings

Most teams treat prompts as strings scattered in code. That is equivalent to shipping
software without version control.

When prompts are versioned:
- You can roll back to `v1.0` if `v2.0` performs worse
- You know exactly which prompt produced each logged output
- You can run A/B tests across versions systematically

### 2. Every Run Is Traceable

The `run_id` is the receipt. If a user reports a bad response, you look up the
`run_id` and you have the full picture: what was asked, what was returned, which
model, which prompt version, how long it took, and how the user rated it.

Without this, debugging AI failures is guesswork.

### 3. Feedback Is Captured at the Right Moment

The longer you wait to ask for feedback, the less accurate it gets. Collecting a
rating immediately after the response — while the user still has full context — is
the highest quality signal you can get at zero infrastructure cost.

### 4. Latency and Token Data Enable Cost Control

Once you have per-run latency and token counts in a log, you can answer:
- "What is our average response time this week?"
- "Which prompt version is most token-efficient?"
- "Are we over-spending on a model that a cheaper one could replace?"

### 5. This Is the Foundation for Evaluation Systems

The log you are building now is exactly the dataset that evaluation frameworks
(LangSmith, Braintrust, custom evals) need to function. You are building that
dataset yourself, with full ownership, no external dependency.

---

## How This Is Done and Managed in Production

What we built here is the right mental model. Production systems scale it up
with more infrastructure, but the same four components remain.

### Production Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCTION RUN TRACKER                   │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐ │
│  │ RunMetadata │    │  RunLogger  │    │FeedbackCollector│ │
│  │  (same)     │    │  (upgraded) │    │  (same logic,   │ │
│  │             │    │             │    │   async or UI)  │ │
│  └─────────────┘    └──────┬──────┘    └─────────────────┘ │
│                            │                                │
│                     ┌──────▼──────┐                         │
│                     │  Postgres / │                         │
│                     │  BigQuery / │                         │
│                     │  S3 + Athena│                         │
│                     └──────┬──────┘                         │
│                            │                                │
│              ┌─────────────▼──────────────┐                 │
│              │      Observability Layer    │                 │
│              │  Grafana / Metabase / custom│                 │
│              └─────────────────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

### What Changes in Production

| Component | This Project | Production |
|-----------|-------------|------------|
| **Storage** | `runs_log.json` (local file) | PostgreSQL table or cloud data warehouse |
| **Feedback** | Terminal input prompt | In-app thumbs up/down, star rating, or async survey |
| **Token tracking** | Logged per run | Aggregated daily, alerted when cost spikes |
| **Prompt versions** | Dict in code | Prompt management system (database or config service) |
| **Run lookup** | Read the JSON file | Query by `run_id`, filter by date/model/rating |
| **Alerting** | None | Alert if avg rating drops below threshold |
| **Dashboards** | None | Grafana / Metabase showing rating trends, latency, cost |

### Production Database Schema (PostgreSQL)

```sql
CREATE TABLE agent_runs (
    run_id          UUID PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL,
    prompt_version  VARCHAR(20) NOT NULL,
    model           VARCHAR(100) NOT NULL,
    input_text      TEXT NOT NULL,
    output_text     TEXT NOT NULL,
    latency_seconds NUMERIC(8, 4),
    prompt_tokens   INTEGER,
    completion_tokens INTEGER,
    total_tokens    INTEGER,
    feedback_rating SMALLINT CHECK (feedback_rating BETWEEN 1 AND 5),
    feedback_comment TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast lookup by version and date
CREATE INDEX idx_runs_prompt_version ON agent_runs (prompt_version, timestamp);
```

### Production Feedback Patterns

In a real product, you do not ask for a rating in a terminal. Instead:

**Pattern A — Inline thumbs (chat UI)**
```
[Response text here]
[👍] [👎]  →  maps to rating 5 or 1
```

**Pattern B — Delayed async survey**
Send a follow-up after 5 minutes via email/Slack:
```
"How useful was the response you got earlier? [1–5]"
```

**Pattern C — Implicit signals**
Track: did the user copy the response? Did they ask a follow-up? Did they close
the session? These proxy signals can supplement explicit ratings.

### Production Prompt Version Management

Prompts in production are not hardcoded dicts. They live in a config store:

```
prompts/
  v1.0.txt   ← deployed, stable
  v2.0.txt   ← in A/B test (10% traffic)
  v3.0.txt   ← draft, not yet deployed
```

Each deploy of a new prompt version is a tracked event, just like a code deploy.
You can roll back a prompt the same way you roll back code.

### Production Alerting Rules

Once you have feedback data in a database, you add rules:

```python
# Example: alert if 24h rolling average drops below 3.5
if avg_rating_last_24h < 3.5:
    send_alert("Agent quality degraded — avg rating {avg_rating_last_24h}")

# Example: alert if p95 latency exceeds 10 seconds
if p95_latency > 10.0:
    send_alert("Agent latency spike — p95 is {p95_latency}s")
```

---

## The Mental Model to Keep

```
Every LLM call is an experiment.
Every experiment needs a record.
Every record needs a rating.
Every rating is data.
Data drives decisions.
```

This project is the habit. The infrastructure can scale up later. What cannot be
retrofitted is the discipline of capturing the signal in the first place.

---

## File Reference

| File | Purpose |
|------|---------|
| `run_tracker.py` | The full pipeline — all four components |
| `runs_log.json` | Append-only log of every run (auto-created) |
| `.env` | Your API key — never committed to git |
| `.env.example` | Template showing which keys are needed |
| `requirements.txt` | `openai`, `python-dotenv` |
