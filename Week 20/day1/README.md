# Production AI Agent
### Week 20 — LangSmith Observability + Model Context Protocol (MCP)

---

## What This Project Is

A production-style AI agent that demonstrates two core skills every serious AI engineer needs:

| Skill | Tool | What It Gives You |
|---|---|---|
| **Observability** | LangSmith | See every step your system takes, in real time |
| **Context Engineering** | MCP | Control exactly what the LLM receives |

This is not a chatbot demo. This is the architecture pattern used in real production systems.

---

## Project Structure

```
production_agent/
│
├── config.py             → Environment setup + LangSmith tracing config
├── memory_store.py       → Persistent user profiles (JSON)
├── context_manager.py    → MCP: structured context + context slicing
├── tools.py              → Search + calculator tools (each @traceable)
├── pipeline.py           → 4-step traced pipeline
├── main.py               → CLI entry point
│
├── data/
│   └── memory.json       → All user profiles saved here
│
├── .env.example          → Copy this to .env and add your keys
├── requirements.txt      → Python dependencies
│

```

---

## How It Works

Every user message flows through this pipeline:

```
User Input     -> What is 20+20 !
    ↓
Router          → classifies: search / calculator / chat ! 
    ↓
Tool Executor   → runs tool if needed (search or calculator) ! 
    ↓
Context Builder → MCP: builds structured prompt from profile + summary + recent messages (structured prompt) ....
    ↓
LLM Call        → sends to OpenRouter/LLM → response !
    ↓
LangSmith       → records every step as a traceable span ....
```

Every arrow above is a separate **span** visible in LangSmith.

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create your `.env` file

```bash
cp .env.example .env
```

Then open `.env` and fill in:

```env
LANGCHAIN_API_KEY=lsv2_pt_your_key_here       # from smith.langchain.com
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=Week20-Production-Agent

OPENROUTER_API_KEY=sk-or-v1-your_key_here     # from openrouter.ai/keys
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=openai/gpt-4o-mini
```

### 3. Create your LangSmith project

1. Go to [smith.langchain.com](https://smith.langchain.com)
2. Click **Tracing** → **New Project**
3. Name it exactly: `Week20-Production-Agent`
4. Click **Create**

### 4. Run

```bash
python main.py
```

---

## Where to Get the API Keys

| Key | Where to get it |
|---|---|
| `LANGCHAIN_API_KEY` | [smith.langchain.com](https://smith.langchain.com) → Settings → API Keys |
| `OPENROUTER_API_KEY` | [openrouter.ai/keys](https://openrouter.ai/keys) |

> **Note:** `LANGCHAIN_API_KEY` is the LangSmith key. LangSmith is a product by LangChain — same company, so the variable is named `LANGCHAIN_API_KEY`.

---

## CLI Commands

Once running, type messages to chat. Special commands:

| Command | What it does |
|---|---|
| `exit` | End the session |
| `/stats` | Show your memory profile |
| `/users` | List all known users |
| `/clear` | Clear the screen |

---


## What You See in LangSmith

After running a query, open your LangSmith project. Click any run:

```
Agent Pipeline                    ← root span (the full pipeline)
  ├── Router          0.00s       ← keyword classification
  ├── Tool Executor   0.00s       ← dispatches tool if needed
  │     ├── Tool Router
  │     └── Search Tool  0.00s   ← actual tool result
  ├── Context Builder (MCP) 0.00s ← structured prompt assembly
  └── LLM Call        3.19s      ← actual API call to OpenRouter
```

Click any span to see:
- **Input** — what went in
- **Output** — what came out
- **Metadata** — latency, runtime, SDK version

---

## What Is MCP (Model Context Protocol)?

Instead of dumping the full conversation history into the LLM, MCP structures context into labeled blocks:

```
=== SYSTEM ===
You are a helpful AI assistant.

=== USER PROFILE ===
Name: Anant | Preferences: technical

=== CONVERSATION SUMMARY ===
User has been learning about LangSmith and observability...

=== RECENT MESSAGES ===
User: what is MCP?
Assistant: MCP is a structured approach...

=== TOOL RESULTS ===
Search results for 'what is python?': ...

=== CURRENT QUERY ===
How does context slicing work?
```

**Why this matters:**
- LLM receives organized, relevant information — not a wall of text
- Old messages get compressed into a summary (context slicing)
- Token count stays flat even after long conversations
- Responses are more accurate and focused

---

## Context Slicing

When conversation exceeds 10 messages:

```
Before slicing:  20 messages → ~800 tokens
                      ↓
  Older 15 → LLM summarizes → 2–3 sentences stored in memory
  Recent 5  → sent directly
                      ↓
After slicing:   5 messages + summary → ~200 tokens
```

The system remembers everything. The context stays small.

---

## Key Design Decisions

**Why OpenRouter instead of OpenAI directly?**
One API key gives access to GPT-4o, Claude, Llama, and dozens of other models.
Switch models by changing one line in `.env`.

**Why JSON instead of a database?**
You can open `data/memory.json` and read it directly.
For teaching, visibility beats sophistication.
The interface is the same — swap JSON for PostgreSQL without changing any other file.

**Why no LangChain chains or LangGraph?**
Every step is plain Python decorated with `@traceable`.
You can read, understand, and modify every line without learning a framework.
This is intentional — understand the architecture first, adopt frameworks later.

---

## Requirements

```
openai>=1.30.0
langsmith>=0.1.75
python-dotenv>=1.0.0
```

Python 3.10+ required (uses `str | None` union type syntax).

---

