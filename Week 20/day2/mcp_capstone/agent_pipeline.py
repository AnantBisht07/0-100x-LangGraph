"""
agent_pipeline.py – Orchestrates the full MCP agent turn.

Pipeline stages (in order):
  1. Load memory          – fetch profile + summary + history from disk
  2. Append user message  – persist the raw input immediately
  3. Summarisation check  – compress history if it exceeds the threshold
  4. Build MCP context    – assemble the structured prompt
  5. Validate context     – run quality checks and print any warnings
  6. LLM call             – send context to Claude and get a response
  7. Store response       – append the assistant turn to history

Each stage is a separate function so it can be unit-tested independently.

"AI systems don't fail because models are weak.
 They fail because context is poorly managed."
"""

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


# ── Stage helpers ─────────────────────────────────────────────────────────────

def _stage_load_memory(user_id: str) -> dict:
    """Stage 1: Load (or create) the user's memory record."""
    return load_user(user_id)


def _stage_append_user_message(user_id: str, user_data: dict, query: str) -> dict:
    """Stage 2: Add the incoming user turn to history (in-memory and on disk)."""
    message = {"role": "user", "content": query}
    user_data["history"].append(message)
    append_message(user_id, message)
    return user_data


def _stage_maybe_summarize(user_id: str, user_data: dict) -> dict:
    """
    Stage 3: Compress history if it has grown past the threshold.

    After compression the old messages are pruned; only the recent slice is
    kept in raw form.  The new summary is saved to disk.
    """
    if should_summarize(user_data["history"], HISTORY_THRESHOLD):
        print("\n  [Pipeline] History threshold reached – compressing memory…")

        new_summary = summarize_history(
            messages=user_data["history"],
            previous_summary=user_data.get("summary", ""),
        )

        from config import RECENT_MESSAGES_LIMIT
        recent = get_recent_messages(user_data["history"])

        user_data["summary"] = new_summary
        user_data["history"] = recent          # keep only the recent slice

        update_summary(user_id, new_summary)
        save_user(user_id, user_data)          # persist pruned history too

        print(f"  [Pipeline] New summary saved ({len(new_summary)} chars).")

    return user_data


def _stage_build_context(user_data: dict, query: str) -> str:
    """Stage 4: Assemble the structured MCP context string."""
    return build_context(user_data, query)


def _stage_validate(context: str, user_data: dict, query: str) -> bool:
    """
    Stage 5: Run the validation layer.

    Prints any issues to stdout.  Returns False only if a hard error is found
    (e.g. context is over the token limit).
    """
    result = validate_context(context, user_data, query)

    print(f"\n  [Validator] Token estimate: ~{result['token_estimate']} tokens")

    if result["issues"]:
        print("  [Validator] Issues detected:")
        for issue in result["issues"]:
            print(f"    ⚠  {issue}")
    else:
        print("  [Validator] Context looks healthy ✓")

    return result["valid"]


def _stage_llm_call(context: str) -> str:
    """
    Stage 6: Send the assembled context to Claude and return the reply.

    The entire MCP context is passed as a single user message so the model
    sees the structured layers exactly as designed.
    """
    client = OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)
    response = client.chat.completions.create(
        model=MODEL_NAME,
        max_tokens=1024,
        messages=[{"role": "user", "content": context}],
    )
    return response.choices[0].message.content.strip()


def _stage_store_response(user_id: str, user_data: dict, reply: str) -> None:
    """Stage 7: Persist the assistant's reply so it becomes part of history."""
    message = {"role": "assistant", "content": reply}
    user_data["history"].append(message)
    append_message(user_id, message)


# ── Public entry point ────────────────────────────────────────────────────────

def run_pipeline(user_id: str, query: str) -> str:
    """
    Execute a full agent turn for the given user and query.

    Args:
        user_id: Unique identifier for the user.
        query:   The user's current message.

    Returns:
        The assistant's response string.
    """
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
