# Conversational Planner Agent (Multimodal-Ready)

## What is This?

A production-grade conversational planning assistant that:
- ✅ Accepts **multiple input types** (text, voice, image)
- ✅ **Streams** responses token-by-token
- ✅ **Plans** tasks (not just answers questions)
- ✅ **Remembers** context across turns
- ✅ **Normalizes** all modalities into text
- ✅ **Async-ready** architecture

## Quick Start

```bash
cd "c:\EADP\Week 16\multimodel"
python planner_agent.py
```

### Example Usage

```
You: text: Plan a 3-day trip to Tokyo
Planner: Here's a structured 3-day Tokyo itinerary...

You: voice: What about budget hotels?
[VOICE PROCESSOR] Mock: Transcribing 'What about budget hotels?'
Planner: For budget-friendly accommodations in Tokyo...

You: image: Photo of cherry blossoms
[IMAGE PROCESSOR] Mock: Analyzing 'Photo of cherry blossoms'
Planner: Based on the cherry blossoms, spring is ideal for Tokyo...

You: quit
```

## Key Concepts

### 1. Modality Normalization

**All inputs become text:**

```
Text:  "Plan my week"        → "Plan my week"
Voice: audio.mp3             → "[Transcribed]: Plan my week"
Image: vacation_photo.jpg    → "[Image]: Beach scene with..."
```

**Why?**
- Core reasoning engine only processes text
- Clean separation of concerns
- Easy to add new modalities

### 2. Planning vs Chatting

**Chatbot:**
```
User: What's Tokyo like?
Bot: Tokyo is Japan's capital with 14 million people...
```

**Planner:**
```
User: Plan my Tokyo trip
Planner: Let me create a structured plan:

Day 1: Arrival & Orientation
- Morning: Check into hotel in Shinjuku
- Afternoon: Visit Tokyo Metropolitan Building (free observation deck)
- Evening: Explore Kabukicho nightlife

Day 2: Cultural Immersion
...
```

**Difference:**
- Chatbot: Answers questions
- Planner: Breaks down tasks, provides structure, asks clarifications

### 3. Streaming Responses

```
Planner: Let me create a plan for your Tokyo trip...
         ↑ Text appears word-by-word as AI generates it
```

Benefits:
- Immediate feedback
- Feels faster
- Better UX

### 4. Memory Management

```
Turn 1-4: Keep all messages
Turn 5:   Compress older messages → summary
Turn 6-9: Keep recent + summary
Turn 10:  Compress again
```

Prevents context overflow!

## Architecture

```
┌─────────────────────────────────────────────┐
│            USER INPUT                       │
│  Commands:                                  │
│  - text: <message>                          │
│  - voice: <message>  (mock)                 │
│  - image: <desc>     (mock)                 │
└─────────────────────────────────────────────┘
                    ↓
        ┌───────────────────────┐
        │   INPUT ROUTER        │
        │ (Detect input type)   │
        └───────────────────────┘
                    ↓
    ┌───────────────┼───────────────┐
    ↓               ↓               ↓
┌────────┐   ┌───────────┐   ┌───────────┐
│ TEXT   │   │  VOICE    │   │  IMAGE    │
│PROCESS │   │ PROCESS   │   │  PROCESS  │
│(Direct)│   │(Mock STT) │   │(Mock Cap) │
└────────┘   └───────────┘   └───────────┘
    │               │               │
    └───────────────┼───────────────┘
                    ↓
    ┌───────────────────────────────────┐
    │  MODALITY NORMALIZATION          │
    │  All → extracted_text            │
    └───────────────────────────────────┘
                    ↓
        ┌───────────────────────┐
        │  PLANNER NODE         │
        │ (Core reasoning +     │
        │  streaming output)    │
        └───────────────────────┘
                    ↓
        ┌───────────────────────┐
        │  MEMORY CHECK         │
        │ (Turn 5, 10, 15...)   │
        └───────────────────────┘
          ↓               ↓
      Compress          END
```

## State Structure

```python
{
    # Conversation
    "messages": [...],
    "summary": "Previous context...",
    "total_turn_count": 5,

    # Multimodal
    "input_type": "text" | "voice" | "image",
    "raw_input_payload": "Original input",
    "extracted_text": "Normalized text",
    "metadata": {
        "processor": "voice",
        "confidence": 0.95,
        "language": "en"
    }
}
```

## Node Breakdown

### 1. Input Router
**Purpose:** Determine input modality

```python
def input_router(state):
    if state["input_type"] == "text":
        return "text_processor"
    elif state["input_type"] == "voice":
        return "voice_processor"
    elif state["input_type"] == "image":
        return "image_processor"
```

### 2. Text Processor
**Purpose:** Direct pass-through

```python
def text_processor(state):
    return {"extracted_text": state["raw_input_payload"]}
```

### 3. Voice Processor (Mock)
**Purpose:** Speech-to-text conversion

**Current:** Mock transcription
**Future:** Whisper API integration

```python
def voice_processor(state):
    # Future: Call Whisper
    return {
        "extracted_text": f"[Transcribed]: {state['raw_input_payload']}",
        "metadata": {"confidence": 0.95, "language": "en"}
    }
```

### 4. Image Processor (Mock)
**Purpose:** Image understanding

**Current:** Mock captioning
**Future:** GPT-4 Vision / BLIP integration

```python
def image_processor(state):
    # Future: Call GPT-4 Vision
    return {
        "extracted_text": f"[Image]: {state['raw_input_payload']}",
        "metadata": {"detected_objects": [...]}
    }
```

### 5. Planner Node
**Purpose:** Core planning with streaming

```python
def planner_node(state):
    context = build_context(state)

    # Stream response
    for chunk in llm.stream(context):
        print(chunk.content, end="", flush=True)
        full_response += chunk.content

    return {"messages": [AIMessage(content=full_response)]}
```

### 6. Memory Compressor
**Purpose:** Compress old messages

**Trigger:** Every 5 turns

```python
def should_compress(state):
    if state["total_turn_count"] % 5 == 0:
        return "compress"
    return "end"
```

## Example Conversations

### Example 1: Planning a Project

```
You: text: I need to build a mobile app in 3 months
Planner: Let me break this down into phases:

Phase 1 (Month 1): Planning & Design
- Week 1-2: Requirements gathering, user research
- Week 3-4: Wireframing, UI/UX design

Phase 2 (Month 2): Development
- Week 5-6: Core features implementation
- Week 7-8: Secondary features, API integration

Phase 3 (Month 3): Polish & Launch
- Week 9-10: Testing, bug fixes
- Week 11: Beta testing with users
- Week 12: Launch preparation, app store submission

What type of app are you building?
```

### Example 2: Voice Input (Mock)

```
You: voice: What's the budget for marketing?
[VOICE PROCESSOR] Processing voice input...
[VOICE PROCESSOR] Mock: Transcribing 'What's the budget for marketing?'

Planner: For the app launch, here's a suggested marketing budget breakdown:

Total: $10,000-15,000 for initial 3 months

Pre-launch (Month 1): $3,000
- Social media ads: $1,500
- Influencer outreach: $1,000
- Landing page + SEO: $500

Launch Month (Month 2): $7,000
- App store ads: $3,000
- PR campaign: $2,000
- Launch events: $2,000

Post-launch (Month 3): $5,000
- Retention campaigns: $3,000
- User acquisition: $2,000
```

### Example 3: Image Input (Mock)

```
You: image: Sketch of app wireframe
[IMAGE PROCESSOR] Processing image input...
[IMAGE PROCESSOR] Mock: Analyzing 'Sketch of app wireframe'

Planner: Based on the wireframe, I can see:

Key Features Identified:
- Login/signup screen
- Dashboard with analytics
- Settings panel
- Navigation menu

Design Recommendations:
1. The dashboard layout looks good for desktop, but consider mobile-first design
2. Add user onboarding flow
3. Include search functionality in main nav
4. Consider dark mode option

Next Steps:
- Create high-fidelity mockups in Figma
- Define user flows between screens
- Plan API endpoints for dashboard data
```

## Multimodal Future Integration

### Voice (Whisper API)

```python
import openai

def voice_processor_real(state):
    audio_file = open(state["raw_input_payload"], "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file)

    return {
        "extracted_text": transcript.text,
        "metadata": {
            "language": transcript.language,
            "confidence": 0.95
        }
    }
```

### Image (GPT-4 Vision)

```python
def image_processor_real(state):
    response = openai.ChatCompletion.create(
        model="gpt-4-vision-preview",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image for planning purposes"},
                {"type": "image_url", "image_url": state["raw_input_payload"]}
            ]
        }]
    )

    return {
        "extracted_text": response.choices[0].message.content,
        "metadata": {"vision_model": "gpt-4"}
    }
```

## Benefits

### 1. Modality Agnostic Core
- Planning logic unchanged regardless of input type
- Easy to add new modalities (video, PDF, etc.)

### 2. Streaming UX
- Users see progress immediately
- Feels faster than batch processing

### 3. Memory Management
- Long conversations don't explode context
- Summary preserves important details

### 4. Async-Ready
- Voice/image processing can be async
- Non-blocking operations

### 5. Clean Architecture
- Separation of concerns
- Easy to test
- Easy to extend

## Files

```
multimodel/
├── planner_agent.py         ← Main implementation
├── README.md                ← This file
├── ARCHITECTURE.md          ← Technical deep dive
├── MODALITY_GUIDE.md        ← Multimodal concepts
├── ASYNC_GUIDE.md           ← Async patterns
├── EXAMPLES.md              ← More examples
└── .env.example             ← Config template
```

## Next Steps

1. **Run the demo**
   ```bash
   python planner_agent.py
   ```

2. **Try different input types**
   - `text: Plan my week`
   - `voice: Budget ideas?`
   - `image: Office layout sketch`

3. **Watch memory compression**
   - Ask 5 questions
   - See compression trigger

4. **Read architecture docs**
   - ARCHITECTURE.md
   - MODALITY_GUIDE.md

5. **Integrate real APIs**
   - Add Whisper for voice
   - Add GPT-4 Vision for images

---

**Key Insight:** This agent shows how to build multimodal systems with clean architecture!
