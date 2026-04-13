# PromptLab Pro

A production-ready A/B testing and evaluation tool for LLM prompts.
Run two prompt versions against 20 test inputs, collect metrics, detect regressions, and visualise everything in a Streamlit dashboard.

---

## Quick Start

```bash
pip install -r requirements.txt

# Copy and fill in your API key
cp .env.example .env

# Run the batch evaluation
python main.py

# Launch the dashboard
streamlit run dashboard.py
```

---

## File Structure

```
promptlab_pro/
│
├── prompts.py          ← Prompt version registry (control / variation)
├── evaluator.py        ← Metrics computation per response
├── batch_runner.py     ← LLM calls for every input × version combination
├── aggregator.py       ← Average metrics + regression detection
├── dashboard.py        ← Streamlit visual comparison dashboard
├── main.py             ← Entry point: runs everything, saves JSON
├── requirements.txt
├── .env.example
├── results_log.json    ← Created by main.py (raw per-input results)
└── summary_log.json    ← Created by main.py (aggregated averages)
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          main.py                                │
│                                                                 │
│  Defines 20 test inputs                                         │
│  Loads prompt versions from prompts.py                          │
│  Calls run_batch_test() → saves results_log.json                │
│  Calls aggregate_metrics() → saves summary_log.json             │
│  Calls detect_regression() → prints warning if needed           │
│  Instructs user to launch dashboard                             │
└───────────────────┬─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                       prompts.py                                │
│                                                                 │
│  PROMPT_VERSIONS = {                                            │
│    "control":   "You are a concise assistant.",                 │
│    "variation": "You are a structured, detailed assistant..."   │
│  }                                                              │
│                                                                 │
│  get_prompt(version) → returns system prompt string             │
└───────────────────┬─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      batch_runner.py                            │
│                                                                 │
│  For each input (1 … 20):                                       │
│                                                                 │
│    ┌──────────────────┐     ┌──────────────────┐               │
│    │  Control Prompt  │     │ Variation Prompt  │               │
│    │  LLM Call        │     │ LLM Call          │               │
│    │  perf_counter()  │     │ perf_counter()    │               │
│    │  token_usage     │     │ token_usage       │               │
│    └────────┬─────────┘     └────────┬──────────┘               │
│             │                        │                          │
│             ▼                        ▼                          │
│    ┌──────────────────────────────────────────┐                 │
│    │             evaluator.py                 │                 │
│    │   word_count, latency, tokens, rating    │                 │
│    └──────────────────────────────────────────┘                 │
│                                                                 │
│  Returns:                                                       │
│  {                                                              │
│    "control":   [ {metrics}, {metrics}, ... ],   (20 items)     │
│    "variation": [ {metrics}, {metrics}, ... ]    (20 items)     │
│  }                                                              │
└───────────────────┬─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      aggregator.py                              │
│                                                                 │
│  aggregate_metrics(results) →                                   │
│  {                                                              │
│    "control":   {                                               │
│      "average_word_count":  42.3,                               │
│      "average_latency":      1.21,                              │
│      "average_tokens":     118.0,                               │
│      "average_user_rating":  3.8                                │
│    },                                                           │
│    "variation": { ... }                                         │
│  }                                                              │
│                                                                 │
│  detect_regression(summary) →                                   │
│    If variation rating < control rating:                        │
│    "⚠  Potential regression detected."                          │
└───────────────────┬─────────────────────────────────────────────┘
                    │
          ┌─────────┴──────────┐
          │                    │
          ▼                    ▼
  results_log.json      summary_log.json
  (raw per-input)       (aggregated avgs)
          │
          └──────────────────────────────────────┐
                                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      dashboard.py (Streamlit)                   │
│                                                                 │
│  Reads results_log.json                                         │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Section 1 — Input Summary                              │   │
│  │  Total Inputs: 20 │ Versions: 2 │ Total LLM Calls: 40  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Section 2 — Metrics Comparison Table                   │   │
│  │                                                         │   │
│  │  Metric              │ Control │ Variation              │   │
│  │  ──────────────────────────────────────────             │   │
│  │  Avg Word Count      │  42.30  │  91.50                 │   │
│  │  Avg Latency (s)     │   1.21  │   1.87                 │   │
│  │  Avg Tokens          │ 118.00  │ 204.00                 │   │
│  │  Avg User Rating     │   3.80  │   4.10                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Section 3 — Bar Charts                                 │   │
│  │                                                         │   │
│  │  Avg Rating      Avg Word Count                         │   │
│  │  ▐███ Control    ▐███ Control                           │   │
│  │  ▐█████ Var.     ▐█████████ Var.                        │   │
│  │                                                         │   │
│  │  Avg Latency     Avg Tokens                             │   │
│  │  ▐████ Control   ▐████ Control                          │   │
│  │  ▐██████ Var.    ▐████████ Var.                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Section 4 — Regression Detection                       │   │
│  │                                                         │   │
│  │  ✅  No regression detected.                            │   │
│  │  — or —                                                 │   │
│  │  ⚠  Potential regression detected. Variation rating    │   │
│  │     (3.6) is 0.2 points below control (3.8).           │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Output Files

| File | Contents |
|---|---|
| `results_log.json` | Full per-input results for both versions (40 entries total) |
| `summary_log.json` | Aggregated averages for control and variation |

### results_log.json structure

```json
{
  "control": [
    {
      "input": "What is machine learning?",
      "output": "Machine learning is...",
      "word_count": 38,
      "latency_seconds": 1.1243,
      "total_tokens": 102,
      "user_rating": 4
    }
  ],
  "variation": [ ... ]
}
```

### summary_log.json structure

```json
{
  "control": {
    "average_word_count": 42.3,
    "average_latency": 1.21,
    "average_tokens": 118.0,
    "average_user_rating": 3.8
  },
  "variation": {
    "average_word_count": 91.5,
    "average_latency": 1.87,
    "average_tokens": 204.0,
    "average_user_rating": 4.1
  }
}
```

---

## Metrics Explained

| Metric | What it measures |
|---|---|
| `word_count` | Verbosity — how long the response is |
| `latency_seconds` | Speed — wall-clock time of the API call |
| `total_tokens` | Cost proxy — total tokens consumed |
| `user_rating` | Quality signal — simulated 3–5 rating (replace with real feedback) |

---

## Regression Detection Logic

```
If variation.average_user_rating < control.average_user_rating
    → Print warning with the rating difference
Else
    → No regression
```

A regression means your new prompt version is performing worse than the baseline. This is the minimum viable signal. Production systems add statistical significance tests before acting on the result.

---

## Extending PromptLab Pro

**Add a new prompt version:**
Edit `prompts.py` — add one key to `PROMPT_VERSIONS`. Nothing else changes.

**Add a new metric:**
Edit `evaluator.py` — add the computation to `evaluate()`. Update `aggregator.py` to include the new key in `aggregate_metrics()`.

**Use real user ratings instead of simulated:**
Pass `simulate_rating=False` to `evaluator.evaluate()` and collect the rating from a human before calling evaluate.
