"""
context_manager.py – Core MCP (Model Context Protocol) engine.

Responsible for assembling the structured prompt that is actually sent to the
LLM.  Context is built in four distinct layers:

  1. System Instruction   – static role definition
  2. User Profile         – persistent facts about this user
  3. Conversation Summary – compressed older history
  4. Recent Messages      – last N raw turns (context slicing)
  5. Current Query        – the live user input

Keeping these layers separate makes it easy to swap, resize, or debug any
individual piece without touching the rest of the pipeline.

"AI systems don't fail because models are weak.
 They fail because context is poorly managed."
"""

from config import RECENT_MESSAGES_LIMIT, SYSTEM_INSTRUCTION


# ── Layer builders ────────────────────────────────────────────────────────────

def _format_profile(profile: dict) -> str:
    """Render the user profile block."""
    lines = ["User Profile:"]
    for key, value in profile.items():
        lines.append(f"  {key.capitalize()}: {value}")
    return "\n".join(lines)


def _format_summary(summary: str) -> str:
    """Render the compressed history block (may be empty)."""
    if not summary:
        return "Conversation Summary:\n  (No prior summary – this may be a new conversation.)"
    return f"Conversation Summary:\n  {summary}"


def _format_recent_messages(history: list) -> str:
    """
    Context slicing: keep only the most recent messages.

    Older messages beyond RECENT_MESSAGES_LIMIT are intentionally excluded;
    their gist is captured in the summary layer instead.
    """
    recent = history[-RECENT_MESSAGES_LIMIT:]
    if not recent:
        return "Recent Messages:\n  (None yet)"

    lines = ["Recent Messages:"]
    for msg in recent:
        role = msg.get("role", "unknown").capitalize()
        content = msg.get("content", "")
        lines.append(f"  [{role}]: {content}")
    return "\n".join(lines)


# ── Public API ────────────────────────────────────────────────────────────────

def build_context(user_data: dict, current_query: str) -> str:
    """
    Assemble the full structured MCP context string.

    This is the single function that transforms raw memory into the exact text
    sent to the LLM.  Every layer is explicit and human-readable so problems
    are easy to spot during debugging.

    Args:
        user_data:     The user's full memory record (profile, summary, history).
        current_query: The live message typed by the user this turn.

    Returns:
        A multi-section string ready to be used as the LLM prompt body.
    """
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


def get_recent_messages(history: list) -> list:
    """
    Return only the sliced portion of history used in context.

    Useful for callers that need the list form (e.g. for the Anthropic messages
    API rather than a plain text prompt).

    Args:
        history: Full raw history list.

    Returns:
        Last RECENT_MESSAGES_LIMIT entries.
    """
    return history[-RECENT_MESSAGES_LIMIT:]


def estimate_token_count(text: str) -> int:
    """
    Rough token count estimate (characters ÷ AVG_CHARS_PER_TOKEN).

    Not exact – use only for early-warning checks in the validator.

    Args:
        text: Any string (usually the assembled context).

    Returns:
        Integer approximation of token count.
    """
    from config import AVG_CHARS_PER_TOKEN
    return len(text) // AVG_CHARS_PER_TOKEN
