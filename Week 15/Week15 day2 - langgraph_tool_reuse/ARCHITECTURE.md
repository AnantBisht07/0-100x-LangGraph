# Architecture Visualization

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE                             │
│                            (main.py)                                │
│                                                                     │
│  Commands:                                                          │
│  • python main.py qna "question"                                   │
│  • python main.py summarize "topic"                                │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ Invokes
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        BEHAVIOR LAYER                               │
│                         (Graphs Package)                            │
│                                                                     │
│  ┌─────────────────────────┐    ┌─────────────────────────┐        │
│  │   QnA Graph             │    │   Summarizer Graph      │        │
│  │   (qna_graph.py)        │    │   (summarizer_graph.py) │        │
│  │                         │    │                         │        │
│  │  • QnA system prompt    │    │  • Summary prompt       │        │
│  │  • Temperature: 0       │    │  • Temperature: 0.3     │        │
│  │  • Factual focus        │    │  • Synthesis focus      │        │
│  └─────────────────────────┘    └─────────────────────────┘        │
│              │                              │                       │
│              └──────────────────────────────┘                       │
│                             │                                       │
│                             │ Both import                           │
│                             ▼                                       │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │
┌─────────────────────────────────────────────────────────────────────┐
│                       CAPABILITY LAYER                              │
│                        (Tools Package)                              │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │         Document Search ToolNode                              │ │
│  │         (document_search.py)                                  │ │
│  │                                                               │ │
│  │  1. Load documents from data/sample_docs/                    │ │
│  │  2. Split into chunks                                        │ │
│  │  3. Create embeddings (OpenAI)                               │ │
│  │  4. Store in FAISS vector store                              │ │
│  │  5. Provide search_documents(@tool)                          │ │
│  │  6. Wrap in ToolNode for LangGraph                           │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ⭐ DEFINED ONCE, USED BY BOTH GRAPHS ⭐                            │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ Uses
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                  │
│                                                                     │
│  📁 data/sample_docs/                                               │
│     • ai_fundamentals.txt                                          │
│     • [your documents here]                                        │
│                                                                     │
│  🗄️  FAISS Vector Store (in-memory)                                │
│     • Document chunks as embeddings                                │
│     • Similarity search capability                                 │
└─────────────────────────────────────────────────────────────────────┘
```

## Graph A: QnA Flow Detail

```
User: "What is machine learning?"
  │
  ├─→ [main.py] Parse command "qna"
  │
  └─→ [qna_graph.py] create_qna_graph()
           │
           ├─→ Build StateGraph with QnAState
           │
           ├─→ Add agent_node (LLM + QnA prompt)
           │
           ├─→ Add tools node (get_document_search_node())  ← IMPORT
           │
           └─→ Compile & Execute:
                  │
                  ├─→ START
                  │
                  ├─→ [Agent Node]
                  │    • System: "You are a QnA assistant..."
                  │    • User: "What is machine learning?"
                  │    • LLM decides: Call search_documents tool
                  │    • Returns: AIMessage with tool_call
                  │
                  ├─→ [should_continue] Routing
                  │    • Sees tool_calls → route to "tools"
                  │
                  ├─→ [Tools Node] ← SHARED TOOL
                  │    • Executes: search_documents("machine learning")
                  │    • Retrieves 3 relevant chunks from FAISS
                  │    • Returns: ToolMessage with chunks
                  │
                  ├─→ [Agent Node]
                  │    • Sees tool results (chunks)
                  │    • Synthesizes answer from chunks
                  │    • Returns: AIMessage with answer
                  │
                  ├─→ [should_continue] Routing
                  │    • No tool_calls → route to END
                  │
                  └─→ END
                       │
                       └─→ Final answer returned to user
```

## Graph B: Summarizer Flow Detail

```
User: "Summarize key concepts"
  │
  ├─→ [main.py] Parse command "summarize"
  │
  └─→ [summarizer_graph.py] create_summarizer_graph()
           │
           ├─→ Build StateGraph with SummarizerState
           │
           ├─→ Add agent_node (LLM + Summary prompt)
           │
           ├─→ Add tools node (get_document_search_node())  ← SAME IMPORT
           │
           └─→ Compile & Execute:
                  │
                  ├─→ START
                  │
                  ├─→ [Agent Node]
                  │    • System: "You are a summarization assistant..."
                  │    • User: "Summarize key concepts"
                  │    • LLM decides: Call search_documents tool
                  │    • Returns: AIMessage with tool_call
                  │
                  ├─→ [should_continue] Routing
                  │    • Sees tool_calls → route to "tools"
                  │
                  ├─→ [Tools Node] ← SAME SHARED TOOL AS QnA!
                  │    • Executes: search_documents("key concepts")
                  │    • Retrieves 3 relevant chunks from FAISS
                  │    • Returns: ToolMessage with chunks
                  │
                  ├─→ [Agent Node]
                  │    • Sees tool results (chunks)
                  │    • Synthesizes SUMMARY from chunks
                  │    • Returns: AIMessage with summary
                  │
                  ├─→ [should_continue] Routing
                  │    • No tool_calls → route to END
                  │
                  └─→ END
                       │
                       └─→ Final summary returned to user
```

## Code Path Analysis

### Tool Definition (Once)
```python
# tools/document_search.py

@tool
def search_documents(query: str, k: int = 3) -> str:
    """Search through documents and return relevant chunks."""
    vector_store = _initialize_vector_store()
    results = vector_store.similarity_search(query, k=k)
    return format_results(results)

def get_document_search_node():
    """Factory for ToolNode."""
    tool = create_document_search_tool()
    return ToolNode([tool])  # ← This is what graphs import
```

### Graph A Import (Reuse)
```python
# graphs/qna_graph.py

from tools import get_document_search_node  # ← Import, don't redefine

def create_qna_graph():
    workflow = StateGraph(QnAState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", get_document_search_node())  # ← Reuse
    # ... rest of graph
    return workflow.compile()
```

### Graph B Import (Reuse)
```python
# graphs/summarizer_graph.py

from tools import get_document_search_node  # ← Same import

def create_summarizer_graph():
    workflow = StateGraph(SummarizerState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", get_document_search_node())  # ← Same reuse
    # ... rest of graph
    return workflow.compile()
```

## The Reuse Principle

### ❌ Bad Pattern (Code Duplication)
```
graphs/
├── qna_graph.py
│   ├── def search_documents(...)  ← Duplicated code
│   └── def create_qna_graph(...)
│
└── summarizer_graph.py
    ├── def search_documents(...)  ← Duplicated code
    └── def create_summarizer_graph(...)

Problems:
• Bug in search? Fix in 2 places
• Want to change chunk size? Update 2 files
• Add 3rd graph? Copy code again
• Testing? Test same code 3 times
```

### ✅ Good Pattern (Reuse)
```
tools/
└── document_search.py
    └── def search_documents(...)  ← Defined ONCE

graphs/
├── qna_graph.py
│   └── import from tools  ← Reuse
│
└── summarizer_graph.py
    └── import from tools  ← Reuse

Benefits:
• Bug in search? Fix in 1 place
• Want to change chunk size? Update 1 file
• Add 3rd graph? Just import, no duplication
• Testing? Test tool once, mock in graph tests
```

## Scalability Vision

### Current State (Demo)
```
1 Tool (Document Search)
  ↓
2 Graphs (QnA, Summarizer)
```

### Near Future (Your Next Project)
```
3 Tools (Document Search, Web Search, Calculator)
  ↓
5 Graphs (QnA, Summarizer, Comparison, Analysis, Router)
```

### Production Scale
```
20+ Tools
  • Document search
  • Web search
  • Database queries
  • API calls (weather, stocks, etc.)
  • Calculations
  • Image analysis
  • Code execution
  • Email sending
  • Calendar management
  • ...and more

  ↓

30+ Graphs
  • Customer support chatbot
  • Research assistant
  • Data analyst
  • Code reviewer
  • Meeting scheduler
  • Report generator
  • Multi-agent orchestrator
  • ...and more
```

**Key Insight**: As you scale, the RATIO of graphs to tools increases. You'll have many graphs using combinations of a smaller set of core tools.

## Decision Framework

### When to Create a New Tool?
```
Question: "Can the system do X?"
Answer: "No"
→ Create a new tool
```

Example: System can search docs but not the web
→ Create `web_search.py` tool

### When to Create a New Graph?
```
Question: "Should the system behave like Y?"
Answer: "That's a new workflow"
→ Create a new graph
```

Example: System can QnA and summarize, but you want comparison
→ Create `comparison_graph.py` using existing tools

### When to Modify a Tool?
```
Question: "Is the current capability insufficient?"
Answer: "Yes, ALL graphs would benefit from the improvement"
→ Modify the tool
```

Example: Search returns too few chunks (affects all graphs)
→ Modify `document_search.py` to return more chunks

### When to Modify a Graph?
```
Question: "Should the behavior change?"
Answer: "Yes, but only for this specific use case"
→ Modify the graph
```

Example: QnA should be friendlier, but Summarizer stays formal
→ Modify `qna_graph.py` system prompt only

## Summary

This architecture achieves:

1. **Separation of Concerns**
   - Tools: Pure capabilities
   - Graphs: Composed behaviors

2. **Reusability**
   - Write once, import everywhere
   - Single source of truth

3. **Maintainability**
   - Changes in one place
   - Easy to test

4. **Scalability**
   - Add graphs without duplicating tools
   - Compose tools into complex behaviors

This is the foundation of production LangGraph systems.
