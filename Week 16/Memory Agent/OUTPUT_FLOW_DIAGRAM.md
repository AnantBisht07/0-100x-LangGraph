# Memory-Controlled Agent - Output Flow Diagram

## Complete Conversation Flow with Actual Outputs

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         START OF CONVERSATION                               │
└─────────────────────────────────────────────────────────────────────────────┘

Initial State:
┌─────────────────────────────────────────┐
│ messages: []                            │
│ summary: ""                             │
│ turn_count: 0                           │
│ window_count: 0                         │
└─────────────────────────────────────────┘


════════════════════════════════════════════════════════════════════════════════
                                  TURN 1
════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│ USER INPUT                                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
You: plan the trip for dubai

         ↓

┌─────────────────────────────────────────────────────────────────────────────┐
│ STATE BEFORE GRAPH                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
messages: [HumanMessage("plan the trip for dubai")]
summary: ""
turn_count: 0
window_count: 0

         ↓

┌─────────────────────────────────────────────────────────────────────────────┐
│ GRAPH EXECUTION                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

    [START]
       ↓
    ┌──────────────┐
    │  CHAT NODE   │
    └──────────────┘

    What happens inside chat_node:
    --------------------------------
    1. Build context:
       context = []

    2. Check for summary:
       if state["summary"]:  → FALSE (empty)
       → Skip summary

    3. Add recent messages:
       context.extend(state["messages"][-4:])
       → context = [HumanMessage("plan the trip for dubai")]

    4. Call LLM:
       response = llm.invoke(context)
       → AIMessage("Planning a trip to Dubai...")

    5. Return updates:
       {
         "messages": [AIMessage("Planning a trip...")],
         "turn_count": 1,
         "window_count": 1
       }

       ↓

    ┌──────────────────┐
    │ ROUTER: compress?│
    │ window_count = 1 │
    │ threshold = 3    │
    │ 1 >= 3? NO       │
    └──────────────────┘

       ↓

    [END]

         ↓

┌─────────────────────────────────────────────────────────────────────────────┐
│ STATE AFTER GRAPH                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
messages: [
  HumanMessage("plan the trip for dubai"),
  AIMessage("Planning a trip to Dubai can be exciting! Here's a guide...")
]
summary: ""
turn_count: 1
window_count: 1

         ↓

┌─────────────────────────────────────────────────────────────────────────────┐
│ OUTPUT TO USER                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
AI: Planning a trip to Dubai can be exciting! Here's a comprehensive guide...
[Turn 1 | Window: 1 | Summary: 0 chars]


════════════════════════════════════════════════════════════════════════════════
                                  TURN 2
════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│ USER INPUT                                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
You: plan 2 day trip for india

         ↓

┌─────────────────────────────────────────────────────────────────────────────┐
│ STATE BEFORE GRAPH                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
messages: [
  HumanMessage("plan the trip for dubai"),
  AIMessage("Planning a trip to Dubai..."),
  HumanMessage("plan 2 day trip for india")
]
summary: ""
turn_count: 1
window_count: 1

         ↓

┌─────────────────────────────────────────────────────────────────────────────┐
│ GRAPH EXECUTION                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

    [START]
       ↓
    ┌──────────────┐
    │  CHAT NODE   │
    └──────────────┘

    What happens:
    -------------
    1. context = []
    2. summary check: FALSE (still empty)
    3. Add recent: context = [Dubai Q&A, India question]
    4. LLM responds: AIMessage("Planning a 2-day trip to India...")
    5. Updates: turn_count=2, window_count=2

       ↓

    ┌──────────────────┐
    │ ROUTER           │
    │ window_count = 2 │
    │ 2 >= 3? NO       │
    └──────────────────┘

       ↓

    [END]

         ↓

┌─────────────────────────────────────────────────────────────────────────────┐
│ OUTPUT TO USER                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
AI: Planning a 2-day trip to India (Delhi) can be exciting! Here's an itinerary...
[Turn 2 | Window: 2 | Summary: 0 chars]


════════════════════════════════════════════════════════════════════════════════
                    TURN 3 - COMPRESSION TRIGGERED! 🔥
════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│ USER INPUT                                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
You: plan 2 day trip for mumbai, india

         ↓

┌─────────────────────────────────────────────────────────────────────────────┐
│ STATE BEFORE GRAPH                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
messages: [
  HumanMessage("plan the trip for dubai"),        ← Will be compressed
  AIMessage("Planning a trip to Dubai..."),       ← Will be compressed
  HumanMessage("plan 2 day trip for india"),      ← Will be compressed
  AIMessage("Planning Delhi trip..."),            ← Will be compressed
  HumanMessage("plan 2 day trip for mumbai")      ← Recent, kept
]
summary: ""
turn_count: 2
window_count: 2

         ↓

┌─────────────────────────────────────────────────────────────────────────────┐
│ GRAPH EXECUTION - PART 1: CHAT NODE                                        │
└─────────────────────────────────────────────────────────────────────────────┘

    [START]
       ↓
    ┌──────────────┐
    │  CHAT NODE   │
    └──────────────┘

    What happens:
    -------------
    1. context = []
    2. summary check: FALSE
    3. Add recent: context = last 4 messages
       [Dubai Q&A, India question, Mumbai question]
    4. LLM responds: AIMessage("Mumbai planning...")
    5. Updates: turn_count=3, window_count=3

       ↓

    ┌──────────────────┐
    │ ROUTER           │
    │ window_count = 3 │
    │ 3 >= 3? YES! ✓  │
    │ → 'summarizer'   │
    └──────────────────┘

       ↓

┌─────────────────────────────────────────────────────────────────────────────┐
│ GRAPH EXECUTION - PART 2: SUMMARIZER NODE                                  │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────┐
    │ SUMMARIZER NODE │
    └─────────────────┘

    Step-by-step compression:
    -------------------------

    1. Extract older messages (exclude last 4):
       older_messages = messages[:-4]
       → [
           HumanMessage("plan the trip for dubai"),
           AIMessage("Planning a trip to Dubai...")
         ]

    2. Check if anything to compress:
       if not older_messages: → FALSE (we have 2 messages)

    3. Build summarization prompt:
       prompt = "Summarize this conversation in 2-3 sentences:\n\n"

    4. Check for existing summary:
       if state["summary"]: → FALSE (first compression)

    5. Format messages:
       prompt += "User: plan the trip for dubai\n"
       prompt += "AI: Planning a trip to Dubai...\n"

    6. Call LLM to summarize:
       summary = llm.invoke([HumanMessage(prompt)])
       → "User asked about planning a Dubai trip. Discussed
          attractions, hotels, and itinerary recommendations."

    7. Print notification:
       [COMPRESSED] Older messages compressed into summary

    8. Return updates:
       {
         "messages": state["messages"][-4:],  ← Keep only last 4!
         "summary": "User asked about planning a Dubai trip...",
         "window_count": 0  ← RESET!
       }

       ↓

    [END]

         ↓

┌─────────────────────────────────────────────────────────────────────────────┐
│ STATE AFTER GRAPH                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
messages: [
  HumanMessage("plan 2 day trip for india"),      ← Recent kept
  AIMessage("Planning Delhi trip..."),            ← Recent kept
  HumanMessage("plan 2 day trip for mumbai"),     ← Recent kept
  AIMessage("Mumbai planning...")                 ← Recent kept
]
summary: "User asked about planning a Dubai trip. Discussed attractions and itinerary."
turn_count: 3
window_count: 0  ← RESET!

NOTICE:
- Dubai Q&A deleted from messages ✓
- Dubai info preserved in summary ✓
- Window counter reset ✓
- Turn counter still incrementing ✓

         ↓

┌─────────────────────────────────────────────────────────────────────────────┐
│ OUTPUT TO USER                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
[COMPRESSED] Older messages compressed into summary

AI: Mumbai, the bustling financial capital of India, is known for...
[Turn 3 | Window: 0 | Summary: 484 chars]


════════════════════════════════════════════════════════════════════════════════
                                  TURN 4
════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│ USER INPUT                                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
You: plan 2 day trip for goa

         ↓

┌─────────────────────────────────────────────────────────────────────────────┐
│ STATE BEFORE GRAPH                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
messages: [
  HumanMessage("plan 2 day trip for india"),
  AIMessage("Planning Delhi trip..."),
  HumanMessage("plan 2 day trip for mumbai"),
  AIMessage("Mumbai planning..."),
  HumanMessage("plan 2 day trip for goa")
]
summary: "User asked about Dubai trip planning..."
turn_count: 3
window_count: 0

         ↓

┌─────────────────────────────────────────────────────────────────────────────┐
│ GRAPH EXECUTION                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

    [START]
       ↓
    ┌──────────────┐
    │  CHAT NODE   │
    └──────────────┘

    What happens (WITH SUMMARY NOW!):
    ---------------------------------
    1. Build context:
       context = []

    2. Check for summary:
       if state["summary"]: → TRUE! ✓
       → context.append(SystemMessage(
           "Previous conversation: User asked about Dubai trip..."
         ))

    3. Add recent messages:
       context.extend(state["messages"][-4:])
       → context = [
           SystemMessage("Previous: Dubai..."),  ← Summary!
           HumanMessage("plan 2 day trip for india"),
           AIMessage("Planning Delhi..."),
           HumanMessage("plan 2 day trip for mumbai"),
           AIMessage("Mumbai planning..."),
           HumanMessage("plan 2 day trip for goa")
         ]

    4. Call LLM:
       LLM sees summary + recent messages!
       → AIMessage("Goa planning...")

    5. Updates:
       turn_count: 4
       window_count: 1  ← Started counting again

       ↓

    ┌──────────────────┐
    │ ROUTER           │
    │ window_count = 1 │
    │ 1 >= 3? NO       │
    └──────────────────┘

       ↓

    [END]

         ↓

┌─────────────────────────────────────────────────────────────────────────────┐
│ OUTPUT TO USER                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
AI: Goa, known for its stunning beaches and vibrant nightlife...
[Turn 4 | Window: 1 | Summary: 484 chars]


════════════════════════════════════════════════════════════════════════════════
                    WHAT AI SEES AT EACH TURN
════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│ TURN 1 - AI INPUT                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
[
  HumanMessage("plan the trip for dubai")
]

TOTAL MESSAGES: 1


┌─────────────────────────────────────────────────────────────────────────────┐
│ TURN 2 - AI INPUT                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
[
  HumanMessage("plan the trip for dubai"),
  AIMessage("Planning a trip to Dubai..."),
  HumanMessage("plan 2 day trip for india")
]

TOTAL MESSAGES: 3


┌─────────────────────────────────────────────────────────────────────────────┐
│ TURN 3 - AI INPUT (BEFORE COMPRESSION)                                     │
└─────────────────────────────────────────────────────────────────────────────┘
[
  HumanMessage("plan the trip for dubai"),
  AIMessage("Planning a trip to Dubai..."),
  HumanMessage("plan 2 day trip for india"),
  AIMessage("Planning Delhi..."),
  HumanMessage("plan 2 day trip for mumbai")
]

TOTAL MESSAGES: 5


┌─────────────────────────────────────────────────────────────────────────────┐
│ TURN 4 - AI INPUT (AFTER COMPRESSION) ⭐                                   │
└─────────────────────────────────────────────────────────────────────────────┘
[
  SystemMessage("Previous conversation: User asked about Dubai trip..."),  ← SUMMARY!
  HumanMessage("plan 2 day trip for india"),
  AIMessage("Planning Delhi..."),
  HumanMessage("plan 2 day trip for mumbai"),
  AIMessage("Mumbai planning..."),
  HumanMessage("plan 2 day trip for goa")
]

TOTAL MESSAGES: 6 (but 1 is compressed summary!)

NOTICE: Dubai conversation is now just 1 summary message instead of 2 full messages!


════════════════════════════════════════════════════════════════════════════════
                    STATE COMPARISON ACROSS TURNS
════════════════════════════════════════════════════════════════════════════════

┌──────┬──────────┬──────────┬──────────────┬──────────────────────────┐
│ Turn │ Messages │ Summary  │ Turn Counter │ Window Counter           │
├──────┼──────────┼──────────┼──────────────┼──────────────────────────┤
│  1   │    2     │   0 chr  │      1       │ 1 (counting...)          │
│  2   │    4     │   0 chr  │      2       │ 2 (counting...)          │
│  3   │    6→4   │ 484 chr  │      3       │ 3→0 (COMPRESSED!)        │
│  4   │    6     │ 484 chr  │      4       │ 1 (counting again...)    │
│  5   │    8     │ 484 chr  │      5       │ 2 (counting...)          │
│  6   │   10→4   │ 720 chr  │      6       │ 3→0 (COMPRESSED AGAIN!)  │
└──────┴──────────┴──────────┴──────────────┴──────────────────────────┘

PATTERN:
- Messages grow until window=3, then compress back to 4
- Summary grows with each compression
- Turn counter never resets
- Window counter resets to 0 after compression


════════════════════════════════════════════════════════════════════════════════
                    MEMORY COMPARISON: WITH vs WITHOUT COMPRESSION
════════════════════════════════════════════════════════════════════════════════

WITHOUT COMPRESSION (Normal Chatbot):
┌──────┬──────────────┐
│ Turn │ Total Msgs   │
├──────┼──────────────┤
│  10  │     20       │
│  20  │     40       │
│  50  │    100       │ ← SLOW!
│ 100  │    200       │ ← VERY SLOW!
└──────┴──────────────┘

WITH COMPRESSION (Our Agent):
┌──────┬──────────┬──────────┬────────────────┐
│ Turn │ Raw Msgs │ Summary  │ Effective Size │
├──────┼──────────┼──────────┼────────────────┤
│  10  │    4     │ 800 chr  │  ~6 messages   │
│  20  │    4     │ 1200 chr │  ~7 messages   │
│  50  │    4     │ 2000 chr │  ~10 messages  │
│ 100  │    4     │ 3000 chr │  ~15 messages  │
└──────┴──────────┴──────────┴────────────────┘

RESULT: Always bounded, never explodes!


════════════════════════════════════════════════════════════════════════════════
                    COMPRESSION CYCLE VISUALIZATION
════════════════════════════════════════════════════════════════════════════════

Turn 1-2: Building up
───────────────────────
messages: [█ █]
summary:  [ ]
window:   1→2

Turn 3: Compression!
────────────────────
messages: [█ █ █ █ █ █]  →  [█ █ █ █]
           ↑ ↑ ↑ ↑              ↑ ↑ ↑ ↑
           Compressed           Recent kept

summary:  [ ]  →  [████]
window:   3    →  0 (RESET)

Turn 4-5: Building up again
───────────────────────────
messages: [█ █ █ █ █ █]
summary:  [████]
window:   1→2

Turn 6: Compression again!
──────────────────────────
messages: [█ █ █ █ █ █]  →  [█ █ █ █]
summary:  [████]  →  [████████]  (merged!)
window:   3    →  0 (RESET)


════════════════════════════════════════════════════════════════════════════════
                    KEY TAKEAWAYS
════════════════════════════════════════════════════════════════════════════════

1. WINDOW COUNTER
   - Counts turns since last compression
   - Resets to 0 after compression
   - Prevents immediate re-compression

2. TURN COUNTER
   - Counts total conversation turns
   - NEVER resets
   - Tracks conversation length

3. SUMMARY
   - Stores compressed old context
   - Grows with each compression (needs size control!)
   - Injected as SystemMessage to AI

4. MESSAGES
   - Recent messages kept in full
   - Older messages compressed then deleted
   - Always bounded to ~4-6 messages

5. COMPRESSION TRIGGER
   - When window_count >= 3
   - Routes to summarizer node
   - Automatic, no user intervention

6. AI CONTEXT
   - Turn 1-2: Raw messages only
   - Turn 3+: Summary + recent messages
   - AI remembers everything (compressed or raw)

════════════════════════════════════════════════════════════════════════════════
