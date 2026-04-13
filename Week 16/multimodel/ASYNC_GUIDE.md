# Async Architecture Guide

## Why Async Matters

### The Problem: Blocking Operations

**Current (Sync) Implementation:**
```python
def voice_processor(state):
    # This BLOCKS for 2-3 | 30-40 seconds
    transcript = whisper_api.transcribe(audio_file)
    return {"extracted_text": transcript}

def image_processor(state):
    # This BLOCKS for 2-5 seconds
    description = vision_api.describe(image)
    return {"extracted_text": description}
```

**Problem:** If processing voice takes 3s and image takes 4s = **7 seconds total**

**With Async:** Both run concurrently = **4 seconds total** (max of the two)

---

## Async Basics

### Sync vs Async

**Synchronous (Blocking):**
```python
def slow_task():
    time.sleep(3)  # Blocks for 3 seconds
    return "done"

result = slow_task()  # Wait 3 seconds
print(result)
```

**Asynchronous (Non-Blocking):**
```python
async def slow_task():
    await asyncio.sleep(3)  # Doesn't block
    return "done"

result = await slow_task()  # Wait, but can do other things
print(result)
```

### Key Concepts

**`async def`** - Defines async function
**`await`** - Wait for async operation
**`asyncio.gather()`** - Run multiple async tasks concurrently

---

## Converting Nodes to Async

### Current: Sync Voice Processor

```python
def voice_processor(state):
    print("[VOICE] Processing...")

    # Mock: Instant
    transcript = f"[Transcribed]: {state['raw_input_payload']}"

    return {"extracted_text": transcript}
```

### Future: Async Voice Processor

```python
async def voice_processor_async(state):
    print("[VOICE] Processing...")

    import openai

    # Non-blocking API call
    audio_file = open(state["raw_input_payload"], "rb")

    transcript = await openai.Audio.atranscribe(
        model="whisper-1",
        file=audio_file
    )

    return {"extracted_text": transcript.text}
```

**Changes:**
1. `def` → `async def`
2. Blocking call → `await` async call

---

## Current: Sync Image Processor

```python
def image_processor(state):
    print("[IMAGE] Processing...")

    # Mock: Instant
    caption = f"[Image]: {state['raw_input_payload']}"

    return {"extracted_text": caption}
```

### Future: Async Image Processor

```python
async def image_processor_async(state):
    print("[IMAGE] Processing...")

    import openai

    # Non-blocking API call
    response = await openai.ChatCompletion.acreate(
        model="gpt-4-vision-preview",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image"},
                {"type": "image_url", "image_url": state["raw_input_payload"]}
            ]
        }]
    )

    return {"extracted_text": response.choices[0].message.content}
```

---

## Planner Node (Already Async-Ready)

### Current: Sync with Streaming

```python
def planner_node(state):
    context = build_context(state)

    # Streaming (already non-blocking in spirit)
    full_response = ""
    for chunk in llm.stream(context):
        print(chunk.content, end="", flush=True)
        full_response += chunk.content

    return {"messages": [AIMessage(content=full_response)]}
```

### Future: Async with Streaming

```python
async def planner_node_async(state):
    context = build_context(state)

    # Async streaming
    full_response = ""
    async for chunk in llm.astream(context):
        print(chunk.content, end="", flush=True)
        full_response += chunk.content

    return {"messages": [AIMessage(content=full_response)]}
```

**Changes:**
1. `def` → `async def`
2. `for chunk in llm.stream()` → `async for chunk in llm.astream()`

---

## Running Async Graph

### LangGraph Async Support

```python
# Create graph (same as before)
graph = StateGraph(MultimodalPlannerState)
graph.add_node("voice", voice_processor_async)  # Async node
graph.add_node("planner", planner_node_async)   # Async node
# ... add edges ...
agent = graph.compile()

# Invoke asynchronously
result = await agent.ainvoke(state)
```

### Async Main Loop

```python
async def main_async():
    agent = create_planner_graph()

    state = {
        "messages": [],
        "summary": "",
        "total_turn_count": 0,
        # ...
    }

    while True:
        user_input = input("You: ")

        if user_input.lower() == 'quit':
            break

        # Update state
        state["input_type"] = "text"
        state["raw_input_payload"] = user_input

        # Async invoke
        result = await agent.ainvoke(state)

        state = result

if __name__ == "__main__":
    asyncio.run(main_async())
```

---

## Concurrent Processing

### Scenario: Process Voice + Image Together

**Sync (Sequential):**
```python
# Voice takes 3s
voice_result = voice_processor(voice_state)

# Image takes 4s
image_result = image_processor(image_state)

# Total: 3s + 4s = 7 seconds
```

**Async (Concurrent):**
```python
# Both run simultaneously
voice_task = voice_processor_async(voice_state)
image_task = image_processor_async(image_state)

voice_result, image_result = await asyncio.gather(voice_task, image_task)

# Total: max(3s, 4s) = 4 seconds (43% faster!)
```

### Practical Example

```python
async def process_multimodal_inputs(inputs):
    """
    Process multiple inputs concurrently

    inputs = [
        {"type": "voice", "payload": "audio.mp3"},
        {"type": "image", "payload": "photo.jpg"}
    ]
    """
    tasks = []

    for input in inputs:
        if input["type"] == "voice":
            tasks.append(voice_processor_async(input))
        elif input["type"] == "image":
            tasks.append(image_processor_async(input))

    # Run all concurrently
    results = await asyncio.gather(*tasks)

    return results
```

---

## Error Handling in Async

### Try-Except with Async

```python
async def voice_processor_async(state):
    try:
        transcript = await openai.Audio.atranscribe(...)
        return {"extracted_text": transcript.text}

    except openai.error.APIError as e:
        print(f"[ERROR] API error: {e}")
        return {"extracted_text": "[Transcription failed]"}

    except asyncio.TimeoutError:
        print("[ERROR] Timeout")
        return {"extracted_text": "[Timeout - please retry]"}
```

### Timeouts

```python
async def voice_processor_with_timeout(state):
    try:
        # Timeout after 5 seconds
        result = await asyncio.wait_for(
            openai.Audio.atranscribe(...),
            timeout=5.0
        )
        return {"extracted_text": result.text}

    except asyncio.TimeoutError:
        return {"extracted_text": "[Processing timeout]"}
```

### Retries

```python
async def voice_processor_with_retry(state):
    max_retries = 3

    for attempt in range(max_retries):
        try:
            transcript = await openai.Audio.atranscribe(...)
            return {"extracted_text": transcript.text}

        except openai.error.RateLimitError:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                raise

    return {"extracted_text": "[Failed after retries]"}
```

---

## Async Best Practices

### 1. Use `async` for I/O-Bound Operations

**Good:**
```python
async def fetch_data():
    data = await api_call()  # Network I/O
    return data
```

**Bad (Don't use async for CPU-bound):**
```python
async def calculate():
    result = expensive_calculation()  # CPU-bound, not I/O
    return result
```

### 2. Avoid Blocking Calls in Async Functions

**Wrong:**
```python
async def bad_async():
    time.sleep(5)  # This BLOCKS! (Defeats purpose)
    return "done"
```

**Correct:**
```python
async def good_async():
    await asyncio.sleep(5)  # This is non-blocking
    return "done"
```

### 3. Use `asyncio.gather()` for Concurrency

**Sequential (Slow):**
```python
result1 = await task1()
result2 = await task2()
result3 = await task3()
# Total time: t1 + t2 + t3
```

**Concurrent (Fast):**
```python
results = await asyncio.gather(task1(), task2(), task3())
# Total time: max(t1, t2, t3)
```

### 4. Handle Exceptions in Gather

```python
results = await asyncio.gather(
    task1(),
    task2(),
    task3(),
    return_exceptions=True  # Don't fail entire batch if one fails
)

for i, result in enumerate(results):
    if isinstance(result, Exception):
        print(f"Task {i} failed: {result}")
    else:
        print(f"Task {i} succeeded: {result}")
```

---

## Performance Comparison

### Latency Analysis

**Scenario:** Process voice + image + plan

**Sync Implementation:**
```
Voice processing:   3s
Image processing:   4s
Planner:            2s
Total:              9s
```

**Async Implementation (Voice + Image concurrent):**
```
Voice + Image concurrently:  max(3s, 4s) = 4s
Planner:                     2s
Total:                       6s (33% faster!)
```

**Full Async (All concurrent where possible):**
```
Voice + Image + Planner (if independent):  max(3s, 4s, 2s) = 4s
Total:                                     4s (56% faster!)
```

---

## Migration Path

### Step 1: Identify I/O-Bound Nodes

```python
# I/O-Bound (Good for async):
- voice_processor  (Network API call)
- image_processor  (Network API call)
- planner_node     (LLM streaming)

# Not I/O-Bound (Keep sync):
- input_router     (Pure logic)
- text_processor   (String operation)
```

### Step 2: Convert One Node

```python
# Before
def voice_processor(state):
    result = api_call(state["raw_input_payload"])
    return {"extracted_text": result}

# After
async def voice_processor(state):
    result = await api_call_async(state["raw_input_payload"])
    return {"extracted_text": result}
```

### Step 3: Update Graph

```python
# Graph construction stays same!
graph.add_node("voice", voice_processor)  # Works with async functions
```

### Step 4: Use Async Invocation

```python
# Before
result = agent.invoke(state)

# After
result = await agent.ainvoke(state)
```

### Step 5: Update Main

```python
# Before
if __name__ == "__main__":
    main()

# After
if __name__ == "__main__":
    asyncio.run(main_async())
```

---

## Common Patterns

### Pattern 1: Async Context Manager

```python
async def process_with_resource(state):
    async with aiofiles.open(state["raw_input_payload"], 'rb') as f:
        content = await f.read()
        result = await process_content(content)
    return {"extracted_text": result}
```

### Pattern 2: Async Generator (Streaming)

```python
async def stream_response(context):
    async for chunk in llm.astream(context):
        yield chunk.content
```

### Pattern 3: Background Tasks

```python
async def main():
    # Start background task
    task = asyncio.create_task(background_sync())

    # Continue with main work
    await main_work()

    # Wait for background task
    await task
```

### Pattern 4: Rate Limiting

```python
from asyncio import Semaphore

semaphore = Semaphore(5)  # Max 5 concurrent

async def rate_limited_process(state):
    async with semaphore:
        result = await api_call(state)
    return result
```

---

## Debugging Async Code

### Print Statement Timing

```python
async def debug_async():
    print("Start")
    await asyncio.sleep(1)
    print("After 1s")
    await asyncio.sleep(1)
    print("After 2s")
```

### Track Running Tasks

```python
import asyncio

async def main():
    tasks = asyncio.all_tasks()
    print(f"Currently running: {len(tasks)} tasks")
    for task in tasks:
        print(f"  - {task.get_name()}")
```

### Async Profiling

```python
import time

async def timed_async(name, func):
    start = time.time()
    result = await func()
    elapsed = time.time() - start
    print(f"{name} took {elapsed:.2f}s")
    return result
```

---

## Summary

### When to Use Async

✅ **Use async for:**
- API calls (Whisper, GPT-4 Vision, etc.)
- File I/O (reading large files)
- Database queries
- Network requests
- Concurrent operations

❌ **Don't use async for:**
- Pure computation (calculations)
- Simple string operations
- Routing logic
- Memory operations

### Key Benefits

1. **Concurrency** - Multiple operations simultaneously
2. **Responsiveness** - Don't block on I/O
3. **Efficiency** - Better resource utilization
4. **Scalability** - Handle more concurrent users

### Implementation Checklist

- [ ] Identify I/O-bound nodes
- [ ] Convert to `async def`
- [ ] Replace blocking calls with `await`
- [ ] Use `asyncio.gather()` for concurrency
- [ ] Update invocation to `ainvoke()`
- [ ] Wrap main in `asyncio.run()`

**Bottom Line:** Async enables concurrent processing for faster, more responsive multimodal systems!
