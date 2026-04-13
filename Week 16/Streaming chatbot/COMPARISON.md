# Streaming vs Non-Streaming - Side-by-Side Comparison

## Quick Visual Comparison

### Non-Streaming Output
```
You: Explain quantum physics

[Waiting... 3 seconds...]

AI: Quantum physics is a fundamental theory in physics that describes nature at the smallest scales of energy levels of atoms and subatomic particles. It challenges our classical understanding of how the universe works...

[Turn 1 | Window: 1 | Summary: 0 chars]
```

### Streaming Output
```
You: Explain quantum physics

AI: Quantum physics is a fundamental theory in physics that describes
nature at the smallest scales of energy levels of atoms and subatomic
particles. It challenges our classical understanding of how the universe
works...
    ↑ Text appears word by word as it's generated

[Turn 1 | Window: 1 | Summary: 0 chars]
```

## Code Comparison

### LLM Initialization

#### Non-Streaming
```python
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
    # No streaming parameter
)
```

#### Streaming
```python
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1",
    streaming=True  # ← Added this line
)
```

---

### Chat Node

#### Non-Streaming
```python
def chat_node(state: ConversationState):
    """Main chat handler"""

    context = []

    if state["summary"]:
        context.append(SystemMessage(content=f"Previous: {state['summary']}"))

    context.extend(state["messages"][-4:])

    # Single call, wait for full response
    response = llm.invoke(context)

    return {
        "messages": [response],
        "turn_count": state["turn_count"] + 1,
        "window_count": state["window_count"] + 1
    }
```

#### Streaming
```python
def chat_node_streaming(state: ConversationState):
    """Chat handler with streaming"""

    context = []

    if state["summary"]:
        context.append(SystemMessage(content=f"Previous: {state['summary']}"))

    context.extend(state["messages"][-4:])

    # Stream tokens and display immediately
    print("AI: ", end="", flush=True)

    full_response = ""
    for chunk in llm.stream(context):  # ← Loop through chunks
        if chunk.content:
            print(chunk.content, end="", flush=True)  # ← Display immediately
            full_response += chunk.content  # ← Accumulate

    print()  # New line

    # Create message with complete response
    response = AIMessage(content=full_response)

    return {
        "messages": [response],
        "turn_count": state["turn_count"] + 1,
        "window_count": state["window_count"] + 1
    }
```

---

### Display Output

#### Non-Streaming
```python
# In main loop
result = agent.invoke(state)
state = result

# Print response
ai_response = state["messages"][-1].content
print(f"AI: {ai_response}")  # ← All at once
```

#### Streaming
```python
# In main loop
result = agent.invoke(state)  # Streaming happens inside chat_node
state = result

# Response already printed during streaming
# No additional print needed
```

---

## What's Identical

### State Structure
```python
# Both versions use exact same state
class ConversationState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    summary: str
    turn_count: int
    window_count: int
```

### Router Node
```python
# Identical in both versions
def should_compress(state: ConversationState) -> Literal["summarizer", "end"]:
    if state["window_count"] >= 3:
        return "summarizer"
    return "end"
```

### Summarizer Node
```python
# Identical in both versions (uses invoke, not streaming)
def summarizer_node(state: ConversationState):
    older_messages = state["messages"][:-4]
    # ... build prompt ...
    summary = llm.invoke([HumanMessage(content=prompt)])  # Non-streaming
    # ... return updates ...
```

### Graph Structure
```python
# Identical in both versions
graph = StateGraph(ConversationState)
graph.add_node("chat", chat_node)  # or chat_node_streaming
graph.add_node("summarizer", summarizer_node)

graph.add_edge(START, "chat")
graph.add_conditional_edges("chat", should_compress,
                           {"summarizer": "summarizer", "end": END})
graph.add_edge("summarizer", END)
```

## User Experience Comparison

### Non-Streaming
```
Pros:
✓ Simple implementation
✓ Easy to test/debug
✓ Response appears complete
✓ Good for batch processing

Cons:
✗ No feedback during wait
✗ Feels slower
✗ Can't interrupt
✗ "Is it frozen?"
```

### Streaming
```
Pros:
✓ Immediate feedback
✓ Feels faster
✓ Can interrupt if wrong
✓ Engaging experience
✓ See progress

Cons:
✗ Slightly more complex
✗ Harder to debug
✗ Terminal-dependent
```

## Performance Metrics

### Time to First Token

| Version | TTFT |
|---------|------|
| Non-Streaming | 2-5 seconds (wait for all) |
| Streaming | 200-500ms (first token) |

### Total Time

| Version | Total Time |
|---------|------------|
| Non-Streaming | 2-5 seconds |
| Streaming | 2-5 seconds (same!) |

### Perceived Performance

| Version | User Perception |
|---------|-----------------|
| Non-Streaming | "Slow" (waiting feels long) |
| Streaming | "Fast" (progress visible) |

## File Size Comparison

| Metric | Non-Streaming | Streaming |
|--------|---------------|-----------|
| Lines of Code | 166 | 178 |
| Difference | - | +12 lines |
| Complexity | Simple | +5% |

**95% of code is identical!**

## When to Choose Each

### Choose Non-Streaming When:
- ✅ Building APIs (return JSON)
- ✅ Batch processing
- ✅ Testing/debugging
- ✅ Simplicity is priority
- ✅ No human watching output

### Choose Streaming When:
- ✅ User-facing chatbots
- ✅ Interactive applications
- ✅ Long responses expected
- ✅ Better UX needed
- ✅ Real-time feel desired

## Memory Management (Identical)

Both versions handle memory the same way:

```
Turn 1-2: No compression
Turn 3:   Compress → Create summary
Turn 4+:  Use summary + recent messages

Compression triggers:
  window_count >= 3 → Summarizer

State after compression:
  messages: Keep last 4
  summary: Compressed older messages
  window_count: Reset to 0
```

## Migration Path

### From Non-Streaming to Streaming

1. Add `streaming=True` to LLM config
2. Replace chat node with streaming version
3. Test streaming output
4. Done!

**Time**: 5 minutes

### From Streaming to Non-Streaming

1. Remove `streaming=True` from LLM config
2. Replace streaming chat node with simple version
3. Add print statement for response
4. Done!

**Time**: 5 minutes

## Example Conversation Output

### Non-Streaming
```
You: plan trip to tokyo

[Waiting...]

AI: Planning a trip to Tokyo can be exciting! Here's a guide: [full response]
[Turn 1 | Window: 1 | Summary: 0 chars]

You: what about kyoto

[Waiting...]

AI: Kyoto is Japan's cultural heart... [full response]
[Turn 2 | Window: 2 | Summary: 0 chars]
```

### Streaming
```
You: plan trip to tokyo

AI: Planning a trip to Tokyo can be exciting! Here's a guide: [text appears]
[Turn 1 | Window: 1 | Summary: 0 chars]

You: what about kyoto

AI: Kyoto is Japan's cultural heart... [text appears word by word]
[Turn 2 | Window: 2 | Summary: 0 chars]
```

## Architecture Diagram

### Non-Streaming Flow
```
User Input → Chat Node → [Wait] → Full Response → Display All
                              ↓
                          LLM API
```

### Streaming Flow
```
User Input → Chat Node → Stream Start
                         ↓
                    ┌────────────────┐
                    │ LLM API Stream │
                    └────────────────┘
                         ↓
              Token 1 → Display → Accumulate
              Token 2 → Display → Accumulate
              Token 3 → Display → Accumulate
                   ...
              Token N → Display → Accumulate
                         ↓
                   Full Response
```

## Testing Differences

### Non-Streaming Test
```python
def test_chat_node():
    state = {...}
    result = chat_node(state)
    assert result["messages"][0].content == "Expected response"
    # ✓ Easy to test
```

### Streaming Test
```python
def test_chat_node_streaming():
    state = {...}

    # Capture printed output
    from io import StringIO
    import sys
    captured = StringIO()
    sys.stdout = captured

    result = chat_node_streaming(state)

    sys.stdout = sys.__stdout__

    assert result["messages"][0].content == "Expected response"
    # ✓ Possible but slightly harder
```

## Summary Table

| Aspect | Non-Streaming | Streaming |
|--------|---------------|-----------|
| **Code Change** | N/A | +12 lines |
| **LLM Call** | `invoke()` | `stream()` |
| **Display** | All at once | Token by token |
| **User Wait** | 2-5s visible wait | 0.5s then progress |
| **Architecture** | Same | Same |
| **Memory** | Same | Same |
| **State** | Same | Same |
| **Complexity** | Simple | +5% |
| **UX** | Good | Better |
| **Use Case** | APIs, batch | Chatbots, interactive |

## Key Takeaway

**Same architecture, different presentation.**

Streaming changes HOW the response is displayed, not HOW the agent works.

You can convert any LangGraph agent to streaming by changing ONE node!
