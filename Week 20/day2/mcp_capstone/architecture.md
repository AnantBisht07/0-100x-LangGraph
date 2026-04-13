# MCP Capstone – Architecture & Output Flow

> "AI systems don't fail because models are weak.
> They fail because context is poorly managed."

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          main.py  (CLI)                         │
│   ┌──────────────┐    ┌─────────────────┐    ┌──────────────┐  │
│   │  User Input  │───▶│  Onboarding /   │───▶│ Conversation │  │
│   │  (keyboard)  │    │  Profile Setup  │    │    Loop      │  │
│   └──────────────┘    └─────────────────┘    └──────┬───────┘  │
└──────────────────────────────────────────────────────│──────────┘
                                                       │
                                                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    agent_pipeline.py  (Orchestrator)            │
│                                                                 │
│  Stage 1        Stage 2        Stage 3        Stage 4          │
│  Load Memory──▶ Append Msg──▶ Summarise?──▶ Build Context      │
│                                                    │            │
│  Stage 7        Stage 6        Stage 5             │            │
│  Store Reply◀── LLM Call ◀── Validate ◀────────────┘           │
└─────────────────────────────────────────────────────────────────┘
       │               │             │              │
       ▼               ▼             ▼              ▼
 memory_store     anthropic     validator      context_manager
  (JSON disk)      (Claude)     (checks)       (MCP layers)
                                                    │
                                               summarizer
                                            (compression)
```

---

## 2. Module Dependency Map

```
main.py
  └── agent_pipeline.py
        ├── memory_store.py   (read + write JSON)
        ├── context_manager.py
        │     └── config.py
        ├── summarizer.py
        │     └── anthropic SDK
        ├── validator.py
        │     └── context_manager.py  (token estimate)
        └── anthropic SDK  (LLM call)

config.py  ◀── imported by almost every module
```

---

## 3. Data Flow Diagram

```
  [Disk: memory_store.json]
           │
           │  load_user()
           ▼
  ┌─────────────────────┐
  │   user_data dict    │
  │  ┌───────────────┐  │
  │  │    profile    │  │  ← persistent facts (name, preferences)
  │  │    summary    │  │  ← compressed older history (text)
  │  │    history    │  │  ← raw recent messages (list of dicts)
  │  └───────────────┘  │
  └──────────┬──────────┘
             │
             │  append_message()  ← adds current user query
             ▼
  ┌─────────────────────┐
  │  summarizer check   │  if len(history) >= 10
  │  (may compress)     │───▶ LLM summarises old msgs
  │                     │    updates summary + prunes history
  └──────────┬──────────┘
             │
             │  build_context()
             ▼
  ┌──────────────────────────────────────────┐
  │         MCP Structured Context           │
  │                                          │
  │  ① System Instruction                    │
  │  ② User Profile                          │
  │  ③ Conversation Summary                  │
  │  ④ Recent Messages  (last 5 only)        │
  │  ⑤ User Query                            │
  └──────────────┬───────────────────────────┘
                 │
                 │  validate_context()
                 ▼
  ┌─────────────────────┐
  │     Validator       │
  │  • token size check │  ── warn if > 4000 tokens
  │  • memory check     │  ── warn if profile/summary missing
  │  • relevance check  │  ── warn if query keywords not in context
  └──────────┬──────────┘
             │  (if valid)
             │  LLM call via Anthropic SDK
             ▼
  ┌─────────────────────┐
  │   Claude (LLM)      │
  │   receives the      │
  │   full MCP context  │
  └──────────┬──────────┘
             │
             │  response text
             ▼
  ┌─────────────────────┐
  │  append_message()   │  ← stores assistant reply to history
  │  (disk + in-memory) │
  └──────────┬──────────┘
             │
             ▼
       Printed to CLI
```

---

## 4. Detailed Output Flow (Turn by Turn)

### Turn 1 – Brand New User

```
python main.py
│
├─▶  Prompt: "Enter your user ID"
│        input: rahul
│
├─▶  load_user("rahul")
│        → no record found → creates default:
│          { profile: {name:"rahul", preferences:"general"},
│            summary: "", history: [] }
│
├─▶  Onboarding questions
│        "What should I call you?" → Rahul
│        "Response style?"         → technical
│        → update_profile() saves to JSON
│
├─▶  Greeting: "Hello, Rahul! I'm your context-aware AI assistant."
│
├─▶  User types: "I am learning LangGraph"
│
├─▶  agent_pipeline.run_pipeline("rahul", "I am learning LangGraph")
│    │
│    ├─ Stage 1: load_user → gets fresh user_data
│    ├─ Stage 2: append_message → history = [{role:user, content:...}]
│    ├─ Stage 3: len(history)=1 < 10 → skip summarisation
│    ├─ Stage 4: build_context →
│    │     ┌─────────────────────────────────────────────┐
│    │     │ You are a context-aware AI assistant…       │
│    │     │ ─────────────────────────────────────────── │
│    │     │ User Profile:                               │
│    │     │   Name: Rahul                               │
│    │     │   Preferences: technical                    │
│    │     │ ─────────────────────────────────────────── │
│    │     │ Conversation Summary:                       │
│    │     │   (No prior summary – new conversation)     │
│    │     │ ─────────────────────────────────────────── │
│    │     │ Recent Messages:                            │
│    │     │   (None yet)                                │
│    │     │ ─────────────────────────────────────────── │
│    │     │ User Query:                                 │
│    │     │   I am learning LangGraph                   │
│    │     └─────────────────────────────────────────────┘
│    ├─ Stage 5: validate_context →
│    │     [Validator] Token estimate: ~95 tokens
│    │     ⚠ [MEMORY] No conversation summary found.
│    │     (expected for new user – not a hard error)
│    ├─ Stage 6: LLM call → Claude replies
│    └─ Stage 7: append assistant reply → history has 2 messages
│
└─▶  Output:  "Agent: LangGraph is a framework for…"
```

---

### Turn 5 – Returning User (Same Session)

```
User types: "How does state work in LangGraph?"
│
├─▶  run_pipeline("rahul", "How does state work in LangGraph?")
│    │
│    ├─ Stage 1: load_user → history has 8 messages, summary still ""
│    ├─ Stage 2: append → history now 9 messages
│    ├─ Stage 3: len=9 < 10 → no summarisation yet
│    ├─ Stage 4: build_context →
│    │     Recent Messages layer shows last 5 raw turns
│    │     (messages 4–8 only – older ones intentionally excluded)
│    ├─ Stage 5: validate →
│    │     [Validator] Token estimate: ~310 tokens
│    │     ✓ Context looks healthy
│    ├─ Stage 6: LLM call
│    └─ Stage 7: history = 10 messages
│
└─▶  Output: "Agent: State in LangGraph is managed via…"
```

---

### Turn 6 – Memory Compression Fires

```
User types: "What was the first thing we talked about?"
│
├─▶  run_pipeline("rahul", "What was the first thing we talked about?")
│    │
│    ├─ Stage 1: load_user → history has 10 messages
│    ├─ Stage 2: append → history = 11 messages
│    ├─ Stage 3: len=11 >= 10  ──▶  SUMMARISATION TRIGGERED
│    │     │
│    │     ├─ old_messages = first 6 messages (11 - recent_limit 5)
│    │     ├─ LLM call to Claude:
│    │     │     "Summarise these 6 messages into bullet points…"
│    │     ├─ new_summary =
│    │     │     "• User is learning LangGraph
│    │     │      • Discussed state management, edges, nodes
│    │     │      • User prefers technical explanations"
│    │     ├─ update_summary() → saves summary to JSON
│    │     ├─ history = last 5 messages only (old 6 are pruned)
│    │     └─ save_user() → persists pruned history
│    │
│    ├─ Stage 4: build_context →
│    │     ┌─────────────────────────────────────────────┐
│    │     │ User Profile: Rahul / technical             │
│    │     │ ─────────────────────────────────────────── │
│    │     │ Conversation Summary:                       │
│    │     │   • User is learning LangGraph              │
│    │     │   • Discussed state management, edges…      │
│    │     │   • User prefers technical explanations     │
│    │     │ ─────────────────────────────────────────── │
│    │     │ Recent Messages: [last 5 raw turns]         │
│    │     │ ─────────────────────────────────────────── │
│    │     │ User Query: What was the first thing…?      │
│    │     └─────────────────────────────────────────────┘
│    ├─ Stage 5: validate → ✓ healthy
│    ├─ Stage 6: LLM answers using the summary layer
│    └─ Stage 7: store reply
│
└─▶  Output: "Agent: We first discussed LangGraph and how it…"
```

---

### Session 2 – Next Day (New Python Process)

```
python main.py
│
├─▶  "Enter your user ID": rahul
│
├─▶  load_user("rahul")
│        → finds existing JSON record:
│          { profile: {name:Rahul, preferences:technical},
│            summary: "• User is learning LangGraph…",
│            history: [last 5 messages] }
│
├─▶  Greeting:
│        "Welcome back, Rahul!"
│        "Last session summary: • User is learning LangGraph…"
│
└─▶  Conversation continues with full memory intact
```

---

## 5. Context Slicing – Why Only 5 Messages?

```
Full History (20 messages over time)
┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
│ 1  │ 2  │ 3  │ 4  │ 5  │ 6  │ 7  │ 8  │ 9  │ 10 │ 11 │…20│
└────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘
 └──────────────── COMPRESSED ──────────────────┘  └── RAW ─┘
              stored as summary text              sent verbatim

Sent to LLM:
  summary  (≈ 200 tokens)  ← gist of messages 1–15
  recent   (≈ 300 tokens)  ← verbatim messages 16–20

NOT sent:
  raw messages 1–15        ← would cost ~1500 tokens with zero benefit
```

**Result:** Context stays small and cheap no matter how long the session grows.

---

## 6. Validator Decision Tree

```
validate_context(context, user_data, query)
│
├─ Check 1: Token size
│       estimated_tokens = len(context) / 4
│       > 4000?  ──▶  ERROR   "Context is too large – abort LLM call"
│       > 3400?  ──▶  WARN    "Context approaching limit"
│       else     ──▶  OK
│
├─ Check 2: Missing memory
│       profile missing?      ──▶  WARN
│       profile.name missing? ──▶  WARN
│       summary missing?      ──▶  INFO  (expected for new users)
│
└─ Check 3: Relevance
        extract keywords from query (len >= 4, not stop words)
        search for any keyword in the context body
        none found? ──▶  WARN  "Agent may lack background for this question"
        found?      ──▶  OK

Final result:
  { valid: True/False, issues: [...], token_estimate: int }
  valid=False only on ERROR (token overflow)
  warnings are printed but do not block the LLM call
```

---

## 7. JSON Memory Schema

```json
{
  "rahul": {
    "profile": {
      "name": "Rahul",
      "preferences": "technical"
    },
    "summary": "• User is learning LangGraph\n• Discussed state and edges\n• Prefers technical depth",
    "history": [
      { "role": "user",      "content": "How do edges work?" },
      { "role": "assistant", "content": "Edges in LangGraph define transitions…" },
      { "role": "user",      "content": "Can I have conditional edges?" },
      { "role": "assistant", "content": "Yes, conditional edges allow…" },
      { "role": "user",      "content": "What was the first thing we talked about?" }
    ]
  }
}
```

`history` never grows past `RECENT_MESSAGES_LIMIT` (5) after the first
compression fires. `summary` absorbs everything older.

---

## 8. Key Design Decisions

| Decision | Reason |
|---|---|
| 5 raw messages in context | Enough for conversational coherence; anything older belongs in the summary |
| Threshold of 10 messages before compression | Gives the LLM enough material to write a meaningful summary |
| Validator does NOT raise exceptions | Policy (abort vs warn) stays in the pipeline, not the validator |
| Each pipeline stage is a separate function | Unit-testable in isolation; easy to swap one stage without touching others |
| Single JSON file for all users | Simple for demos; swap `memory_store.py` backend for Redis/Postgres in production |
| context built as plain text, not messages array | Human-readable – you can print and debug it without any tooling |
