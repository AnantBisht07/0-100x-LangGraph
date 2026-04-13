# Memory-Controlled Conversational Agent - Student Guide

## What is This?

A chatbot that **automatically compresses old conversations** to prevent memory overflow and keep responses fast.

## The Problem

Normal chatbots keep ALL messages in memory:
- Turn 1: 2 messages
- Turn 10: 20 messages
- Turn 100: 200 messages ❌ Too slow! Too expensive!

## Our Solution

After every 3 turns, compress old messages into a summary:
- Turn 1-3: Keep all messages
- Turn 3: **Compress** old → Create summary
- Turn 4-6: Keep recent + summary
- Turn 6: **Compress** again

## How to Run

```bash
python simple_memory_agent.py
```

---

## Example Output Explained

### Turn 1: Normal Chat
```
You: plan the trip for dubai
AI: [Dubai trip planning response...]
[Turn 1 | Window: 1 | Summary: 0 chars]
```

**What's happening:**
- First conversation turn
- No compression yet
- Window counter = 1 (counting towards threshold)

---

### Turn 2: Normal Chat
```
You: plan 2 day trip for india
AI: [Delhi trip planning response...]
[Turn 2 | Window: 2 | Summary: 0 chars]
```

**What's happening:**
- Second conversation turn
- Still no compression
- Window counter = 2 (almost at threshold)

---

### Turn 3: COMPRESSION TRIGGERED! 🔥
```
You: plan 2 day trip for mumbai, india

[COMPRESSED] Older messages compressed into summary

AI: [Mumbai trip planning response...]
[Turn 3 | Window: 0 | Summary: 484 chars]
```

**What's happening:**
- Window counter reached 3 (threshold!)
- Agent compressed Dubai + Delhi conversations
- Created summary (484 characters)
- Kept only Mumbai conversation in full
- Window counter **reset to 0**

---

### Turn 4: Chat Continues
```
You: plan 2 day trip for goa
AI: [Goa trip planning response...]
[Turn 4 | Window: 1 | Summary: 484 chars]
```

**What's happening:**
- Window counter starts counting again (1)
- Summary still exists (484 chars)
- AI remembers Dubai + Delhi via summary
- AI sees Mumbai + Goa in full detail

---

## Understanding the Metrics

### [Turn X | Window: Y | Summary: Z chars]

- **Turn**: Total conversation turns (never resets)
- **Window**: Turns since last compression (resets to 0)
- **Summary**: Size of compressed old context

### Examples

```
[Turn 1 | Window: 1 | Summary: 0 chars]
   ↑        ↑           ↑
 Total   Counting   No summary yet

[Turn 3 | Window: 0 | Summary: 484 chars]
   ↑        ↑           ↑
 Total   Just reset  Summary created!

[Turn 6 | Window: 3 | Summary: 720 chars]
   ↑        ↑           ↑
 Total   Threshold   Summary updated
```

---

## Key Concepts

### 1. Window Counter
Tracks how many turns since the last compression.
- Starts at 0
- Increments each turn
- Resets to 0 after compression

**Why?** Prevents compressing every single turn (wasteful!)

### 2. Threshold (Default: 3)
The trigger point for compression.
- When `window_count >= 3` → Compress!
- Can be changed (e.g., 5, 10, 20)

### 3. Summary
Short text that stores compressed old conversations.
- Old conversations → Summarized
- Recent conversations → Kept in full

### 4. Recent Window (Default: 4 messages)
How many recent messages to keep in full detail.
- Last 4 messages stay uncompressed
- Older messages get summarized

---

## What AI "Sees" at Each Turn

### Turn 1
```
Input to AI:
- "plan the trip for dubai"
```

### Turn 2
```
Input to AI:
- "plan the trip for dubai"
- [Dubai response]
- "plan 2 day trip for india"
```

### Turn 3 (After Compression)
```
Input to AI:
- Summary: "User asked about Dubai trip... Then asked about Delhi..."
- "plan 2 day trip for mumbai"
```

### Turn 4
```
Input to AI:
- Summary: "User asked about Dubai, Delhi trips..."
- "plan 2 day trip for mumbai"
- [Mumbai response]
- "plan 2 day trip for goa"
```

---

## Benefits

✅ **Controlled Memory**: Never grows too large
✅ **Fast Responses**: AI reads less data
✅ **No Information Loss**: Summary preserves key facts
✅ **Cost Efficient**: Fewer tokens = cheaper
✅ **Scalable**: Can chat for 1000 turns!

---

## Visualizing Compression

### Before Compression (Turn 3)
```
Messages: [Dubai Q&A, Delhi Q&A, Mumbai Q&A]  ← 6 messages
Summary: ""                                   ← Empty
Window: 3                                     ← Hit threshold!
```

### After Compression (Turn 3)
```
Messages: [Mumbai Q&A]                        ← Only 2 messages!
Summary: "User discussed Dubai, Delhi..."     ← Created!
Window: 0                                     ← Reset!
```

---

## Try It Yourself!

1. Run the agent
2. Ask 3 questions
3. Watch for `[COMPRESSED]` message
4. See window counter reset to 0
5. Notice summary appears

---

## Quiz Questions

1. What happens when window_count reaches 3?
2. Why do we reset the window counter?
3. What's the difference between Turn and Window?
4. Where do old conversations go after compression?
5. How many recent messages are kept in full?

**Answers:**
1. Compression triggers, old messages summarized
2. To prevent compressing on every turn
3. Turn = total count, Window = since last compression
4. They get compressed into the summary
5. Last 4 messages (configurable)

---

## Next Steps

- Modify threshold to 5 or 10
- Change recent window size
- Add more complex routing logic
- Integrate with a database for persistence

---

**Remember:** This agent solves the fundamental problem of memory management in conversational AI!
