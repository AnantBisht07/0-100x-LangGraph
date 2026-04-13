# Simple Memory-Controlled Agent

## What Does This Do?

This agent **automatically compresses old conversation** to prevent running out of memory.

**Problem:** If you chat for 100 turns, the AI has to read all 100 messages every time. Too slow and expensive!

**Solution:** After every 3 turns, compress old messages into a short summary. Keep only recent 4 messages.

## How It Works

```
Turn 1-3: Normal chat (no compression)
Turn 3: Compress old messages → summary
Turn 4-6: Chat continues (AI sees: summary + recent 4 messages)
Turn 6: Compress again
...
```

## Architecture

```
User Input
    ↓
Chat Node (LLM responds)
    ↓
Router (window_count >= 3?)
    ↓
    ├─ YES → Summarizer Node (compress old messages)
    └─ NO  → END
```

## State Explained

```python
ConversationState:
  messages      → All messages (gets trimmed after compression)
  summary       → Compressed old context
  turn_count    → Total turns (never resets)
  window_count  → Turns since last compression (resets to 0)
```

## Run It

```bash
python simple_memory_agent.py
```

Example:
```
=== Memory-Controlled Chatbot ===
Type 'quit' to exit

You: Hi, I'm planning a trip to Japan
AI: That sounds exciting! I'd be happy to help...
[Turn 1 | Window: 1 | Summary: 0 chars]

You: What cities should I visit?
AI: I recommend Tokyo, Kyoto, and Osaka...
[Turn 2 | Window: 2 | Summary: 0 chars]

You: How many days in each?
AI: I suggest 3-4 days in Tokyo...
[Turn 3 | Window: 3 | Summary: 0 chars]

[COMPRESSED] Older messages compressed into summary

You: What about food?
AI: Based on your trip to Tokyo, Kyoto, and Osaka...
[Turn 4 | Window: 1 | Summary: 145 chars]
```

## Key Code Parts

### 1. Chat Node
```python
def chat_node(state):
    context = []
    if state["summary"]:
        context.append(SystemMessage(content=f"Previous: {state['summary']}"))
    context.extend(state["messages"][-4:])  # Last 4 messages only
    response = llm.invoke(context)
    return {"messages": [response], "turn_count": +1, "window_count": +1}
```

### 2. Summarizer Node
```python
def summarizer_node(state):
    older = state["messages"][:-4]  # Everything except last 4
    summary = llm.invoke("Summarize: " + older)
    return {
        "messages": state["messages"][-4:],  # Keep only recent 4
        "summary": summary,
        "window_count": 0  # Reset counter
    }
```

### 3. Router
```python
def should_compress(state):
    if state["window_count"] >= 3:
        return "summarizer"
    return "end"
```

## Why Two Counters?

- **turn_count**: Total conversation turns (1, 2, 3, 4, 5, 6...)
- **window_count**: Turns since compression (1, 2, 3, **reset to 0**, 1, 2, 3, **reset to 0**)

This prevents compressing on every single turn!

## Benefits

✅ **Bounded memory**: Old messages deleted after compression
✅ **Fast responses**: LLM only reads summary + recent messages
✅ **No context loss**: Summary preserves important info
✅ **Scalable**: Can chat for 1000 turns without slowdown

## Compare With/Without Compression

| Turns | Without Compression | With Compression |
|-------|---------------------|------------------|
| 10    | 20 messages         | Summary + 4 msgs |
| 50    | 100 messages        | Summary + 4 msgs |
| 100   | 200 messages        | Summary + 4 msgs |

## Learning Points

1. **State Management**: Use TypedDict to track conversation state
2. **Reducers**: `add_messages` automatically appends messages
3. **Conditional Routing**: Router function decides graph flow
4. **Context Compression**: Trade-off between memory and fidelity
5. **Counter Pattern**: Separate lifetime counter from window counter

## Customize

Change compression threshold:
```python
def should_compress(state):
    if state["window_count"] >= 5:  # Compress after 5 turns instead of 3
        return "summarizer"
```

Change recent window size:
```python
context.extend(state["messages"][-8:])  # Keep 8 recent messages instead of 4
```

---

**That's it!** Simple memory management without external databases.
