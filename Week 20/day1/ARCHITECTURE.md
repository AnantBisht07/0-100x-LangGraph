# System Architecture — Production AI Agent
### Week 20 | LangSmith + Model Context Protocol

---

## 1. FULL SYSTEM OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PRODUCTION AI AGENT                              │
│                                                                         │
│   ┌──────────┐      ┌──────────────────────────────────────────────┐   │
│   │          │      │              PIPELINE                        │   │
│   │  main.py │─────▶│                                              │   │
│   │  (CLI)   │      │  Router → Tool → Context Builder → LLM Call  │   │
│   │          │◀─────│                                              │   │
│   └──────────┘      └──────────────────────────────────────────────┘   │
│        │                         │              │                       │
│        │                         │              │                       │
│        ▼                         ▼              ▼                       │
│   ┌──────────┐           ┌────────────┐  ┌───────────┐                 │
│   │  memory  │           │   tools    │  │ LangSmith │                 │
│   │  store   │           │  (search,  │  │ (tracing) │                 │
│   │  .json   │           │  calc)     │  │ dashboard │                 │
│   └──────────┘           └────────────┘  └───────────┘                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. REQUEST FLOW (One User Message)

```
  USER TYPES: "what is python?"
        │
        ▼
┌───────────────┐
│   main.py     │  captures input, holds message history
│               │  calls run_pipeline(user_id, messages, query)
└───────┬───────┘
        │
        ▼
┌───────────────────────────────────────────────────────────┐
│                    pipeline.py                            │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  STEP 1 — Router                                    │  │
│  │                                                     │  │
│  │  query.lower() → scan for keywords                 │  │
│  │                                                     │  │
│  │  "what is python?"                                  │  │
│  │       ↓                                             │  │
│  │  "what is" found in SEARCH_TRIGGERS                 │  │
│  │       ↓                                             │  │
│  │  route = { type: "search", query: "..." }           │  │
│  └─────────────────────┬───────────────────────────────┘  │
│                        │                                   │
│                        ▼                                   │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  STEP 2 — Tool Executor                             │  │
│  │                                                     │  │
│  │  route.type == "search"                             │  │
│  │       ↓                                             │  │
│  │  dispatch_tool("search", query)                     │  │
│  │       ↓                                             │  │
│  │  search_tool(query) → scans knowledge dict          │  │
│  │       ↓                                             │  │
│  │  "Python is a high-level programming language..."   │  │
│  └─────────────────────┬───────────────────────────────┘  │
│                        │                                   │
│                        ▼                                   │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  STEP 3 — Context Builder (MCP)                     │  │
│  │                                                     │  │
│  │  load profile from memory_store                     │  │
│  │       ↓                                             │  │
│  │  _maybe_compress(messages)  ← slicing check         │  │
│  │       ↓                                             │  │
│  │  fill _CONTEXT_TEMPLATE with:                       │  │
│  │    • profile (name, preferences)                    │  │
│  │    • summary (compressed history)                   │  │
│  │    • recent messages (last 5)                       │  │
│  │    • tool result (search output)                    │  │
│  │    • current query                                  │  │
│  │       ↓                                             │  │
│  │  returns structured context string (~131 tokens)    │  │
│  └─────────────────────┬───────────────────────────────┘  │
│                        │                                   │
│                        ▼                                   │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  STEP 4 — LLM Call                                  │  │
│  │                                                     │  │
│  │  OpenAI(base_url=openrouter.ai/api/v1)              │  │
│  │       ↓                                             │  │
│  │  chat.completions.create(                           │  │
│  │    model    = "openai/gpt-4o-mini"                  │  │
│  │    messages = [{"role": "system", content: ctx}]    │  │
│  │  )                                                  │  │
│  │       ↓  (3.19s)                                    │  │
│  │  "Python is a versatile, high-level language..."    │  │
│  └─────────────────────┬───────────────────────────────┘  │
└────────────────────────┼──────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────┐
              │    main.py       │
              │                  │
              │  prints response │
              │  prints metadata │
              │  appends to      │
              │  messages[]      │
              └──────────────────┘
```

---

## 3. LANGSMITH TRACE HIERARCHY

```
Every run_pipeline() call creates this tree in LangSmith:

  ┌─────────────────────────────────────────────────────────┐
  │  🔴 Agent Pipeline          [chain]    root span        │
  │  │                                                      │
  │  ├── 🔵 Router              [chain]    0.00s            │
  │  │        Input:  "what is python?"                     │
  │  │        Output: { type: "search" }                    │
  │  │                                                      │
  │  ├── 🟢 Tool Executor       [tool]     0.00s            │
  │  │   │    Input:  "search", "what is python?"           │
  │  │   │    Output: "Python is a high-level..."           │
  │  │   │                                                  │
  │  │   ├── 🔵 Tool Router     [chain]    0.00s            │
  │  │   │                                                  │
  │  │   └── 🟢 Search Tool     [tool]     0.00s            │
  │  │             Input:  "what is python?"                │
  │  │             Output: "Search results for..."          │
  │  │                                                      │
  │  ├── 🔵 Context Builder     [chain]    0.00s            │
  │  │        Input:  user_id, messages, query, tool_result │
  │  │        Output: structured MCP context string         │
  │  │                token_estimate: 131                   │
  │  │                                                      │
  │  └── 🟠 LLM Call            [llm]      3.19s            │
  │             Input:  structured context                  │
  │             Output: "Python is a versatile..."          │
  │             Tokens: recorded automatically              │
  └─────────────────────────────────────────────────────────┘

  Icon legend:
  🔴 chain  = multi-step orchestration logic
  🟢 tool   = external action / tool call
  🟠 llm    = actual language model API call
```

---

## 4. MCP CONTEXT STRUCTURE (What the LLM Receives)

```
┌────────────────────────────────────────────────────────────┐
│                   STRUCTURED CONTEXT (MCP)                 │
│                                                            │
│  ┌──────────────────────────────────┐                      │
│  │  LAYER 1 — SYSTEM                │  always included     │
│  │  "You are a helpful assistant.   │  defines agent role  │
│  │   Adapt tone to user preference."│                      │
│  └──────────────────────────────────┘                      │
│                                                            │
│  ┌──────────────────────────────────┐                      │
│  │  LAYER 2 — USER PROFILE          │  from memory.json    │
│  │  Name:        Anant              │  persistent across   │
│  │  Preferences: technical          │  all sessions        │
│  │  Member since: 2026-03-21        │                      │
│  └──────────────────────────────────┘                      │
│                                                            │
│  ┌──────────────────────────────────┐                      │
│  │  LAYER 3 — CONVERSATION SUMMARY  │  compressed history  │
│  │  "User has been learning about   │  auto-generated by   │
│  │   LangSmith and MCP concepts..." │  LLM when msgs > 10  │
│  └──────────────────────────────────┘                      │
│                                                            │
│  ┌──────────────────────────────────┐                      │
│  │  LAYER 4 — RECENT MESSAGES       │  last 5 turns only   │
│  │  User: what is langsmith?        │  always fresh        │
│  │  Agent: LangSmith is...          │                      │
│  └──────────────────────────────────┘                      │
│                                                            │
│  ┌──────────────────────────────────┐                      │
│  │  LAYER 5 — TOOL RESULTS          │  only if tool ran    │
│  │  "Search results for 'python':   │  injected here       │
│  │   Python is a high-level..."     │                      │
│  └──────────────────────────────────┘                      │
│                                                            │
│  ┌──────────────────────────────────┐                      │
│  │  LAYER 6 — CURRENT QUERY         │  always last         │
│  │  "what is python?"               │  what user just said │
│  └──────────────────────────────────┘                      │
│                                                            │
│  Total: ~131 tokens    ←   lean, structured, controlled   │
└────────────────────────────────────────────────────────────┘
```

---

## 5. CONTEXT SLICING (Memory Management Over Time)

```
SESSION START                           AFTER 10+ MESSAGES
─────────────                           ──────────────────

messages = []                           messages = [
                                          msg 1,  msg 2,
Turn 1:  2 messages                       msg 3,  msg 4,
Turn 2:  4 messages                       msg 5,  msg 6,
Turn 3:  6 messages                       msg 7,  msg 8,
Turn 4:  8 messages                       msg 9,  msg 10,
Turn 5: 10 messages ← threshold hit!      msg 11, msg 12
Turn 6: 12 messages                     ]
                                               │
                                    _maybe_compress() runs
                                               │
                              ┌────────────────┴────────────────┐
                              │                                 │
                         OLDER (msgs 1-7)             RECENT (msgs 8-12)
                              │                                 │
                              ▼                                 │
                    LLM summarizes into                         │
                    2-3 sentences                               │
                              │                                 │
                              ▼                                 ▼
                    stored in memory.json            sent directly to LLM
                    as "summary" field
                              │
                              ▼
                    Next turn context:
                    ┌────────────────────────────┐
                    │ SUMMARY  (2-3 sentences)   │ ← compressed past
                    │ RECENT   (last 5 messages) │ ← fresh present
                    │ QUERY    (current input)   │ ← new input
                    └────────────────────────────┘
                         ~150 tokens total
                    (instead of 600+ without slicing)
```

---

## 6. MEMORY PERSISTENCE (data/memory.json)

```
  python main.py                    data/memory.json
  ──────────────                    ────────────────

  User types: anant
        │                           {
        │  create_user()              "anant": {
        └─────────────────────────▶    "name": "Anant",
                                       "preferences": "technical",
  After each response:                 "summary": "",
        │                              "created_at": "2026-03-21"
        │  update_summary()           },
        └─────────────────────────▶  "priya": {
                                       "name": "Priya",
  After 10+ messages:                  "preferences": "casual",
        │                              "summary": "User discussed...",
        │  update_summary()             "created_at": "2026-03-21"
        └─────────────────────────▶  }
                                    }

  Next session:
        │  load_memory("anant")
        └─────────────────────────▶  reads file → returns profile
                                     "Welcome back, Anant!"
```

---

## 7. FILE DEPENDENCY MAP

```
                         main.py
                        /       \
                       /         \
                  config.py    pipeline.py
                                /   |   \
                               /    |    \
                    context_manager  tools  memory_store
                              \              /
                               \            /
                                config.py  (shared by all)


  Import order matters:
  config.py must load FIRST — it sets env vars LangSmith needs at startup.
```

---

## 8. ROUTER DECISION LOGIC

```
  User Input
      │
      ▼
  query.lower()
      │
      ├── contains digit AND calc keyword?
      │   ("calculate", "compute", "+", "-", etc.)
      │         │
      │         ▼
      │      type = "calculator"
      │      → calculator_tool(expression)
      │
      ├── contains search keyword?
      │   ("what is", "find", "explain", "search", etc.)
      │         │
      │         ▼
      │      type = "search"
      │      → search_tool(query)
      │
      └── none of the above
                │
                ▼
             type = "chat"
             → no tool, go straight to LLM
```

---

## 9. ENVIRONMENT & CONFIGURATION FLOW

```
  .env file                 config.py               All other modules
  ─────────                 ─────────               ────────────────
  LANGCHAIN_API_KEY    ──▶  load_dotenv()   ──▶     import config
  LANGCHAIN_PROJECT    ──▶  os.getenv()     ──▶     config.OPENROUTER_API_KEY
  OPENROUTER_API_KEY   ──▶  os.environ[]=  ──▶     config.LLM_MODEL
  OPENROUTER_BASE_URL  ──▶  validate_config()──▶    config.LANGCHAIN_PROJECT
  LLM_MODEL            ──▶  (fail fast)
  MAX_RECENT_MESSAGES
  SUMMARY_THRESHOLD

  ▲
  One source of truth.
  Change the model? Edit .env.
  Change the project name? Edit .env.
  No other file needs touching.
```

---

## 10. PRODUCTION SCALABILITY PATH

```
  THIS PROJECT (learning)          PRODUCTION (scale)
  ───────────────────────          ──────────────────

  memory_store: JSON file    →     PostgreSQL / Redis
  search_tool:  dict lookup  →     Serper / Tavily API
  router:       keywords     →     LLM-based classifier
  summary:      gpt-4o-mini  →     smaller/cheaper model
  single file:  memory.json  →     per-user database rows
  local run:    python main  →     FastAPI + Docker + K8s

  The ARCHITECTURE stays identical.
  Only the implementations change.
  That's the point of clean modular design.
```
