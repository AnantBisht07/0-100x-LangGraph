"""
context_manager.py — Model Context Protocol (MCP) implementation.

THIS IS THE MOST IMPORTANT MODULE IN THE PROJECT.

Problem this solves:
    Blindly sending the entire conversation history to the LLM causes:
      - Token explosion  → higher cost
      - Slower responses → worse UX
      - Irrelevant noise → more hallucinations

MCP Solution — structured context with three layers:
    1. PROFILE   → persistent user info (always included, small)
    2. SUMMARY   → compressed old conversation (medium, auto-generated)
    3. RECENT    → last N messages (last 3–5, always fresh)

Think of it as packing a suitcase:
    You don't carry your entire house when traveling.
    You carry only what's needed for the trip.
    MCP = your packing strategy.
"""

import config
import memory_store
from openai import OpenAI

# OpenRouter is OpenAI-compatible — only the base_url and api_key differ
_client = OpenAI(
    api_key  = config.OPENROUTER_API_KEY,
    base_url = config.OPENROUTER_BASE_URL,
    default_headers = {
        "HTTP-Referer": config.OPENROUTER_SITE_URL,
        "X-Title":      config.OPENROUTER_APP_NAME,
    },
)

_CONTEXT_TEMPLATE = """\
=== SYSTEM ===
You are a helpful AI assistant. Be clear, concise, and accurate.
Adapt your tone to the user's preference (technical vs casual).

=== USER PROFILE ===
Name:        {name}
Preferences: {preferences}
Member since: {created_at}

=== CONVERSATION SUMMARY ===
{summary}

=== RECENT MESSAGES ===
{recent_messages}

=== TOOL RESULTS ===
{tool_results}

=== CURRENT QUERY ===
{query}
"""


class ContextManager:
    """
    Builds structured, token-efficient context using MCP principles.

    Usage:
        ctx = ContextManager()
        prompt = ctx.build_context(user_id, messages, query, tool_result)
    """

    def __init__(self):
        self.max_recent   = config.MAX_RECENT_MESSAGES
        self.threshold    = config.SUMMARY_THRESHOLD

    # ── Public API ────────────────────────────────────────────────────────────

    def build_context(
        self,
        user_id:     str,
        messages:    list[dict],
        query:       str,
        tool_result: str | None = None,
    ) -> str:
        """
        MCP core function — builds the structured context string.

        Steps:
          1. Load persistent user profile
          2. Slice messages: compress old → summary, keep recent
          3. Inject profile + summary + recent + tool result + query
          4. Return one structured string ready for the LLM

        Args:
            user_id:     Unique user identifier.
            messages:    Full conversation history as list of
                         {"role": "user"/"assistant", "content": "..."}.
            query:       The current user input.
            tool_result: Optional output from a tool call.

        Returns:
            Structured context string (the MCP-formatted prompt).
        """
        profile = memory_store.load_memory(user_id)

        # Auto-compress if history is too long
        messages = self._maybe_compress(user_id, messages, profile)

        # Slice: keep only recent N messages
        recent = messages[-self.max_recent:]

        # Format each layer
        recent_text = self._format_messages(recent)
        summary     = profile.get("summary", "") or "No prior summary yet."
        tool_text   = tool_result if tool_result else "No tool was called."

        return _CONTEXT_TEMPLATE.format(
            name          = profile.get("name", user_id),
            preferences   = profile.get("preferences", "general"),
            created_at    = profile.get("created_at", "unknown"),
            summary       = summary,
            recent_messages = recent_text,
            tool_results  = tool_text,
            query         = query,
        )

    def get_token_estimate(self, context: str) -> int:
        """Rough token estimate: ~4 chars per token."""
        return len(context) // 4

    # ── Private Helpers ───────────────────────────────────────────────────────

    def _maybe_compress(
        self,
        user_id:  str,
        messages: list[dict],
        profile:  dict,
    ) -> list[dict]:
        """
        Context Slicing — compress old messages into a summary.

        If the conversation exceeds SUMMARY_THRESHOLD messages:
          - Take everything except the last MAX_RECENT_MESSAGES
          - Summarize them using the LLM
          - Store summary in memory_store
          - Return only the recent messages

        This keeps context tight without losing important history.
        """
        if len(messages) <= self.threshold:
            return messages

        older_messages  = messages[:-self.max_recent]
        recent_messages = messages[-self.max_recent:]

        # Build existing summary to chain compressions
        existing_summary = profile.get("summary", "")

        new_summary = self._summarize(older_messages, existing_summary)
        memory_store.update_summary(user_id, new_summary)

        return recent_messages

    def _summarize(self, messages: list[dict], existing: str) -> str:
        """
        Use the LLM to compress old messages into a concise summary.

        In production this could be a smaller/cheaper model to save cost.
        """
        if not messages:
            return existing

        conversation_text = self._format_messages(messages)

        prompt = (
            "You are a conversation summarizer. "
            "Given the conversation history below, produce a concise "
            "2–3 sentence summary capturing the key topics and outcomes.\n\n"
            f"EXISTING SUMMARY:\n{existing}\n\n"
            f"NEW MESSAGES TO INCLUDE:\n{conversation_text}\n\n"
            "UPDATED SUMMARY:"
        )

        try:
            response = _client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=150,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            # Graceful fallback — never crash the pipeline over summarization
            return existing or "Conversation history available."

    @staticmethod
    def _format_messages(messages: list[dict]) -> str:
        """Format message list into readable text for the context block."""
        if not messages:
            return "No messages yet."
        lines = []
        for m in messages:
            role    = m.get("role", "user").capitalize()
            content = m.get("content", "")
            lines.append(f"{role}: {content}")
        return "\n".join(lines)
