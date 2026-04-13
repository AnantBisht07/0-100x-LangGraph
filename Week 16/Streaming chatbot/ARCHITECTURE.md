# Streaming Memory-Controlled Agent - Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│             Streaming Memory-Controlled Agent               │
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Chat Node  │───▶│   Router     │───▶│ Summarizer   │  │
│  │ (STREAMING) │    │ (Unchanged)  │    │ (Non-stream) │  │
│  └─────────────┘    └──────────────┘    └──────────────┘  │
│         ▲                                        │         │
│         │                                        │         │
│         └────────────────────────────────────────┘         │
│                                                             │
│  State: {messages, summary, turn_count, window_count}      │
└─────────────────────────────────────────────────────────────┘
```

## Core Concept

**Streaming is a presentation layer change, not an architectural change.**

### What Stays the Same
- ✓ State structure
- ✓ Graph topology
- ✓ Compression logic
- ✓ Memory management
- ✓ Node flow

### What Changes
- ✗ Output display method
- ✗ LLM invocation pattern (streaming vs batch)

## Architectural Layers

```
┌───────────────────────────────────────────────────────────┐
│ Layer 4: Presentation (CHANGED)                          │
│ ┌───────────────────────────────────────────────────────┐ │
│ │ Token-by-token display with flush                     │ │
│ │ print(chunk.content, end="", flush=True)              │ │
│ └───────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────┘
                          ↓
┌───────────────────────────────────────────────────────────┐
│ Layer 3: LLM Communication (CHANGED)                      │
│ ┌───────────────────────────────────────────────────────┐ │
│ │ for chunk in llm.stream(context):                     │ │
│ │     process_chunk(chunk)                              │ │
│ └───────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────┘
                          ↓
┌───────────────────────────────────────────────────────────┐
│ Layer 2: Business Logic (UNCHANGED)                       │
│ ┌───────────────────────────────────────────────────────┐ │
│ │ - Compression triggers at window_count >= 3           │ │
│ │ - Summary generation and merging                      │ │
│ │ - Message trimming to recent window                   │ │
│ └───────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────┘
                          ↓
┌───────────────────────────────────────────────────────────┐
│ Layer 1: State Management (UNCHANGED)                     │
│ ┌───────────────────────────────────────────────────────┐ │
│ │ ConversationState with reducers                       │ │
│ │ {messages, summary, turn_count, window_count}         │ │
│ └───────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────┘
```

## Node-by-Node Analysis

### 1. Chat Node (STREAMING)

#### Original Version
```python
def chat_node(state):
    context = build_context(state)
    response = llm.invoke(context)  # ← Batch call
    return {
        "messages": [response],
        "turn_count": state["turn_count"] + 1,
        "window_count": state["window_count"] + 1
    }
```

#### Streaming Version
```python
def chat_node_streaming(state):
    context = build_context(state)  # ← Same

    # NEW: Stream tokens
    full_response = ""
    for chunk in llm.stream(context):
        print(chunk.content, end="", flush=True)
        full_response += chunk.content

    # Create message with complete response
    response = AIMessage(content=full_response)

    # Same state updates
    return {
        "messages": [response],
        "turn_count": state["turn_count"] + 1,
        "window_count": state["window_count"] + 1
    }
```

**Key Insight**: State updates identical, only display method changed.

### 2. Router (UNCHANGED)

```python
def should_compress(state):
    if state["window_count"] >= 3:
        return "summarizer"
    return "end"
```

**No changes needed** - streaming doesn't affect routing logic.

### 3. Summarizer (NON-STREAMING)

```python
def summarizer_node(state):
    # Build prompt...
    summary = llm.invoke([HumanMessage(content=prompt)])  # ← Still invoke!
    # ...
```

**Why not stream?**
- Summarizer is background task
- User doesn't see it happening
- Streaming adds no value
- invoke() is simpler and faster

## Streaming Implementation Details

### Token Flow

```
LLM Server                Python Process              Terminal
─────────────────────────────────────────────────────────────

1. Generate token "The"
                    ─────▶
                          2. Receive chunk
                          3. Print "The"
                                              ─────▶ Display "The"

4. Generate token "quick"
                    ─────▶
                          5. Receive chunk
                          6. Print "quick"
                                              ─────▶ Display "quick"

7. Generate token "brown"
                    ─────▶
                          8. Receive chunk
                          9. Print "brown"
                                              ─────▶ Display "brown"

... continues until complete ...
```

### Buffering Control

#### Without flush=True
```python
print(chunk.content, end="")  # No flush
```
**Result**: OS buffers output, displays in batches
```
[Wait...]
The quick brown fox jumps  [Batch 1]
[Wait...]
over the lazy dog          [Batch 2]
```

#### With flush=True
```python
print(chunk.content, end="", flush=True)  # Force flush
```
**Result**: Immediate display
```
The quick brown fox jumps over the lazy dog
↑   ↑     ↑     ↑   ↑     ↑    ↑   ↑    ↑
Each word appears immediately
```

### Response Assembly

```python
full_response = ""  # ← Accumulator

for chunk in llm.stream(context):
    # Display token
    print(chunk.content, end="", flush=True)

    # Build complete response
    full_response += chunk.content  # ← IMPORTANT!

# Create AIMessage with full text
response = AIMessage(content=full_response)
```

**Why accumulate?**
- State needs complete response
- Can't store partial chunks
- AIMessage expects full content

## Memory Management Interaction

### Streaming + Compression Flow

```
Turn 1:
  User: "Tokyo"
  Chat Node: Stream response token-by-token
  State: messages=[Human, AI], window_count=1

Turn 2:
  User: "Kyoto"
  Chat Node: Stream response token-by-token
  State: messages=[H, A, H, A], window_count=2

Turn 3:
  User: "Osaka"
  Chat Node: Stream response token-by-token
  Router: window_count=3 → COMPRESS!
  Summarizer: Non-streaming summary generation
  State: messages=[H, A, H, A], summary="...", window_count=0

Turn 4:
  User: "Nara"
  Chat Node: Context = [Summary + Recent messages]
              Stream response (knows about Tokyo/Kyoto via summary)
  State: messages=[H, A, H, A, H, A], summary="...", window_count=1
```

**Key Point**: Compression unaffected by streaming!

## Performance Characteristics

### Time to First Token (TTFT)

```
Non-Streaming:
  Request → [Wait for full response] → Display all
  TTFT: ~2-5 seconds

Streaming:
  Request → Display first token → Display rest
  TTFT: ~200-500ms
```

### Total Time

```
Both versions: Same total time (~2-5 seconds)
Streaming advantage: User sees progress immediately
```

### Network Utilization

```
Non-Streaming:
  ▓▓▓▓▓▓▓▓░░░░░░░░  (Burst then idle)

Streaming:
  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  (Steady stream)
```

## State Consistency

### Important: Full Response Required

```python
# ✗ WRONG: Store partial chunks
for chunk in llm.stream(context):
    state["messages"].append(AIMessage(content=chunk.content))
# Result: Multiple partial messages!

# ✓ CORRECT: Accumulate then store
full_response = ""
for chunk in llm.stream(context):
    full_response += chunk.content

state["messages"].append(AIMessage(content=full_response))
# Result: One complete message
```

### Why?

State must represent **complete conversation turns**, not partial chunks.

## Graph Topology (UNCHANGED)

```
      START
        ↓
    ┌────────┐
    │  Chat  │ ← Only this node changed internally
    └────────┘
        ↓
    ┌────────┐
    │ Router │ ← Unchanged
    └────────┘
      ↙    ↘
Summarizer  END
    ↓
   END
```

Same edges, same routing, same flow.

## Technical Trade-offs

### Advantages
- ✅ Better perceived performance
- ✅ Immediate user feedback
- ✅ Can interrupt if needed
- ✅ More engaging UX
- ✅ Minimal code changes

### Disadvantages
- ❌ Slightly more complex (accumulation logic)
- ❌ Harder to debug (output interspersed)
- ❌ Terminal-dependent (flush behavior)
- ❌ Can't batch-process easily

## Streaming Patterns

### Pattern 1: Simple Display (Our Implementation)
```python
for chunk in llm.stream(context):
    print(chunk.content, end="", flush=True)
```
**Use**: CLI applications

### Pattern 2: Callback-based
```python
def on_token(token):
    update_ui(token)

for chunk in llm.stream(context):
    on_token(chunk.content)
```
**Use**: GUI applications

### Pattern 3: Generator
```python
def stream_response(context):
    for chunk in llm.stream(context):
        yield chunk.content

for token in stream_response(context):
    process(token)
```
**Use**: Web APIs (Server-Sent Events)

### Pattern 4: Async Streaming
```python
async def stream_response(context):
    async for chunk in llm.astream(context):
        await websocket.send(chunk.content)
```
**Use**: WebSocket applications

## Configuration Options

### LLM Streaming Settings

```python
llm = ChatOpenAI(
    model="gpt-4o-mini",
    streaming=True,         # Enable streaming
    temperature=0,          # Same as before
    # stream_usage=True,   # Optional: Include token usage in stream
    # timeout=30,          # Optional: Timeout for stream
)
```

### When to Enable Streaming

```python
# Enable globally (our approach)
llm = ChatOpenAI(streaming=True)

# Or per-call
response = llm.stream(context)  # Streams even if streaming=False
```

## Error Handling

### Streaming-Specific Errors

```python
try:
    full_response = ""
    for chunk in llm.stream(context):
        print(chunk.content, end="", flush=True)
        full_response += chunk.content
except Exception as e:
    print(f"\nStream interrupted: {e}")
    # Still create message with partial response
    response = AIMessage(content=full_response or "[Error]")
```

### Network Interruption
```
Streaming: The quick brown fox ju[CONNECTION LOST]
          ↑
          Partial response visible, user knows what happened

Non-streaming: [CONNECTION LOST]
               ↑
               No output, user confused
```

## Summary

### Core Principle
**Streaming is a runtime behavior, not an architectural redesign.**

### What This Means
1. **Same State**: No new fields needed
2. **Same Graph**: No new nodes/edges needed
3. **Same Logic**: Compression unchanged
4. **Different Display**: Tokens appear incrementally

### Implementation Checklist
- [x] Enable `streaming=True` in LLM config
- [x] Replace `llm.invoke()` with `llm.stream()` in chat node
- [x] Accumulate chunks into full response
- [x] Use `flush=True` for immediate display
- [x] Keep other nodes unchanged
- [x] Maintain state consistency

### Key Insight for Learners
You can add streaming to ANY LangGraph agent by changing ONE node's display logic. The architecture remains intact.

---

**Bottom Line**: Streaming changes the user experience, not the system architecture.
