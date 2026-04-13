"""
summarizer.py – Automatic memory compression via LLM.

When the conversation history exceeds HISTORY_THRESHOLD, this module:
  1. Takes the *older* messages (everything except the most recent slice).
  2. Calls the LLM to produce a concise bullet-point summary.
  3. Returns the new summary so the pipeline can persist it and prune history.

This is what keeps the context window lean over long sessions.

"AI systems don't fail because models are weak.
 They fail because context is poorly managed."
"""

from openai import OpenAI

from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, MODEL_NAME, RECENT_MESSAGES_LIMIT


def _build_summarization_prompt(messages: list, previous_summary: str) -> str:
    """
    Build the prompt sent to the LLM for compression.

    Args:
        messages:         The older message dicts to compress.
        previous_summary: Any summary already stored (may be empty).

    Returns:
        Plain-text prompt string.
    """
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


def summarize_history(messages: list, previous_summary: str = "") -> str:
    """
    Compress older conversation messages into a short textual summary.

    Only messages *beyond* the recent-message slice are compressed; the slice
    itself stays in raw form so the LLM still has verbatim recent context.

    Args:
        messages:         Full raw history list (all turns).
        previous_summary: The summary already stored for this user.

    Returns:
        New summary string that replaces the old one.
    """
    # Determine which messages are "old" (will be compressed)
    old_messages = messages[:-RECENT_MESSAGES_LIMIT] if len(messages) > RECENT_MESSAGES_LIMIT else messages

    if not old_messages:
        return previous_summary  # nothing to compress yet

    prompt = _build_summarization_prompt(old_messages, previous_summary)

    client = OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)
    response = client.chat.completions.create(
        model=MODEL_NAME,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    new_summary = response.choices[0].message.content.strip()
    return new_summary


def should_summarize(history: list, threshold: int) -> bool:
    """
    Check whether history is long enough to trigger compression.

    Args:
        history:   Current raw history list.
        threshold: Maximum number of messages before compression fires.

    Returns:
        True if compression should run now.
    """
    return len(history) >= threshold
