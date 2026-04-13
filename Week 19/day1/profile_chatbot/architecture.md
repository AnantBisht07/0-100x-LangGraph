# Profile-Aware Chatbot — Architecture

## What This System Does

This system is a chatbot that knows who it is talking to. Not because it has access to a database or a search engine, but because it reads a stored user profile and places that information directly inside the model's system prompt before every response. The model starts each reply already knowing the user's name, the communication style they prefer, and what they were last studying.

This technique is called memory injection. It is one of the fundamental patterns in adaptive AI systems.

---

## The Problem Being Solved

A standard chatbot is stateless. Every conversation starts from zero. The model has no idea who you are, how you like to be spoken to, or what you were learning last week. You have to re-explain your context every single time.

Memory injection solves this by persisting user context to a file and reloading it at the start of every session. The loaded context is then formatted into text and injected into the system prompt. From the model's perspective, it was always aware of this information. It does not know the information came from a file.

---

## Module Map

```
┌─────────────────────────────────────────────────────────────┐
│  main.py                                                    │
│  Entry point. Manages the CLI flow.                         │
│  Calls ProfileManager to load or create profiles.           │
│  Calls generate_response() for each user message.           │
│  Calls update_last_topic() before the session ends.         │
└────────────────────────┬────────────────────────────────────┘
                         │ uses
           ┌─────────────┼─────────────┐
           ▼             ▼             ▼
┌──────────────┐  ┌────────────┐  ┌────────────────────┐
│ profile_     │  │ chatbot.py │  │ profile_manager.py │
│ manager.py   │  │            │  │                    │
│              │  │ generate_  │  │ load_profiles()    │
│ Reads and    │  │ response() │  │ save_profiles()    │
│ writes       │  │            │  │ get_profile()      │
│ users.json   │  │ Builds     │  │ create_profile()   │
│              │  │ system     │  │ update_last_topic()│
│              │  │ prompt +   │  │                    │
│              │  │ calls LLM  │  │                    │
└──────────────┘  └─────┬──────┘  └────────────────────┘
                        │ uses
                        ▼
               ┌────────────────────┐
               │ memory_injector.py │
               │                    │
               │ build_memory_      │
               │ context(profile)   │
               │                    │
               │ Returns formatted  │
               │ context string     │
               └────────────────────┘
```

---

## Data Flow — Step by Step

```
Step 1: User enters username
        main.py → ProfileManager.get_profile(username)

        If profile exists:
            → Greet user, display last topic
        If no profile:
            → Collect name and tone
            → ProfileManager.create_profile()
            → Save to users.json

        ↓

Step 2: User types a message
        main.py → chatbot.generate_response(user_input, profile)

        Inside generate_response:

          a) MemoryInjector.build_memory_context(profile)
             Produces:
             "User Profile:
              Name: Rahul
              Preferred Tone: Friendly
              Last Discussed Topic: LangGraph"

          b) _build_system_prompt(profile, memory_context)
             Produces:
             "You are a helpful AI assistant.

              User Profile:
              Name: Rahul
              Preferred Tone: Friendly
              Last Discussed Topic: LangGraph

              Use a warm, friendly, and encouraging tone.
              If possible, relate your explanation to: LangGraph."

          c) OpenAI API call
             messages = [
               {"role": "system", "content": <system prompt above>},
               {"role": "user",   "content": <user message>}
             ]

          d) Returns response text

        ↓

Step 3: Response printed to terminal
        Loop continues until user types 'exit'

        ↓

Step 4: User exits
        main.py prompts: "What topic did we discuss today?"
        ProfileManager.update_last_topic(username, topic)
        → updates users.json
        → next session will inject this topic into the prompt
```

---

## Memory Injection in Detail

The system prompt is the most powerful lever available when working with LLMs. Whatever you place in the system prompt, the model treats as established context — it does not question it, it does not look it up. It just uses it.

This system exploits that property. When the model sees:

```
User Profile:
Name: Rahul
Preferred Tone: Friendly
Last Discussed Topic: LangGraph
```

...at the top of its instructions, it behaves as if it has always known these things about Rahul. It adjusts its vocabulary, its warmth, and the examples it reaches for — all because of three lines of text that were injected before the conversation started.

This is fundamentally different from giving the user a way to tell the bot their preferences mid-conversation. Memory injection means the adaptation happens before the first word is exchanged.

---

## Tone Adaptation

The chatbot reads the preferred_tone field from the profile and maps it to a concrete instruction. This mapping lives in chatbot.py in the TONE_INSTRUCTIONS dictionary.

```
"friendly"  → "Use a warm, friendly, and encouraging tone."
"formal"    → "Use a professional and formal tone."
"concise"   → "Be brief and direct. Avoid unnecessary elaboration."
"detailed"  → "Provide thorough, step-by-step explanations."
"humorous"  → "Be conversational and lightly humorous where appropriate."
```

The model does not decide how to talk. It is told. The profile stores the preference as a simple string. The chatbot converts that string into a behavioural instruction. The model follows it.

---

## Persistence Model

```
Session 1                    Session 2
─────────────────            ─────────────────────────────
User types: rahul            User types: rahul
                             ↓
No profile found             users.json read
                             Profile for "rahul" loaded
                             ↓
Name: Rahul                  name: Rahul
Tone: friendly               preferred_tone: friendly
                             last_topic: LangGraph  ← remembered
                             ↓
Conversation runs            Memory injected into system prompt

On exit:                     On exit:
Topic saved: LangGraph       Topic saved: Agents
users.json written           users.json written
```

The only file that persists between sessions is `profiles/users.json`. Everything else is computed fresh on each run from that file. The file is the memory. The system prompt is the delivery mechanism.

---

## Why This Architecture

**profile_manager.py is separate** so that file I/O is isolated. If the storage format ever changes — a database, an API, a cloud store — only this file changes. chatbot.py and memory_injector.py never need to know how profiles are stored.

**memory_injector.py is separate** so that the prompt format can be changed without touching the chatbot. If you want to add a new field to the memory context — say, the user's skill level — you add it to the injector. Nothing else changes.

**chatbot.py is separate** so that LLM interaction is isolated from CLI logic. If you replace the CLI with a web interface tomorrow, chatbot.py stays exactly the same.

**main.py is thin** by design. It coordinates. It does not implement. Every decision about how to store data, how to format memory, how to call the LLM — those decisions are made by the specialist modules. main.py just wires them together in the right order.
