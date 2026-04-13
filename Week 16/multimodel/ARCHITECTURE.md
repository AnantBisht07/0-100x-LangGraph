# Architecture - Conversational Planner Agent

## System Design Principles

### 1. **Modality Normalization**
All inputs (text, voice, image) → Text → Reasoning

### 2. **Separation of Concerns**
- Modality Layer: Handle input types
- Reasoning Layer: Planning logic
- Memory Layer: Context management

### 3. **Async-Ready**
Structure allows async processing without redesign

### 4. **Streaming-First**
User sees progress immediately

### 5. **Extensible**
Easy to add new modalities or reasoning modes

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1: INPUT LAYER                                        │
│ Handles different modality inputs                           │
│                                                             │
│ ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│ │   Text   │  │  Voice   │  │  Image   │                  │
│ │  Input   │  │  Input   │  │  Input   │                  │
│ └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 2: ROUTING LAYER                                      │
│ Determines processing path                                  │
│                                                             │
│        ┌────────────────────────────┐                      │
│        │     Input Router           │                      │
│        │ Examines: input_type       │                      │
│        │ Routes to: Processor node  │                      │
│        └────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 3: MODALITY PROCESSING LAYER                          │
│ Converts each modality to text                              │
│                                                             │
│ ┌──────────────┐  ┌─────────────┐  ┌──────────────┐      │
│ │Text Processor│  │Voice        │  │Image         │      │
│ │(Pass-through)│  │Processor    │  │Processor     │      │
│ │              │  │(STT)        │  │(Vision→Text) │      │
│ └──────────────┘  └─────────────┘  └──────────────┘      │
│                                                             │
│ Output: extracted_text (normalized)                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 4: REASONING LAYER                                    │
│ Core planning logic (modality-agnostic)                     │
│                                                             │
│        ┌────────────────────────────┐                      │
│        │   Planner Node             │                      │
│        │ - Reads: extracted_text    │                      │
│        │ - Uses: summary + messages │                      │
│        │ - Generates: Structured    │                      │
│        │   planning response        │                      │
│        │ - Streams: Token-by-token  │                      │
│        └────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 5: MEMORY MANAGEMENT LAYER                            │
│ Compresses context to prevent overflow                      │
│                                                             │
│        ┌────────────────────────────┐                      │
│        │  Memory Controller         │                      │
│        │ - Trigger: Every 5 turns   │                      │
│        │ - Action: Compress old     │                      │
│        │   messages → summary       │                      │
│        │ - Keep: Recent messages    │                      │
│        └────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

---

## State Design

### State Structure

```python
class MultimodalPlannerState(TypedDict):
    # Core conversation (modality-agnostic)
    messages: Annotated[list[BaseMessage], add_messages]
    summary: str
    total_turn_count: int

    # Modality-specific (input layer)
    input_type: Literal["text", "voice", "image"]
    raw_input_payload: str
    extracted_text: str
    metadata: Dict[str, Any]
```

### State Flow Example

**Initial State:**
```python
{
    "messages": [],
    "summary": "",
    "total_turn_count": 0,
    "input_type": "text",
    "raw_input_payload": "",
    "extracted_text": "",
    "metadata": {}
}
```

**After Voice Input:**
```python
{
    "messages": [HumanMessage("..."), AIMessage("...")],
    "summary": "",
    "total_turn_count": 1,

    # Modality fields updated
    "input_type": "voice",
    "raw_input_payload": "What's the budget?",
    "extracted_text": "[Transcribed from voice]: What's the budget?",
    "metadata": {
        "processor": "voice",
        "confidence": 0.95,
        "language": "en",
        "processed_at": "2024-..."
    }
}
```

**After 5 Turns (Compression):**
```python
{
    "messages": [Recent 4 messages only],
    "summary": "User is planning a mobile app launch with 3-month timeline...",
    "total_turn_count": 5,
    "input_type": "image",
    "raw_input_payload": "wireframe.jpg",
    "extracted_text": "[Image]: Dashboard wireframe with analytics...",
    "metadata": {...}
}
```

---

## Node Architecture

### 1. Input Router

**Type:** Conditional Edge Function
**Execution:** Synchronous

```python
def input_router(state) -> Literal["text_processor", "voice_processor", "image_processor"]:
    """
    Pure routing logic - no state changes
    """
    return f"{state['input_type']}_processor"
```

**Design Principles:**
- ✅ Stateless (pure function)
- ✅ Fast (no I/O)
- ✅ Extensible (easy to add modalities)

**Future Extensions:**
```python
elif input_type == "video":
    return "video_processor"
elif input_type == "pdf":
    return "pdf_processor"
elif input_type == "audio":
    return "audio_processor"
```

---

### 2. Modality Processors

**Type:** State Update Nodes
**Execution:** Sync (can be async)

#### A. Text Processor

```python
def text_processor(state):
    """
    Direct pass-through (text is already text)
    """
    return {
        "extracted_text": state["raw_input_payload"],
        "metadata": {"processor": "text"}
    }
```

**Complexity:** O(1)
**Latency:** <1ms

#### B. Voice Processor (Mock)

```python
def voice_processor(state):
    """
    Mock: Future Whisper API integration
    """
    # Future async call:
    # transcript = await whisper.transcribe(audio_file)

    return {
        "extracted_text": f"[Transcribed]: {state['raw_input_payload']}",
        "metadata": {
            "processor": "voice",
            "confidence": 0.95,
            "language": "en"
        }
    }
```

**Future Complexity:** O(audio_length)
**Future Latency:** ~1-3 seconds

**Real Implementation:**
```python
async def voice_processor_real(state):
    import openai

    audio_file = open(state["raw_input_payload"], "rb")

    transcript = await openai.Audio.atranscribe(
        "whisper-1",
        audio_file
    )

    return {
        "extracted_text": transcript.text,
        "metadata": {
            "processor": "voice",
            "confidence": transcript.confidence,
            "language": transcript.language
        }
    }
```

#### C. Image Processor (Mock)

```python
def image_processor(state):
    """
    Mock: Future GPT-4 Vision integration
    """
    # Future async call:
    # description = await gpt4_vision.describe(image_path)

    return {
        "extracted_text": f"[Image]: {state['raw_input_payload']}",
        "metadata": {
            "processor": "image",
            "detected_objects": []
        }
    }
```

**Future Complexity:** O(image_size)
**Future Latency:** ~2-5 seconds

**Real Implementation:**
```python
async def image_processor_real(state):
    import openai

    response = await openai.ChatCompletion.acreate(
        model="gpt-4-vision-preview",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image for planning context"},
                {"type": "image_url", "image_url": state["raw_input_payload"]}
            ]
        }]
    )

    return {
        "extracted_text": response.choices[0].message.content,
        "metadata": {
            "processor": "image",
            "model": "gpt-4-vision"
        }
    }
```

---

### 3. Planner Node (Core)

**Type:** LLM Reasoning Node
**Execution:** Sync with streaming

```python
def planner_node(state):
    """
    Core planning logic - modality agnostic
    """
    # Build context from:
    # 1. Summary (if exists)
    # 2. Recent messages
    # 3. Current extracted_text

    context = build_context(state)

    # Stream response
    full_response = ""
    for chunk in llm.stream(context):
        if chunk.content:
            print(chunk.content, end="", flush=True)
            full_response += chunk.content

    return {
        "messages": [AIMessage(content=full_response)],
        "total_turn_count": state["total_turn_count"] + 1
    }
```

**Characteristics:**
- ✅ Modality-agnostic (only sees extracted_text)
- ✅ Streaming-enabled (better UX)
- ✅ Memory-aware (uses summary)
- ✅ Turn tracking (increments counter)

**Why Streaming?**
```
Without streaming:
  User: Plan my week
  [Wait... 3 seconds...]
  Planner: [Full response appears]

With streaming:
  User: Plan my week
  Planner: Let me help you plan your week...
           ↑ Text appears as it's generated
```

---

### 4. Memory Controller

#### A. Compression Trigger

**Type:** Conditional Edge Function
**Execution:** Sync

```python
def should_compress(state) -> Literal["compress", "end"]:
    """
    Decide if compression needed
    """
    if state["total_turn_count"] % 5 == 0:
        return "compress"
    return "end"
```

**Trigger Logic:**
- Turn 1-4: No compression
- Turn 5: Compress ✓
- Turn 6-9: No compression
- Turn 10: Compress ✓

**Why Every 5 Turns?**
- Balance between memory and context
- Configurable threshold
- Prevents context explosion

#### B. Memory Compressor

**Type:** State Update Node
**Execution:** Sync (LLM call)

```python
def memory_compressor(state):
    """
    Compress older messages into summary
    """
    older_messages = state["messages"][:-4]

    # Build summarization prompt
    prompt = f"""Previous summary: {state['summary']}
New messages: {older_messages}

Merge into concise summary (3-4 sentences):"""

    summary = llm.invoke([HumanMessage(content=prompt)])

    return {
        "messages": state["messages"][-4:],  # Keep recent only
        "summary": summary.content
    }
```

**Before Compression:**
```python
messages = [msg1, msg2, msg3, msg4, msg5, msg6, msg7, msg8]  # 8 messages
summary = ""
```

**After Compression:**
```python
messages = [msg5, msg6, msg7, msg8]  # 4 recent messages
summary = "User planning app launch, discussed budget, timeline, features..."
```

---

## Graph Topology

```python
graph = StateGraph(MultimodalPlannerState)

# Add nodes
graph.add_node("text_processor", text_processor)
graph.add_node("voice_processor", voice_processor)
graph.add_node("image_processor", image_processor)
graph.add_node("planner", planner_node)
graph.add_node("compress", memory_compressor)

# Entry with routing
graph.add_conditional_edges(START, input_router, {
    "text_processor": "text_processor",
    "voice_processor": "voice_processor",
    "image_processor": "image_processor"
})

# All processors → planner
graph.add_edge("text_processor", "planner")
graph.add_edge("voice_processor", "planner")
graph.add_edge("image_processor", "planner")

# Planner → memory check
graph.add_conditional_edges("planner", should_compress, {
    "compress": "compress",
    "end": END
})

# Compressor → end
graph.add_edge("compress", END)
```

**Visual:**
```
                START
                  ↓
         [Input Router] ─────┐
           ↓    ↓    ↓        │ (Conditional)
       Text Voice Image       │
         ↓    ↓    ↓          │
         └────┼────┘          │
              ↓               │
          [Planner]           │
              ↓               │
      [Memory Check] ─────────┘ (Conditional)
         ↓        ↓
     Compress    END
         ↓
        END
```

---

## Async Architecture

### Current: Sync Implementation

```python
def voice_processor(state):
    # Blocking mock
    transcript = f"[Transcribed]: {state['raw_input_payload']}"
    return {"extracted_text": transcript}
```

### Future: Async Implementation

```python
async def voice_processor_async(state):
    # Non-blocking real implementation
    transcript = await whisper_api.transcribe(state["raw_input_payload"])
    return {"extracted_text": transcript.text}

async def image_processor_async(state):
    # Non-blocking real implementation
    caption = await vision_api.describe(state["raw_input_payload"])
    return {"extracted_text": caption}

# Both can run concurrently if needed
async def process_multimodal_batch(inputs):
    tasks = [
        voice_processor_async(inputs[0]),
        image_processor_async(inputs[1])
    ]
    results = await asyncio.gather(*tasks)
    return results
```

**Benefits:**
- Voice processing (3s) + Image processing (3s) = 3s total (not 6s)
- Non-blocking I/O
- Better resource utilization

---

## Performance Characteristics

### Latency Breakdown (Future with Real APIs)

```
┌──────────────────────────────────────────────────────┐
│ Turn Latency Analysis                                │
├──────────────────────────────────────────────────────┤
│                                                      │
│ Text Input:                                          │
│   Router:         <1ms                               │
│   Processor:      <1ms                               │
│   Planner:        2-4s (LLM streaming)               │
│   Total:          ~2-4s                              │
│                                                      │
│ Voice Input:                                         │
│   Router:         <1ms                               │
│   Processor:      1-3s (Whisper STT)                 │
│   Planner:        2-4s (LLM streaming)               │
│   Total:          ~3-7s                              │
│                                                      │
│ Image Input:                                         │
│   Router:         <1ms                               │
│   Processor:      2-5s (Vision API)                  │
│   Planner:        2-4s (LLM streaming)               │
│   Total:          ~4-9s                              │
│                                                      │
│ With Compression (Every 5th turn):                   │
│   +1-2s for summarization                            │
└──────────────────────────────────────────────────────┘
```

### Memory Usage

```
Without Compression:
  Turn 10:  ~20 messages × 500 tokens = 10,000 tokens
  Turn 20:  ~40 messages × 500 tokens = 20,000 tokens
  Turn 50:  ~100 messages × 500 tokens = 50,000 tokens ← Too big!

With Compression (Every 5 turns):
  Turn 10:  Summary (200 tokens) + 4 recent messages (2,000 tokens) = ~2,200 tokens
  Turn 20:  Summary (400 tokens) + 4 recent messages (2,000 tokens) = ~2,400 tokens
  Turn 50:  Summary (800 tokens) + 4 recent messages (2,000 tokens) = ~2,800 tokens ← Bounded!
```

---

## Design Patterns

### Pattern 1: Modality Normalization

```python
# All modalities converge to text
def normalize_input(input_type, raw_payload):
    if input_type == "text":
        return raw_payload
    elif input_type == "voice":
        return transcribe_audio(raw_payload)
    elif input_type == "image":
        return caption_image(raw_payload)

# Core logic only sees text
def reason(extracted_text):
    # Doesn't care about original modality!
    return generate_plan(extracted_text)
```

### Pattern 2: Streaming Response Assembly

```python
full_response = ""
for chunk in llm.stream(context):
    # Display immediately
    print(chunk.content, end="", flush=True)

    # Accumulate for state
    full_response += chunk.content

# Save complete response
return {"messages": [AIMessage(content=full_response)]}
```

### Pattern 3: Conditional Routing

```python
# Route based on state
def router(state):
    if condition(state):
        return "path_a"
    else:
        return "path_b"

# Use in graph
graph.add_conditional_edges(node, router, {
    "path_a": "node_a",
    "path_b": "node_b"
})
```

---

## Key Architectural Decisions

### Decision 1: Why Normalize to Text?

**Alternative:** Process each modality differently in planner

**Chosen:** Normalize all to text before planner

**Rationale:**
- ✅ Planner logic stays clean (modality-agnostic)
- ✅ Easy to add new modalities (just add processor)
- ✅ LLMs work best with text anyway
- ✅ Simpler testing (mock text inputs)

### Decision 2: Why Streaming?

**Alternative:** Batch processing (invoke)

**Chosen:** Streaming (stream)

**Rationale:**
- ✅ Better perceived performance
- ✅ Immediate user feedback
- ✅ Can interrupt if needed
- ✅ More engaging UX
- ❌ Slight complexity increase (acceptable)

### Decision 3: Why Compress Every 5 Turns?

**Alternative:** Compress every turn or never compress

**Chosen:** Compress every 5 turns

**Rationale:**
- ✅ Balance between memory and context fidelity
- ✅ Not too frequent (wasteful)
- ✅ Not too rare (context explosion)
- ✅ Configurable (can adjust threshold)

### Decision 4: Why Mock Processors?

**Alternative:** Implement real APIs immediately

**Chosen:** Mock first, integrate later

**Rationale:**
- ✅ Demonstrates architecture without API dependencies
- ✅ Faster development/testing
- ✅ Clear integration points for future
- ✅ Educational (shows structure)

---

## Summary

### Core Principles

1. **Modality Normalization** - All inputs → text
2. **Separation of Layers** - Modality, Routing, Reasoning, Memory
3. **Streaming-First** - Better UX
4. **Async-Ready** - Extensible to async
5. **Memory-Aware** - Prevents context overflow

### Extensibility Points

- Add new modalities: Create processor node
- Change planning style: Modify planner node
- Adjust memory: Change compression logic
- Add async: Convert nodes to async functions

### Key Insight

**Clean architecture enables multimodal systems without complexity explosion!**
