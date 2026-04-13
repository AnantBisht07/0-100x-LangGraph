# Quick Reference Guide

## Installation & Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create .env file
cp .env.example .env

# 3. Add your API keys to .env
# NEWS_API_KEY=your_key_here
# OPENAI_API_KEY=your_key_here

# 4. Run the agent
python agent.py
```

## Key Code Patterns

### 1. External API Tool Pattern

```python
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode

@tool
def search_news(query: str) -> str:
    """Tool that calls external API"""
    response = requests.get(api_url, params=params)
    return format_results(response.json())

# Wrap in ToolNode for LangGraph
workflow.add_node("news_tool_node", ToolNode([search_news]))
```

**Why?**
- `@tool` makes function LLM-callable
- `ToolNode` wraps for graph execution
- Automatic state management

### 2. Parallel Execution Pattern

```python
# Fan-out: One node to many
workflow.add_edge("news_tool_node", "summarizer_1")
workflow.add_edge("news_tool_node", "summarizer_2")
workflow.add_edge("news_tool_node", "summarizer_3")

# Fan-in: Many nodes to one
workflow.add_edge("summarizer_1", "merge")
workflow.add_edge("summarizer_2", "merge")
workflow.add_edge("summarizer_3", "merge")
```

**Result**: All summarizers run simultaneously

### 3. State Sharing Pattern

```python
def parallel_node_1(state: MessagesState):
    # Read shared data from state
    messages = state["messages"]
    articles = messages[3].content  # Tool results

    # Process independently
    result = process(articles)

    # Return new message
    return {"messages": [result]}

def parallel_node_2(state: MessagesState):
    # Reads SAME articles from state
    messages = state["messages"]
    articles = messages[3].content  # Same tool results

    # Different processing
    result = different_process(articles)

    return {"messages": [result]}
```

**Key**: All nodes read same state, no redundant API calls

### 4. Merge Pattern

```python
def merge_summaries(state: MessagesState):
    """Consolidate parallel results"""
    llm = ChatOpenAI(temperature=0.3)

    system_message = SystemMessage(content="""
    You will see multiple analyses.
    Combine them into one cohesive output.
    """)

    messages = state["messages"]
    response = llm.invoke([system_message] + messages)

    return {"messages": [response]}
```

## Graph Structure Quick Reference

```python
from langgraph.graph import StateGraph, MessagesState, START, END

# 1. Create graph
workflow = StateGraph(MessagesState)

# 2. Add nodes
workflow.add_node("node_name", node_function)

# 3. Add edges
workflow.add_edge(START, "first_node")
workflow.add_edge("first_node", "second_node")
workflow.add_edge("last_node", END)

# 4. Compile
graph = workflow.compile()

# 5. Execute
result = graph.invoke({"messages": [HumanMessage(content="question")]})
```

## Common Node Types

### Agent Node (LLM Decision)

```python
def agent_node(state: MessagesState):
    llm = ChatOpenAI(temperature=0)
    system_msg = SystemMessage(content="You are an expert...")
    response = llm.invoke([system_msg] + state["messages"])
    return {"messages": [response]}
```

### Agent with Tools

```python
def agent_with_tools(state: MessagesState):
    llm = ChatOpenAI(temperature=0)
    llm_with_tools = llm.bind_tools([tool1, tool2])
    response = llm_with_tools.invoke([system_msg] + state["messages"])
    return {"messages": [response]}
```

### Tool Execution Node

```python
# Don't write this manually - use ToolNode
workflow.add_node("tools", ToolNode([tool1, tool2, tool3]))
```

### Processing Node (No LLM)

```python
def processing_node(state: MessagesState):
    messages = state["messages"]
    data = messages[-1].content

    # Pure processing
    result = process_data(data)

    return {"messages": [AIMessage(content=result)]}
```

## Message Types

```python
from langchain_core.messages import (
    HumanMessage,    # User input
    AIMessage,       # Assistant response
    SystemMessage,   # System instructions
    ToolMessage      # Tool results
)

# Usage
HumanMessage(content="user question")
AIMessage(content="assistant response")
SystemMessage(content="system prompt")
ToolMessage(content="tool output", tool_call_id="id")
```

## Debugging

### Print State at Each Node

```python
def debug_node(state: MessagesState):
    print(f"\n{'='*50}")
    print(f"Node: debug_node")
    print(f"Messages count: {len(state['messages'])}")
    for i, msg in enumerate(state["messages"]):
        print(f"[{i}] {type(msg).__name__}: {msg.content[:100]}...")
    print(f"{'='*50}\n")

    # Your actual logic here
    return {"messages": [...]}
```

### View Final State

```python
final_state = graph.invoke(initial_state)

# Print all messages
for i, msg in enumerate(final_state["messages"]):
    print(f"\n[{i}] {type(msg).__name__}")
    print(msg.content if hasattr(msg, 'content') else msg)
```

### LangGraph Studio

1. Open project in Studio
2. Click nodes to inspect state
3. View message history
4. See execution timing
5. Debug tool calls

## Environment Variables

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Required
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Optional (with defaults)
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "anthropic/claude-3.5-sonnet")
```

## Common Errors & Solutions

### "NEWS_API_KEY not set"

```bash
# Check .env file exists
ls -la .env

# Check contents (without exposing key)
grep NEWS_API_KEY .env

# Recreate if needed
cp .env.example .env
# Then edit .env with actual keys
```

### "No articles found"

```python
# Check API response
response = requests.get(url, params=params)
print(response.json())  # See actual API response

# Common causes:
# - Query too specific
# - Free tier limitations
# - API key invalid
```

### "Rate limit exceeded"

```python
# News API free tier: 100 requests/day
# Solutions:
# 1. Wait 24 hours
# 2. Use caching
# 3. Upgrade API plan

# Caching example:
import hashlib
cache = {}

@tool
def search_news_cached(query: str):
    key = hashlib.md5(query.encode()).hexdigest()
    if key in cache:
        return cache[key]
    result = call_api(query)
    cache[key] = result
    return result
```

### "Graph not executing in parallel"

```python
# Check: Multiple edges from same source
workflow.add_edge("source", "target1")  # ✓
workflow.add_edge("source", "target2")  # ✓
workflow.add_edge("source", "target3")  # ✓

# NOT this (sequential):
workflow.add_edge("source", "target1")
workflow.add_edge("target1", "target2")  # ✗
workflow.add_edge("target2", "target3")  # ✗
```

## Performance Tips

### 1. Reduce LLM Calls

```python
# Bad: LLM call in loop
for item in items:
    llm.invoke(f"Process {item}")  # N calls

# Good: Batch processing
llm.invoke(f"Process all: {items}")  # 1 call
```

### 2. Use Appropriate Temperature

```python
# Factual tasks: temperature=0
llm = ChatOpenAI(temperature=0)  # Deterministic

# Creative tasks: temperature=0.3-0.7
llm = ChatOpenAI(temperature=0.5)  # Creative

# Very creative: temperature=0.7-1.0
llm = ChatOpenAI(temperature=0.8)  # Highly creative
```

### 3. Parallel When Possible

```python
# Identify independent operations
# Run them in parallel, not sequentially

# Example: Multiple summarizations
# DON'T run sequentially
# DO use parallel pattern (this project)
```

### 4. Cache Expensive Operations

```python
# Cache API calls
# Cache embeddings
# Cache LLM responses for repeated queries

from functools import lru_cache

@lru_cache(maxsize=100)
def expensive_operation(input_data):
    # Cached result
    return process(input_data)
```

## Testing Patterns

### Unit Test a Node

```python
def test_qna_agent():
    state = {
        "messages": [HumanMessage(content="What's new in AI?")]
    }

    result = qna_agent(state)

    assert len(result["messages"]) == 1
    assert isinstance(result["messages"][0], AIMessage)
    print(f"Query: {result['messages'][0].content}")
```

### Test Tool Directly

```python
def test_search_news():
    result = search_news.invoke({"query": "AI", "max_articles": 3})

    assert isinstance(result, str)
    assert "Article" in result
    print(result)
```

### Test Full Graph

```python
def test_full_workflow():
    graph = create_research_workflow()

    initial_state = {
        "messages": [HumanMessage(content="climate change")]
    }

    result = graph.invoke(initial_state)

    assert "messages" in result
    assert len(result["messages"]) > 0
    print(f"Final output: {result['messages'][-1].content}")
```

## Next Steps Checklist

- [ ] Run basic workflow successfully
- [ ] Understand parallel execution timing
- [ ] Modify system prompts and observe changes
- [ ] Add print statements for debugging
- [ ] Visualize in LangGraph Studio
- [ ] Add a fourth summarizer node
- [ ] Implement caching for API calls
- [ ] Try different research topics
- [ ] Experiment with temperatures
- [ ] Add error handling
- [ ] Implement retry logic
- [ ] Create custom tools
- [ ] Build conditional routing

## Resources

- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [LangChain Tools](https://python.langchain.com/docs/modules/agents/tools/)
- [News API Docs](https://newsapi.org/docs)
- [OpenRouter](https://openrouter.ai/docs)
- [MessagesState Reference](https://langchain-ai.github.io/langgraph/reference/graphs/#messagesstate)
