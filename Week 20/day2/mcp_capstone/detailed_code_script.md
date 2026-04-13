# Detailed Code Script – MCP Capstone (Day 2)
### Line-by-line explanation of every file

**Teaching time: 2–3 hours (with live coding)**
**Audience: Students who have run the project at least once**

---

> Before starting, open `python main.py` in a terminal and keep it live.
> Also have all 7 files open in editor tabs side by side.

---

## THE CORE PRINCIPLE (say this first, every class)

```
"AI systems don't fail because models are weak.
 They fail because context is poorly managed."
```

This quote is on line 4–5 of `config.py`, line 7–8 of `memory_store.py`,
line 16–17 of `context_manager.py`, and in every other file.

It is not decoration. It is the engineering principle driving every
design decision you are about to see.

---

---

# FILE 1: config.py
### "The single source of truth"

---

```
Open config.py
```

### Lines 8–9 – Imports

```python
import os
from dotenv import load_dotenv
```

**`import os`** — we need this to read environment variables.
Environment variables are values you set outside your code (in `.env` file)
so that secret keys never appear inside source code.

**`from dotenv import load_dotenv`** — `python-dotenv` is a library that
reads a file called `.env` and loads its contents as environment variables.
Without this, `os.getenv()` would return empty strings.

---

### Line 11 – Load environment

```python
load_dotenv()
```

This is the first thing that runs when Python imports `config.py`.
It reads the `.env` file from disk into memory.

**Why call it at the top?**
Because every line below this uses `os.getenv()`.
If you moved this to the bottom, all the `os.getenv()` calls above it
would fire before `.env` was loaded → all keys would be empty strings.

---

### Lines 14–16 – OpenRouter configuration

```python
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
MODEL_NAME: str = "anthropic/claude-haiku-4-5"
```

**Line 14** — `os.getenv("OPENROUTER_API_KEY", "")` reads the key from
the environment. The second argument `""` is the default if the key is missing.
So if `.env` has no key, this returns `""` instead of crashing.

**Line 15** — OpenRouter is OpenAI-compatible. That means we use the same
`openai` Python SDK, but we point it at a different URL. OpenRouter then
routes our request to whichever model we specify.

**Line 16** — `"anthropic/claude-haiku-4-5"` is the OpenRouter model ID.
The format is `provider/model-name`. You can change this one line to switch
to `openai/gpt-4o-mini` or `google/gemini-flash-1.5` and the entire system
uses a different model. No other file needs to change.

**Why store model name here?**
Because it is used in `summarizer.py` AND `agent_pipeline.py`.
If you hardcode it in both files and want to change it, you edit two places
and risk them getting out of sync. Centralised config prevents that.

---

### Lines 19–21 – Memory tuning

```python
MEMORY_FILE: str = "memory_store.json"
HISTORY_THRESHOLD: int = 10
RECENT_MESSAGES_LIMIT: int = 5
```

**Line 19** — The name of the JSON file on disk.
All users share one file. The file is a dict keyed by user_id.

**Line 20** — `HISTORY_THRESHOLD = 10`
When a user has sent 10 or more messages, we trigger summarisation.
This is the most important tuning knob in the whole system.
Set it lower → compress more aggressively (cheaper, but less raw context).
Set it higher → keep more raw history (better context, costs more tokens).

**Line 21** — `RECENT_MESSAGES_LIMIT = 5`
After compression, we keep only the last 5 messages in raw form.
These 5 are the ones actually sent verbatim to the LLM.
Everything older is represented only by the summary text.

**The relationship:**
```
Threshold (10) controls WHEN compression fires.
Recent limit (5) controls HOW MUCH is kept raw after firing.
```

---

### Lines 24–25 – Token budget

```python
MAX_CONTEXT_TOKENS: int = 4_000
AVG_CHARS_PER_TOKEN: int = 4
```

**Line 24** — Our maximum context size in tokens. The validator will warn
us if we approach or exceed this. `4_000` uses Python's underscore separator
for readability — it is just the number 4000.

**Line 25** — A rough rule: one token ≈ 4 characters in English text.
This is not exact. It is an approximation used only for early warning.
Real token counting requires the tokenizer library.

---

### Lines 28–32 – System instruction

```python
SYSTEM_INSTRUCTION: str = (
    "You are a context-aware AI assistant that remembers users across sessions. "
    "Always personalise your responses using the user's profile and conversation history. "
    "Be concise, helpful, and technical when the user's preferences indicate it."
)
```

This is the first thing the LLM reads in every context.
It sets the model's role, tone, and behaviour rules.

**Why put it in config and not in context_manager.py?**
Because it is configuration. If a student wants to change the agent's
personality, they edit config.py — not the logic files.
The logic files (context_manager) import it, they do not own it.

---

---

# FILE 2: memory_store.py
### "The database layer"

---

```
Open memory_store.py
```

This file is the ONLY file in the project that reads from and writes to disk.
All other files call functions in this file. They never touch the file directly.
This is called **single responsibility** — one job, one place.

---

### Lines 11–15 – Imports

```python
import json
import os
from typing import Any

from config import MEMORY_FILE
```

**`import json`** — for reading/writing JSON files.
**`import os`** — for checking if the file exists (`os.path.exists`).
**`from typing import Any`** — imported but not used in visible code (from an earlier draft). Harmless.
**`from config import MEMORY_FILE`** — we import just the filename string.
This file does not hardcode `"memory_store.json"` — it gets it from config.

---

### Lines 20–25 – `_load_db()` (private)

```python
def _load_db() -> dict:
    """Read the entire memory file from disk; return an empty dict if missing."""
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r", encoding="utf-8") as fh:
        return json.load(fh)
```

The underscore prefix on `_load_db` means **private** — only functions
inside this file should call it.

**Line 22** — `os.path.exists(MEMORY_FILE)` checks if the file exists.
First time you ever run the project, it does not. We return `{}` instead
of crashing with a FileNotFoundError.

**Line 24** — `open(..., "r", encoding="utf-8")` opens for reading.
`utf-8` ensures non-English names (like Anant, Rahul) are read correctly.

**Line 25** — `json.load(fh)` parses the file contents into a Python dict.
The `with` block automatically closes the file when done, even if an error occurs.

---

### Lines 28–31 – `_save_db()` (private)

```python
def _save_db(db: dict) -> None:
    with open(MEMORY_FILE, "w", encoding="utf-8") as fh:
        json.dump(db, fh, indent=2, ensure_ascii=False)
```

**`"w"` mode** — write mode. This **overwrites** the entire file each time.
We write the whole database, not just one user's record.
Simple and safe — there is no partial-write bug possible.

**`indent=2`** — makes the JSON file human-readable (pretty-printed).
Without this, the file would be one long line.

**`ensure_ascii=False`** — allows non-ASCII characters (emojis, accented letters)
to be stored as-is instead of escaped as `\u0041`.

---

### Lines 34–43 – `_default_user()` (private)

```python
def _default_user(user_id: str) -> dict:
    return {
        "profile": {
            "name": user_id,
            "preferences": "general",
        },
        "summary": "",
        "history": [],
    }
```

This is the blank template for a brand-new user.
Notice three keys:
- **profile** — who the user is (permanent, updated once)
- **summary** — compressed history text (grows slowly, replaces itself)
- **history** — raw recent messages (capped at 5 after compression)

`name` defaults to `user_id`. So if someone types `anant` as their ID,
their name starts as `"anant"` until onboarding replaces it with `"Anant"`.

`history` starts as an empty list `[]`.
An empty list is falsy in Python — used later for "is this a new user?" checks.

---

### Lines 48–64 – `load_user()` (public)

```python
def load_user(user_id: str) -> dict:
    db = _load_db()
    if user_id not in db:
        db[user_id] = _default_user(user_id)
        _save_db(db)
    return db[user_id]
```

**Line 60** — loads the whole JSON file into `db`.
**Line 61** — checks if this user_id exists as a key in `db`.
**Line 62** — if NOT found: auto-creates a default record.
**Line 63** — immediately saves to disk so the new user persists.
**Line 64** — returns only this user's data (not the whole database).

**Key design decision:** This function never returns `None`. It always returns
a valid dict. All callers can safely use `user_data["profile"]` without
checking if the dict exists. This prevents a whole class of bugs.

---

### Lines 80–94 – `update_summary()` (public)

```python
def update_summary(user_id: str, summary: str) -> None:
    db = _load_db()
    if user_id not in db:
        db[user_id] = _default_user(user_id)
    db[user_id]["summary"] = summary
    _save_db(db)
```

**Line 93** — Direct key assignment: `db[user_id]["summary"] = summary`
This replaces the entire summary string. The new summary from the LLM
completely replaces the old one.

**Why load–modify–save instead of updating just the summary field?**
JSON files have no concept of "update one field". You read the whole file,
change the value in memory, then write the whole file back.
This is a known limitation of flat-file storage. For scale, use a database.

---

### Lines 97–111 – `append_message()` (public)

```python
def append_message(user_id: str, message: dict) -> None:
    db = _load_db()
    if user_id not in db:
        db[user_id] = _default_user(user_id)
    db[user_id]["history"].append(message)
    _save_db(db)
```

**Line 110** — `.append(message)` adds to the end of the history list.
The message format is always `{"role": "user", "content": "..."}` or
`{"role": "assistant", "content": "..."}`.

**CRITICAL:** We call this function BEFORE the LLM responds.
The user's message is saved to disk immediately when they send it.
If the program crashes during the LLM call, we still have the user's message.
This is called **write-ahead persistence** — write first, process later.

---

### Lines 114–126 – `update_profile()` (public)

```python
def update_profile(user_id: str, profile: dict) -> None:
    db = _load_db()
    if user_id not in db:
        db[user_id] = _default_user(user_id)
    db[user_id]["profile"].update(profile)
    _save_db(db)
```

**Line 125** — `.update(profile)` is a Python dict method that **merges**
the incoming dict into the existing profile.
So `update_profile("anant", {"name": "Anant"})` only changes `name`,
it leaves `preferences` untouched.
This is safer than `=` assignment which would wipe the whole profile.

---

---

# FILE 3: context_manager.py
### "The MCP Engine — most important file"

---

```
Open context_manager.py
```

Say this before starting:

> "Everything before this file was plumbing — reading/writing data.
> This file is where AI engineering actually happens.
> This is where we decide WHAT the model sees."

---

### Line 20 – Import

```python
from config import RECENT_MESSAGES_LIMIT, SYSTEM_INSTRUCTION
```

We only import two things. This function does not need the API key,
model name, or file paths. It only shapes text.
Minimal imports = clear responsibilities.

---

### Lines 25–30 – `_format_profile()`

```python
def _format_profile(profile: dict) -> str:
    lines = ["User Profile:"]
    for key, value in profile.items():
        lines.append(f"  {key.capitalize()}: {value}")
    return "\n".join(lines)
```

Converts the profile dict `{"name": "Anant", "preferences": "technical"}`
into the readable text:
```
User Profile:
  Name: Anant
  Preferences: technical
```

**Line 27** — starts the list with the header `"User Profile:"`.
**Line 28** — loops over every key-value pair in the profile dict.
**Line 29** — `key.capitalize()` makes `"name"` → `"Name"` for clean display.
**Line 30** — `"\n".join(lines)` joins the list into one multi-line string.

**Why a loop instead of hardcoding `name` and `preferences`?**
If someone adds a third field to the profile (e.g. `timezone`),
this function automatically includes it without any code change.
Flexible by design.

---

### Lines 33–37 – `_format_summary()`

```python
def _format_summary(summary: str) -> str:
    if not summary:
        return "Conversation Summary:\n  (No prior summary – this may be a new conversation.)"
    return f"Conversation Summary:\n  {summary}"
```

**Line 35** — `if not summary` is True when summary is an empty string `""`.
A new user has `summary = ""`. Instead of showing a blank section,
we show an explanatory message: "this may be a new conversation."

**Why tell the model it is a new conversation?**
The model is smart enough to use this information.
It will not say "as we discussed before..." when there is no prior conversation.
Explicit instructions in context → better quality responses.

---

### Lines 40–56 – `_format_recent_messages()` — CONTEXT SLICING

```python
def _format_recent_messages(history: list) -> str:
    recent = history[-RECENT_MESSAGES_LIMIT:]
    if not recent:
        return "Recent Messages:\n  (None yet)"

    lines = ["Recent Messages:"]
    for msg in recent:
        role = msg.get("role", "unknown").capitalize()
        content = msg.get("content", "")
        lines.append(f"  [{role}]: {content}")
    return "\n".join(lines)
```

**Line 47 — THE MOST IMPORTANT LINE IN THIS FILE:**

```python
recent = history[-RECENT_MESSAGES_LIMIT:]
```

This is **context slicing**. Write this on the board.

`history[-5:]` in Python means: give me the LAST 5 elements.
If history has 3 messages → returns all 3.
If history has 100 messages → returns ONLY the last 5.

**Why only 5?**
If a user has had 100 messages and we send all 100:
- 100 messages ≈ 3,000 tokens just for history
- The LLM loses focus — older messages dilute attention on recent context
- It costs 10× more per request

After context slicing:
- 5 messages ≈ 150 tokens
- The LLM focuses on what matters NOW
- Older context is captured efficiently in the summary

**Lines 52–55** — loops through the sliced messages and formats each one:
`[User]: How does LangGraph work?`
`[Assistant]: LangGraph is a framework for...`

---

### Lines 61–90 – `build_context()` — THE MCP FUNCTION

```python
def build_context(user_data: dict, current_query: str) -> str:
    profile_block  = _format_profile(user_data.get("profile", {}))
    summary_block  = _format_summary(user_data.get("summary", ""))
    history_block  = _format_recent_messages(user_data.get("history", []))
    query_block    = f"User Query:\n  {current_query}"
    separator      = "\n" + "─" * 60 + "\n"

    context = separator.join([
        SYSTEM_INSTRUCTION,
        profile_block,
        summary_block,
        history_block,
        query_block,
    ])

    return context
```

This is the MCP (Model Context Protocol) implementation.
It assembles 5 named layers into one structured string.

**Lines 76–79** — build each layer separately using the private functions above.
Each layer is independently formatted, independently readable.

**Line 79** — `query_block` is just a plain f-string. No special function needed.

**Line 80** — `separator = "\n" + "─" * 60 + "\n"` creates a visual divider:
```
────────────────────────────────────────────────────────────
```
60 dash characters. This divider appears between every layer in the context.
It helps the LLM understand where one section ends and the next begins.
And it helps YOU debug by making the context human-readable.

**Lines 82–88** — `separator.join([...])` inserts the divider between every element.
If you print the result, you see exactly what the LLM receives:

```
You are a context-aware AI assistant...
────────────────────────────────────────────────────────────
User Profile:
  Name: Anant
  Preferences: technical
────────────────────────────────────────────────────────────
Conversation Summary:
  • User is learning LangGraph
────────────────────────────────────────────────────────────
Recent Messages:
  [User]: What are edges in LangGraph?
  [Assistant]: Edges define transitions between nodes...
────────────────────────────────────────────────────────────
User Query:
  How do I add conditional edges?
```

**This is the MCP pattern.** Five layers. Each labelled. Each with a specific purpose.
The model receives a structured briefing, not a raw chat log.

---

### Lines 109–122 – `estimate_token_count()`

```python
def estimate_token_count(text: str) -> int:
    from config import AVG_CHARS_PER_TOKEN
    return len(text) // AVG_CHARS_PER_TOKEN
```

**Line 121** — imports `AVG_CHARS_PER_TOKEN` (value: 4) lazily inside the function.
This is a style choice — the import only happens when this function is called.

**Line 122** — `len(text) // 4` is integer division.
If text is 1200 characters → estimate is 300 tokens.
This is rough. Use it for early warnings, not billing.

---

---

# FILE 4: summarizer.py
### "The memory compression engine"

---

```
Open summarizer.py
```

> "Every time a user chats, history grows. If we never shrink it,
> eventually the context overflows. The summariser solves this.
> It uses the LLM to summarise itself — brilliant and recursive."

---

### Lines 15–17 – Imports

```python
from openai import OpenAI
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, MODEL_NAME, RECENT_MESSAGES_LIMIT
```

We import `OpenAI` from the `openai` package.
Even though we are using OpenRouter (not OpenAI directly), the SDK is the same.
OpenRouter is fully OpenAI-compatible — it accepts the same request format.
We just change `base_url` when we create the client.

---

### Lines 20–47 – `_build_summarization_prompt()`

```python
def _build_summarization_prompt(messages: list, previous_summary: str) -> str:
    history_text = "\n".join(
        f"[{m['role'].capitalize()}]: {m['content']}" for m in messages
    )

    prior = (
        f"Existing summary (incorporate this):\n{previous_summary}\n\n"
        if previous_summary
        else ""
    )

    return (
        f"{prior}"
        "Summarise the following conversation into 3–5 concise bullet points. "
        "Focus on: topics discussed, decisions made, and anything the user wants "
        "to continue or remember. Be factual and brief.\n\n"
        f"Conversation to summarise:\n{history_text}"
    )
```

**Lines 31–33** — uses a **generator expression** (the part inside `"\n".join(...)`)
to format each message into `[User]: content` without building a temporary list.

**Lines 35–39** — the `prior` variable conditionally adds the old summary.
If there is an existing summary (`if previous_summary`), we include it and ask
the LLM to MERGE the new messages into it.
If this is the first compression, `prior = ""` so nothing extra is prepended.

This rolling summary design means:
- Compression 1: messages 1–10 → summary A
- Compression 2: messages 11–20 + summary A → summary B (merged)
- Compression 3: messages 21–30 + summary B → summary C (merged)

The summary always contains the essence of the ENTIRE conversation history,
no matter how many compressions have happened.

---

### Lines 50–80 – `summarize_history()` — core function

```python
def summarize_history(messages: list, previous_summary: str = "") -> str:
    old_messages = messages[:-RECENT_MESSAGES_LIMIT] if len(messages) > RECENT_MESSAGES_LIMIT else messages

    if not old_messages:
        return previous_summary

    prompt = _build_summarization_prompt(old_messages, previous_summary)

    client = OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)
    response = client.chat.completions.create(
        model=MODEL_NAME,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    new_summary = response.choices[0].message.content.strip()
    return new_summary
```

**Line 65 — CRITICAL:**

```python
old_messages = messages[:-RECENT_MESSAGES_LIMIT] if len(messages) > RECENT_MESSAGES_LIMIT else messages
```

`messages[:-5]` means: everything EXCEPT the last 5.

Example with 11 messages:
- `messages[:-5]` → messages 0–5 (the old ones to compress)
- `messages[-5:]` → messages 6–10 (kept raw in context_manager)

We only compress the old ones. The recent 5 stay as raw text.

**Line 67–68** — edge case: if `old_messages` is empty (fewer than 5 messages),
return the existing summary unchanged. Nothing to compress yet.

**Line 72** — creates an OpenAI client pointed at OpenRouter.
This client is created fresh every call (not a module-level singleton).
Simple and stateless.

**Lines 73–77** — the actual LLM call.
`max_tokens=512` limits the summary to roughly 380 words.
We do not need more than that for a bullet-point summary.

**Line 79** — `.choices[0].message.content` is the OpenAI response format.
`.strip()` removes leading/trailing whitespace.

---

### Lines 83–94 – `should_summarize()`

```python
def should_summarize(history: list, threshold: int) -> bool:
    return len(history) >= threshold
```

Single line. Checks one thing. Returns a boolean.
Called in `agent_pipeline.py` stage 3.

**Why is this a separate function instead of an inline `if`?**
Testability. You can write a unit test:
```python
assert should_summarize([1,2,3,4,5,6,7,8,9,10], 10) == True
assert should_summarize([1,2,3], 10) == False
```
Without running the whole pipeline.

---

---

# FILE 5: validator.py
### "The production quality gate"

---

```
Open validator.py
```

> "This is what separates a demo from production.
> In a demo you call the LLM and hope. In production you CHECK.
> Three checks run before every single LLM call in this system."

---

### Lines 19–20 – Imports

```python
from context_manager import estimate_token_count
from config import MAX_CONTEXT_TOKENS
```

The validator imports `estimate_token_count` from `context_manager.py`.
This is a deliberate dependency: validation needs to know context size,
and the context module owns the token estimation logic.
We do not copy that logic — we import it.

---

### Lines 25–45 – `_check_context_size()` — Check 1

```python
def _check_context_size(context: str) -> list[str]:
    issues = []
    estimated = estimate_token_count(context)

    if estimated > MAX_CONTEXT_TOKENS:
        issues.append(
            f"[SIZE] Context is too large: ~{estimated} tokens "
            f"(limit {MAX_CONTEXT_TOKENS}). Consider summarising more aggressively."
        )
    elif estimated > MAX_CONTEXT_TOKENS * 0.85:
        issues.append(
            f"[SIZE] Context is approaching the limit: ~{estimated} tokens "
            f"({MAX_CONTEXT_TOKENS * 0.85:.0f} soft threshold)."
        )

    return issues
```

**Line 31** — starts with an empty list. Issues are collected, not raised.
**Line 32** — estimates token count using the shared function.

**Two thresholds:**
- `> MAX_CONTEXT_TOKENS` (4000) → HARD limit: do not call the LLM.
- `> 4000 * 0.85 = 3400` → SOFT warning: you are getting close.

`0.85` is 85% of the limit. The soft warning gives you time to react
before you hit the hard limit.

**Why `list[str]` return type?**
Every check function returns a list of strings.
The master `validate_context()` function collects all lists and combines them.
This means new checks can be added without changing the return structure.

---

### Lines 48–71 – `_check_missing_memory()` — Check 2

```python
def _check_missing_memory(user_data: dict) -> list[str]:
    issues = []
    profile = user_data.get("profile", {})

    if not profile:
        issues.append("[MEMORY] User profile is completely missing.")
    else:
        if not profile.get("name"):
            issues.append("[MEMORY] Profile is missing the 'name' field.")
        if not profile.get("preferences"):
            issues.append("[MEMORY] Profile is missing the 'preferences' field.")

    if not user_data.get("summary"):
        issues.append(
            "[MEMORY] No conversation summary found. "
            "This is expected for new users but may indicate a summarisation failure for returning users."
        )

    return issues
```

**Line 55** — `user_data.get("profile", {})` — if profile key is somehow missing,
use an empty dict as default. Never crashes.

**Line 57** — `if not profile` — an empty dict `{}` is falsy in Python.
So this catches both "key missing" and "key exists but is empty".

**Line 65** — `if not user_data.get("summary")` — empty string `""` is also falsy.
New users will always trigger this warning. That is expected.
But a returning user with no summary might indicate a bug in the summariser.
The message is context-aware: it explains both scenarios.

---

### Lines 74–107 – `_check_relevance()` — Check 3

```python
def _check_relevance(context: str, query: str) -> list[str]:
    issues = []

    context_body = context.split("User Query:")[0].lower()

    stop_words = {"what", "when", "where", "which", "with", "from", "that",
                  "this", "have", "been", "will", "your", "about", "tell"}
    keywords = [
        word for word in query.lower().split()
        if len(word) >= 4 and word not in stop_words
    ]

    if not keywords:
        return issues

    found = any(kw in context_body for kw in keywords)
    if not found:
        issues.append(
            f"[RELEVANCE] None of the query keywords {keywords[:5]} were found in the "
            "context memory. The agent may lack relevant background for this question."
        )

    return issues
```

**Line 87** — `context.split("User Query:")[0]`
Splits the context at the phrase "User Query:" and takes the FIRST part.
This means we only search the memory layers (profile, summary, recent),
NOT the query itself. We are checking if the query topic already exists
in the agent's memory.

**Lines 90–95** — builds a keyword list from the query:
- `len(word) >= 4` filters out short words (`is`, `the`, `it`)
- `word not in stop_words` filters common query words (`what`, `tell`)

Example: query `"What is LangGraph?"` → keywords: `["langgraph"]`
Example: query `"How do I do it?"` → keywords: `[]` (too short/stop words)

**Line 100** — `any(kw in context_body for kw in keywords)`
Returns True if ANY keyword appears anywhere in the memory layers.
Uses Python's `any()` — stops as soon as one match is found (efficient).

**When does this trigger?**
If user asks "How does Redis work?" but their profile/summary/history
has no mention of "redis" → warning fires. The agent might give
a generic answer because it has no background on this topic.

---

### Lines 112–143 – `validate_context()` — master function

```python
def validate_context(context: str, user_data: dict, query: str = "") -> dict:
    issues: list[str] = []

    issues.extend(_check_context_size(context))
    issues.extend(_check_missing_memory(user_data))

    if query:
        issues.extend(_check_relevance(context, query))

    has_error = any("[SIZE] Context is too large" in i for i in issues)

    return {
        "valid": not has_error,
        "issues": issues,
        "token_estimate": estimate_token_count(context),
    }
```

**Line 128** — starts with an empty issues list.
**Lines 130–131** — calls both checks and extends the list with any issues found.
`.extend()` adds all elements from one list to another.

**Line 133** — `if query:` — the relevance check is optional. If no query is
passed (empty string), we skip it.

**Line 137 — key design decision:**

```python
has_error = any("[SIZE] Context is too large" in i for i in issues)
```

Not all issues are equal. Only the hard size limit is a TRUE error that
blocks the LLM call. Missing summary on a new user is a warning, not an error.

`any(...)` returns True if at least one issue contains `"[SIZE] Context is too large"`.

**Lines 139–143** — returns a dict with:
- `"valid"`: True = proceed with LLM call. False = abort.
- `"issues"`: list of warning/error strings for printing.
- `"token_estimate"`: the number, displayed in pipeline logs.

**Why return a dict instead of raising an exception?**
The validator DETECTS problems. The PIPELINE decides what to do about them.
Policy (abort/warn/proceed) belongs in the caller, not in the checker.
This is **separation of concerns** — a core engineering principle.

---

---

# FILE 6: agent_pipeline.py
### "The conductor — 7 stages"

---

```
Open agent_pipeline.py
```

> "This file does not do any actual work itself.
> It calls other files in the right order.
> Think of it as a recipe — it tells you what to do and when,
> but the actual cooking happens in the ingredient files."

---

### Lines 19–30 – Imports

```python
from openai import OpenAI
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, HISTORY_THRESHOLD, MODEL_NAME
from context_manager import build_context, get_recent_messages
from memory_store import (
    append_message,
    load_user,
    save_user,
    update_summary,
)
from summarizer import should_summarize, summarize_history
from validator import validate_context
```

The import block tells you everything this file depends on.
Reading it top to bottom, you see the full dependency tree:
OpenAI SDK → config → context_manager → memory_store → summarizer → validator.

Every function imported here is called in exactly one stage of the pipeline.

---

### Lines 35–37 – Stage 1

```python
def _stage_load_memory(user_id: str) -> dict:
    """Stage 1: Load (or create) the user's memory record."""
    return load_user(user_id)
```

One line. Just delegates to `memory_store.load_user()`.
**Why wrap it?** Naming. When you read `run_pipeline()`, seeing
`_stage_load_memory()` is self-documenting. You know this is Stage 1,
not a raw function call.

---

### Lines 40–45 – Stage 2

```python
def _stage_append_user_message(user_id: str, user_data: dict, query: str) -> dict:
    message = {"role": "user", "content": query}
    user_data["history"].append(message)
    append_message(user_id, message)
    return user_data
```

**Line 42** — builds the message dict. `role` is always `"user"` here.
**Line 43** — appends to the IN-MEMORY copy of history (the Python dict).
**Line 44** — ALSO writes to disk via `append_message()`.

Two writes happen:
1. To the in-memory `user_data` dict (used by the rest of this pipeline turn)
2. To disk (persists even if the program crashes after this line)

Both must happen. If you only update memory, a crash loses the message.
If you only write to disk, the rest of the pipeline sees stale data.

---

### Lines 48–74 – Stage 3 (SUMMARISATION)

```python
def _stage_maybe_summarize(user_id: str, user_data: dict) -> dict:
    if should_summarize(user_data["history"], HISTORY_THRESHOLD):
        print("\n  [Pipeline] History threshold reached – compressing memory…")

        new_summary = summarize_history(
            messages=user_data["history"],
            previous_summary=user_data.get("summary", ""),
        )

        from config import RECENT_MESSAGES_LIMIT
        recent = get_recent_messages(user_data["history"])

        user_data["summary"] = new_summary
        user_data["history"] = recent

        update_summary(user_id, new_summary)
        save_user(user_id, user_data)

        print(f"  [Pipeline] New summary saved ({len(new_summary)} chars).")

    return user_data
```

**Line 55** — `should_summarize(...)` returns True if `len(history) >= 10`.
The whole compression block only runs when needed.

**Lines 58–61** — calls `summarize_history()` with the full history and
the previous summary. The LLM produces a new merged summary.

**Line 63** — `from config import RECENT_MESSAGES_LIMIT` — local import.
Slightly unusual placement, but harmless. Gets the value 5.

**Line 64** — `get_recent_messages()` returns `history[-5:]` (last 5 messages).

**Lines 66–67 — THE PRUNING:**
```python
user_data["summary"] = new_summary   # replace old summary
user_data["history"] = recent        # DISCARD messages 0 to (len-5)
```

After these two lines, old messages no longer exist in memory.
They have been compressed into `new_summary`.

**Lines 69–70** — persist both changes to disk.
`update_summary` updates only the summary field.
`save_user` saves the whole record including the pruned history.

---

### Lines 77–79 – Stage 4

```python
def _stage_build_context(user_data: dict, query: str) -> str:
    """Stage 4: Assemble the structured MCP context string."""
    return build_context(user_data, query)
```

One line. Delegates to `context_manager.build_context()`.
Returns the fully assembled MCP prompt string.

---

### Lines 82–100 – Stage 5 (VALIDATION)

```python
def _stage_validate(context: str, user_data: dict, query: str) -> bool:
    result = validate_context(context, user_data, query)

    print(f"\n  [Validator] Token estimate: ~{result['token_estimate']} tokens")

    if result["issues"]:
        print("  [Validator] Issues detected:")
        for issue in result["issues"]:
            print(f"    ⚠  {issue}")
    else:
        print("  [Validator] Context looks healthy ✓")

    return result["valid"]
```

**Line 89** — calls `validate_context()` from `validator.py`.
Gets back the dict `{valid, issues, token_estimate}`.

**Line 91** — always prints the token estimate. Every request. Visible to student.
This teaches observability — you should always know how large your context is.

**Lines 93–98** — prints any warnings with a `⚠` symbol.

**Line 100** — returns `result["valid"]` as a boolean.
The pipeline uses this to decide whether to call the LLM or abort.

---

### Lines 103–116 – Stage 6 (LLM CALL)

```python
def _stage_llm_call(context: str) -> str:
    client = OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)
    response = client.chat.completions.create(
        model=MODEL_NAME,
        max_tokens=1024,
        messages=[{"role": "user", "content": context}],
    )
    return response.choices[0].message.content.strip()
```

**Line 110** — creates the OpenAI client with OpenRouter credentials.
`base_url=OPENROUTER_BASE_URL` is what makes it use OpenRouter instead of OpenAI.

**Line 111** — `client.chat.completions.create(...)` is the standard OpenAI SDK call.

**Line 114** — `messages=[{"role": "user", "content": context}]`
The ENTIRE MCP context (all 5 layers) is passed as a single user message.
The model receives the structured briefing exactly as designed in `context_manager.py`.

**`max_tokens=1024`** — limits the response to ~768 words. Enough for most answers.

**Line 116** — `.choices[0].message.content` — OpenAI SDK response format.
The model can return multiple choices (if `n > 1`), but we only want the first.
`.strip()` removes whitespace that some models pad their responses with.

---

### Lines 119–123 – Stage 7

```python
def _stage_store_response(user_id: str, user_data: dict, reply: str) -> None:
    message = {"role": "assistant", "content": reply}
    user_data["history"].append(message)
    append_message(user_id, message)
```

Mirror of Stage 2 but for the assistant's response.
Role is `"assistant"` (not `"user"`).
Again: both in-memory and on-disk updates happen simultaneously.

After Stage 7, the history on disk looks like:
```json
[
  {"role": "user",      "content": "How does LangGraph work?"},
  {"role": "assistant", "content": "LangGraph is a framework..."}
]
```
Ready for the next turn.

---

### Lines 128–171 – `run_pipeline()` — THE MASTER FUNCTION

```python
def run_pipeline(user_id: str, query: str) -> str:
    print("\n" + "═" * 60)
    print(f"  [Pipeline] User: {user_id}  |  Query: {query[:60]}…"
          if len(query) > 60 else f"  [Pipeline] User: {user_id}  |  Query: {query}")

    # 1 – Load memory
    user_data = _stage_load_memory(user_id)

    # 2 – Append user message
    user_data = _stage_append_user_message(user_id, user_data, query)

    # 3 – Summarisation check
    user_data = _stage_maybe_summarize(user_id, user_data)

    # 4 – Build MCP context
    context = _stage_build_context(user_data, query)

    # 5 – Validate context
    context_ok = _stage_validate(context, user_data, query)
    if not context_ok:
        print("  [Pipeline] ⛔ Context validation failed – aborting LLM call.")
        return "I'm sorry, I ran into a context issue. Please try again."

    # 6 – LLM call
    print("  [Pipeline] Calling LLM…")
    reply = _stage_llm_call(context)

    # 7 – Store response
    _stage_store_response(user_id, user_data, reply)

    print("  [Pipeline] Turn complete.")
    print("═" * 60)

    return reply
```

**Lines 139–141** — visual header printed before each request.
`query[:60]` truncates long queries to 60 chars for display.
The `if len(query) > 60` on the same line chooses between two print formats.

**Lines 143–166** — each stage runs in sequence with a comment label.
Reading this function alone, you understand the entire system flow.

**Lines 157–159 — THE ABORT PATH:**
```python
if not context_ok:
    print("  [Pipeline] ⛔ Context validation failed – aborting LLM call.")
    return "I'm sorry, I ran into a context issue. Please try again."
```

If `_stage_validate()` returns `False`, we return immediately.
No LLM call happens. Zero tokens spent. User sees a graceful message.
The pipeline short-circuits cleanly.

**Line 171** — returns the `reply` string.
This goes all the way back to `main.py` which prints it as `Agent: {reply}`.

---

---

# FILE 7: main.py
### "The entry point — UI only"

---

```
Open main.py
```

> "This file has one rule: no business logic.
> It only asks questions and prints answers.
> All intelligence is in the other files."

---

### Lines 18–21 – Imports

```python
import sys

from agent_pipeline import run_pipeline
from memory_store import load_user, update_profile
```

**`import sys`** — for `sys.exit(0)` to quit cleanly.
**`run_pipeline`** — the single function that does everything.
**`load_user, update_profile`** — needed for onboarding and the refresh at line 112.

---

### Lines 26–42 – `_greet_user()`

```python
def _greet_user(user_id: str, user_data: dict) -> None:
    name        = user_data["profile"].get("name", user_id)
    has_history = bool(user_data["history"] or user_data["summary"])

    if has_history:
        summary_snippet = user_data.get("summary", "")
        if summary_snippet:
            print(f"\nWelcome back, {name}!")
            print(f"  Last time we spoke about: {summary_snippet[:120]}…"
                  if len(summary_snippet) > 120 else
                  f"  Last session summary: {summary_snippet}")
        else:
            print(f"\nWelcome back, {name}! Continuing our conversation.")
    else:
        print(f"\nHello, {name}! I'm your context-aware AI assistant.")
        print("  I'll remember you across sessions and get smarter over time.")
```

**Line 29** — `bool(user_data["history"] or user_data["summary"])`
True if history list is non-empty OR summary is non-empty string.
False if BOTH are empty → brand new user.

**Line 35** — `summary_snippet[:120]` — truncates to 120 chars for display.
The full summary might be 500 chars. We only preview it in the greeting.

**Two different welcome messages:**
- Has history + summary → `"Welcome back, {name}! Last session: ..."`
- Has history but no summary yet → `"Welcome back, Continuing our conversation."`
- No history, no summary → `"Hello! I'll remember you..."` (new user)

---

### Lines 45–68 – `_onboard_new_user()`

```python
def _onboard_new_user(user_id: str, user_data: dict) -> dict:
    if user_data["history"] or user_data["summary"]:
        return user_data   # returning user – skip onboarding

    print("\nLooks like you're new here. Let me set up your profile.")

    name = input("  What should I call you? (press Enter to keep your ID): ").strip()
    if not name:
        name = user_id

    prefs = input(
        "  Response style preference – technical / casual / detailed [technical]: "
    ).strip().lower() or "technical"

    update_profile(user_id, {"name": name, "preferences": prefs})
    user_data["profile"]["name"]        = name
    user_data["profile"]["preferences"] = prefs

    print(f"  Profile saved: {name} ({prefs} mode).")
    return user_data
```

**Line 50** — early return for returning users. Skips the whole function.
No repeated onboarding for users who already have data.

**Line 56** — `input().strip()` gets the typed name and removes surrounding spaces.

**Line 57–58** — if they pressed Enter without typing, use the user_id as name.
The `or` operator: `"" or "fallback"` → returns `"fallback"` (empty string is falsy).

**Line 61** — `... .strip().lower() or "technical"` — same pattern.
If they press Enter, default is `"technical"`.
`.lower()` prevents `"Technical"` and `"technical"` being stored differently.

**Lines 63–65** — saves TWICE:
- `update_profile()` → persists to disk
- Direct assignment → updates the in-memory `user_data` dict used this session

---

### Lines 73–112 – `main()` — the loop

```python
def main() -> None:
    print("╔══════════════════════════════════════════════════════════╗")
    ...

    user_id = input("\nEnter your user ID (or press Enter for 'demo_user'): ").strip()
    if not user_id:
        user_id = "demo_user"

    user_data = load_user(user_id)
    user_data = _onboard_new_user(user_id, user_data)
    _greet_user(user_id, user_data)

    print("\nType your message below. Type 'exit' to quit.\n")

    while True:
        try:
            query = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            sys.exit(0)

        if not query:
            continue

        if query.lower() in {"exit", "quit", "bye"}:
            ...
            sys.exit(0)

        reply = run_pipeline(user_id, query)
        print(f"\nAgent: {reply}\n")

        user_data = load_user(user_id)
```

**Lines 80–81** — `or` default pattern again: empty input → `"demo_user"`.

**Lines 84–86** — three steps before the loop:
load → onboard (if new) → greet.
These happen ONCE per session.

**Lines 92–96** — `try/except (KeyboardInterrupt, EOFError)`:
- `KeyboardInterrupt`: user pressed Ctrl+C
- `EOFError`: piped input reached end of file (useful in testing)
Both are caught gracefully instead of printing a Python traceback.

**Line 98** — `if not query: continue` — if user pressed Enter with no text,
loop back and ask again. Do not call the pipeline with an empty string.

**Line 107** — `reply = run_pipeline(user_id, query)` — this single line
triggers all 7 stages. Everything else in `main.py` is just setup and display.

**Line 112 — THE REFRESH:**
```python
user_data = load_user(user_id)
```
After the pipeline runs, `user_data` may be stale.
If compression happened (Stage 3), the pipeline rewrote the JSON file.
But our local `user_data` variable still has the old data from before the turn.
By reloading from disk here, we guarantee `_greet_user` always shows
fresh data if called again (e.g. after a `/stats` command).

---

### Line 115–116 – Entry guard

```python
if __name__ == "__main__":
    main()
```

Standard Python pattern. This runs `main()` only when you execute the file
directly (`python main.py`). If another file imports `main.py`, `main()`
does not auto-run.

---

---

# HOW IT ALL CONNECTS — The Full Turn

When you type `"How do LangGraph edges work?"`, here is every line that executes:

```
main.py:107       → run_pipeline("anant", "How do LangGraph edges work?")

agent_pipeline.py:144  → _stage_load_memory("anant")
  memory_store.py:60   →   _load_db()  [reads JSON from disk]
  memory_store.py:64   →   returns user_data dict

agent_pipeline.py:147  → _stage_append_user_message(...)
  memory_store.py:107  →   _load_db()
  memory_store.py:110  →   db["anant"]["history"].append(message)
  memory_store.py:111  →   _save_db(db)  [writes JSON to disk]

agent_pipeline.py:150  → _stage_maybe_summarize(...)
  summarizer.py:94     →   should_summarize(history, 10)
                            → False (only 3 messages) → skip

agent_pipeline.py:153  → _stage_build_context(user_data, query)
  context_manager.py:76 →   _format_profile(...)
  context_manager.py:77 →   _format_summary(...)
  context_manager.py:78 →   _format_recent_messages(...)  ← SLICING HAPPENS HERE
  context_manager.py:47 →   history[-5:]
  context_manager.py:82 →   separator.join([5 blocks]) → context string

agent_pipeline.py:156  → _stage_validate(context, user_data, query)
  validator.py:130     →   _check_context_size(context)  → []
  validator.py:131     →   _check_missing_memory(user_data)
                            → [⚠ no summary yet]
  validator.py:134     →   _check_relevance(context, query)
                            → [] (LangGraph is mentioned in context)
  validator.py:140     →   returns {valid: True, issues: [...], tokens: 95}

agent_pipeline.py:163  → _stage_llm_call(context)
  openai SDK           →   POST https://openrouter.ai/api/v1/chat/completions
  [LLM CALL HAPPENS]   →   Claude receives the structured context
                       →   returns response text

agent_pipeline.py:166  → _stage_store_response(...)
  memory_store.py:121  →   db["anant"]["history"].append(assistant message)
  memory_store.py:111  →   _save_db(db)

agent_pipeline.py:171  → returns reply string

main.py:109         → print(f"\nAgent: {reply}\n")
main.py:112         → user_data = load_user("anant")  [refresh]
```

---

---

# THE LANGSMITH QUESTION

LangSmith does NOT auto-trace this project. You have to add it.

What is LangSmith?
An observability dashboard. Instead of reading `print()` statements in the terminal,
you see a visual trace on a website: each stage as a box with inputs, outputs, latency.

What you would need to add to THIS project:

**Step 1** — install:
```bash
pip install langsmith
```

**Step 2** — add to `.env`:
```
LANGCHAIN_API_KEY=your_key_here
LANGCHAIN_PROJECT=mcp-capstone
LANGCHAIN_TRACING_V2=true
```

**Step 3** — decorate functions in `agent_pipeline.py`:
```python
from langsmith import traceable

@traceable(name="Agent Pipeline", run_type="chain")
def run_pipeline(user_id, query):
    ...

@traceable(name="LLM Call", run_type="llm")
def _stage_llm_call(context):
    ...

@traceable(name="Validator", run_type="chain")
def _stage_validate(context, user_data, query):
    ...
```

`@traceable` is a Python **decorator**. It wraps the function.
When the function runs, LangSmith records:
- The input arguments
- The return value
- How long it took
- Errors if any

The `production_agent` project already has all of this wired up.
The `mcp_capstone` (this project) focuses on context engineering,
not observability — they teach different things.

---

---

# FINAL SUMMARY FOR STUDENTS

```
config.py        → where numbers live. Change here, change everywhere.
memory_store.py  → the only file that touches disk.
                   Three keys: profile, summary, history.
context_manager  → the MCP engine. Five layers. One clean string.
                   Line 47: history[-5:] is context slicing.
summarizer.py    → LLM compresses itself. Rolling summary never grows old.
                   Line 65: messages[:-5] = everything except recent.
validator.py     → three checks before every LLM call.
                   Returns dict, not exception. Policy stays in pipeline.
agent_pipeline   → 7 stages. Each testable. Each named.
                   Line 157: abort path if validation fails.
main.py          → no business logic. Just asks, prints, loops.
                   Line 107: one line calls the whole system.
```

The design principle connecting all of it:

> "AI systems don't fail because models are weak.
>  They fail because context is poorly managed."

You now control the context.
