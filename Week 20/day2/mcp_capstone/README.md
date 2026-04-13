# MCP Capstone – Context-Aware Scalable AI Agent

> "AI systems don't fail because models are weak.
> They fail because context is poorly managed."

This is the **final capstone** of the AI curriculum. It demonstrates a
production-grade context management system built on the **Model Context
Protocol (MCP)** pattern.

---

## What This Is

This is **not** a chatbot.

It is a **context-aware, scalable AI agent** that demonstrates:

| Concept | Implementation |
|---|---|
| Structured context injection | `context_manager.py` – 5-layer MCP prompt |
| Persistent memory | `memory_store.py` – JSON-backed per-user records |
| Automatic memory compression | `summarizer.py` – LLM-based history summarisation |
| Production context validation | `validator.py` – size, memory, relevance checks |
| Modular pipeline | `agent_pipeline.py` – 7 discrete, testable stages |

---

## Project Structure

```
mcp_capstone/
├── config.py           # All constants and env vars
├── memory_store.py     # Persistent JSON memory (load, save, append, summarise)
├── context_manager.py  # MCP engine – builds the structured prompt
├── summarizer.py       # LLM-powered memory compression
├── validator.py        # Context quality validation layer
├── agent_pipeline.py   # 7-stage orchestration pipeline
└── main.py             # CLI entry point
```

---

## Setup

```bash
cd mcp_capstone
pip install -r requirements.txt
cp .env.example .env
# edit .env and add your ANTHROPIC_API_KEY
```

---

## Run

```bash
python main.py
```

---

## How It Works

### Context Structure (MCP Layers)

Every LLM call is structured as five explicit layers:

```
System Instruction
────────────────────────────────────────────────────────────
User Profile:
  Name: Anant
  Preferences: technical
────────────────────────────────────────────────────────────
Conversation Summary:
  • User is learning LangGraph and AI agent patterns
  • Discussed memory management and context slicing
────────────────────────────────────────────────────────────
Recent Messages:
  [User]: What is context slicing?
  [Assistant]: Context slicing is the practice of…
────────────────────────────────────────────────────────────
User Query:
  How does summarisation work in this system?
```

### Pipeline Stages

```
User Input
   ↓  Stage 1 – Load memory from JSON
   ↓  Stage 2 – Append user message
   ↓  Stage 3 – Summarise if history > threshold (10 msgs)
   ↓  Stage 4 – Build MCP structured context
   ↓  Stage 5 – Validate (size, memory, relevance)
   ↓  Stage 6 – LLM call with full context
   ↓  Stage 7 – Store assistant response
   ↓
Response
```

### Memory Compression

Once the conversation history exceeds **10 messages**:
- The older messages are sent to Claude/LLM to be summarised into bullet points
- The summary replaces the old messages in the context
- Only the **last 5 raw messages** are kept in full
- The agent stays fast and cheap, no matter how long the session runs

---

## Session Demonstration

**Session 1:**
```
User ID: rahul
You: I'm learning LangGraph and building AI agents
Agent: Great! LangGraph is a powerful framework for…
```

**Session 2 (next day):**
```
User ID: rahul
Welcome back, Rahul!
  Last session summary: • User is learning LangGraph…
```

---

## Key Design Principles

1. **Separation of concerns** – each file has one job
2. **Context is explicit** – every layer is visible and debuggable
3. **Fail loudly** – the validator prints warnings before LLM calls
4. **Scale by design** – compression keeps context small as sessions grow
5. **Persistent by default** – memory survives across Python sessions
