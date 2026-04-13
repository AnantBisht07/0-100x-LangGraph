# LangGraph Studio Complete Setup Guide

## What is LangGraph Studio?

LangGraph Studio is a visual IDE for debugging and testing LangGraph agents. It provides:
- Visual graph representation of your agent
- Interactive chat interface
- Step-by-step debugging
- State inspection at each node

## Prerequisites

- Python 3.9+
- Virtual environment (recommended)

## Installation

### 1. Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate (Windows CMD)
.venv\Scripts\activate

# Activate (Mac/Linux)
source .venv/bin/activate
```

### 2. Install Required Packages

```bash
# Core LangGraph packages
pip install langgraph langchain-core langchain-openai

# For loading .env files
pip install python-dotenv

# LangGraph CLI for Studio
pip install "langgraph-cli[inmem]"
```

## Files You Need to Create

You need **4 files** in your project:

```
your-project/
├── agent.py           # Your LangGraph agent code
├── langgraph.json     # LangGraph Studio configuration
├── requirements.txt   # Python dependencies
└── .env               # API keys
```

---

## File 1: `agent.py` (Your Agent Code)

### Basic Agent (Graph tab only)

```python
from typing import TypedDict
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
import os

load_dotenv()

# Define state
class AgentState(TypedDict):
    user_message: HumanMessage

# Create LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

# Define node function
def first_node(state: AgentState) -> AgentState:
    response = llm.invoke(state["user_message"])
    print(f"\nAI: {response.content}")
    return state

# Build graph
graph = StateGraph(AgentState)
graph.add_node("node1", first_node)
graph.add_edge(START, "node1")
graph.add_edge("node1", END)

# IMPORTANT: Export as variable - this name goes in langgraph.json
agent = graph.compile()
```

### Agent with Chat Support (Graph + Chat tabs)

For the Chat tab to work, use `messages` key in state:

```python
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import os

load_dotenv()

# State MUST have "messages" key for Chat tab
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# Create LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

# Node function
def first_node(state: AgentState):
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

# Build graph
graph = StateGraph(AgentState)
graph.add_node("node1", first_node)
graph.add_edge(START, "node1")
graph.add_edge("node1", END)

# Export compiled graph
agent = graph.compile()
```

### Using OpenRouter Instead of OpenAI

```python
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    base_url="https://openrouter.ai/api/v1"
)
```

---

## File 2: `langgraph.json` (Studio Configuration)

```json
{
  "graphs": {
    "agent": "./agent.py:agent"
  },
  "env": ".env",
  "dependencies": ["."]
}
```

### What Each Key Means

| Key | Value | Description |
|-----|-------|-------------|
| `graphs` | `{"name": "path:variable"}` | Maps graph name to file path and variable name |
| `env` | `".env"` | Path to environment variables file |
| `dependencies` | `["."]` | Directories to install (`.` = current dir with requirements.txt) |

### Graph Path Format

```
"./agent.py:agent"
   │         │
   │         └── Variable name (agent = graph.compile())
   └── File path
```

### Multiple Graphs Example

```json
{
  "graphs": {
    "simple_agent": "./agent.py:agent",
    "rag_agent": "./rag.py:rag_graph",
    "chatbot": "./chatbot.py:chat_agent"
  },
  "env": ".env",
  "dependencies": ["."]
}
```

---

## File 3: `requirements.txt` (Dependencies)

```
langgraph
langchain-core
langchain-openai
python-dotenv
```

---

## File 4: `.env` (API Keys)

### For OpenAI

```
OPENAI_API_KEY=sk-your-openai-key-here
```

### For OpenRouter

```
OPENAI_API_KEY=sk-or-v1-your-openrouter-key-here
```

**Note:** Add `.env` to `.gitignore` to keep your keys private!

---

## Running LangGraph Studio

### Start the Studio

```bash
langgraph dev
```

### What Happens

1. CLI reads `langgraph.json`
2. Loads your graph from the specified file
3. Starts local server at `http://127.0.0.1:8123`
4. Opens Studio in your browser

### Studio Interface

| Tab | Description |
|-----|-------------|
| **Graph** | Visual representation of your agent nodes and edges |
| **Chat** | Chat interface (requires `messages` key in state) |
| **Memory** | View agent memory/state |
| **Interrupts** | Set breakpoints in your graph |

---

## Troubleshooting

### Error: "langgraph not recognized"

```bash
pip install "langgraph-cli[inmem]"
```

### Error: "No dependencies found"

Add `"dependencies": ["."]` to `langgraph.json`

### Error: "Create a graph with messages key"

The Chat tab requires state with `messages` key. Use:

```python
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
```

### Error: "API key not found"

1. Check `.env` file exists
2. Check key name is correct
3. Make sure `load_dotenv()` is called in your code

### Error: "Invalid API key"

- For OpenRouter: Use `base_url="https://openrouter.ai/api/v1"`
- Check your key is valid and has credits

---

## Quick Reference

### Minimum Setup Checklist

- [ ] Create `agent.py` with compiled graph exported as variable
- [ ] Create `langgraph.json` pointing to your graph
- [ ] Create `requirements.txt` with dependencies
- [ ] Create `.env` with API key
- [ ] Install `langgraph-cli[inmem]`
- [ ] Run `langgraph dev`

### Key Points

1. **Export your graph**: `agent = graph.compile()` - the variable name matters
2. **Config format**: `"file.py:variable"` in langgraph.json
3. **Chat tab**: Requires `messages` key in state
4. **OpenRouter**: Add `base_url` parameter to ChatOpenAI
