# Profile-Aware Chatbot with Memory Injection

A CLI chatbot that remembers who you are across sessions. Every user gets a persistent profile stored in a JSON file. When you return, the chatbot greets you by name, references your last topic, and responds in the tone you prefer — because that context is injected directly into the model's system prompt before it reads your message.

---

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in your API key in .env
python main.py
```

---

## File Structure

```
profile_chatbot/
│
├── profiles/
│   └── users.json          ← Persistent storage for all user profiles
│
├── profile_manager.py      ← Reads and writes user profiles to JSON
├── memory_injector.py      ← Formats profile data into an LLM-ready context string # Ai part.
├── chatbot.py              ← Builds the system prompt and calls the LLM
├── main.py                 ← CLI entry point and conversation loop
├── requirements.txt
└── .env.example
```

---

## How It Works

```
┌──────────────────────────────────────────────────────────────┐
│                        main.py                               │
│                                                              │
│  User enters username   # Anant                                      │
│       │                                                      │
│       ▼                                                      │
│  ProfileManager.get_profile(username)                        │
│       │                                                      │
│       ├── Profile exists → greet + show last topic           │
│       └── No profile     → collect name + tone → create      │
│                                                              │
│  Conversation loop begins                                    │
│  User types a message → generate_response(input, profile)   │
│  Assistant replies → loop repeats                            │
│                                                              │
│  On exit → ask today's topic → update_last_topic() → save   │
└──────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                     chatbot.py                               │
│                                                              │
│  generate_response(user_input, profile)                      │
│       │                                                      │
│       ├── MemoryInjector.build_memory_context(profile)       │
│       │        Returns formatted string:                     │
│       │        "User Profile:                                │
│       │         Name: Rahul                                  │
│       │         Preferred Tone: Friendly                     │
│       │         Last Discussed Topic: LangGraph"             │
│       │                                                      │
│       ├── _build_system_prompt(profile, memory_context)      │
│       │        Assembles:                                    │
│       │        "You are a helpful AI assistant.              │
│       │         [memory context block]                       │
│       │         Use a warm, friendly, encouraging tone.      │
│       │         Relate explanation to: LangGraph"            │
│       │                                                      │
│       └── OpenAI client call → returns response text         │
└──────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                  profiles/users.json                         │
│                                                              │
│  {                                                           │
│    "rahul": {                                                │
│      "name": "Rahul",                                        │
│      "preferred_tone": "friendly",                           │
│      "last_topic": "LangGraph"                               │
│    }                                                         │
│  }                                                           │
│                                                              │
│  Written by ProfileManager after every update.              │
│  Read when the user returns in the next session.             │
└──────────────────────────────────────────────────────────────┘
```

---

## Memory Injection — The Core Concept

Memory injection means taking stored information about the user and placing it inside the system prompt before the LLM reads the conversation. The model treats the system prompt as ground truth — it shapes how the model behaves before seeing a single word of the user's message.

Without memory injection, every session starts from zero. The model has no idea who it is talking to.

With memory injection, the model starts every response already knowing the user's name, their preferred tone, and what they were last studying. It can say "Building on what we covered last time with LangGraph..." because that context was handed to it in the system prompt.

```
System Prompt (with memory injected)
─────────────────────────────────────────────────────────────
You are a helpful AI assistant.

User Profile:
Name: Rahul
Preferred Tone: Friendly
Last Discussed Topic: LangGraph

Use a warm, friendly, and encouraging tone.
If possible, relate your explanation to their previous topic: LangGraph.
─────────────────────────────────────────────────────────────
User message: "Explain how agents work."
```

The model sees the profile context before the user's question. This is memory injection.

---

## Supported Tones

| Tone | Model Instruction |
|---|---|
| friendly | Warm, encouraging tone |
| formal | Professional and structured |
| concise | Brief and direct, no elaboration |
| detailed | Thorough, step-by-step explanations |
| humorous | Conversational with light humour |

---

## Example Session

**Session 1 — New user:**
```
Enter your username: rahul
We don't have a profile for you yet. What is your name? Rahul
Choose your preferred tone: friendly

Nice to meet you, Rahul! Your profile has been created.
Preferred tone set to: Friendly

You: What is LangGraph?
Assistant: Great question! LangGraph is a library built on top of LangChain...

[exit]
What topic did we discuss today? LangGraph
Got it. I'll remember 'LangGraph' for next time.
```

**Session 2 — Returning user:**
```
Enter your username: rahul

Welcome back, Rahul!
Last time we discussed: LangGraph

You: Now explain agents.
Assistant: Building on what we covered with LangGraph last time, agents are...
```

---

## Profile Storage Format

```json
{
  "rahul": {
    "name": "Rahul",
    "preferred_tone": "friendly",
    "last_topic": "LangGraph"
  },
  "sara": {
    "name": "Sara",
    "preferred_tone": "formal",
    "last_topic": "RAG pipelines"
  }
}
```

Profiles are stored in `profiles/users.json`. Each session writes the updated profile back to this file, so the data persists across restarts.
