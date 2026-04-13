"""
validator.py – Production-grade context validation layer.

Before every LLM call this module inspects the assembled context and reports
any issues that could degrade response quality or silently waste tokens.

Checks performed:
  1. Context size  – warn if estimated token count exceeds the configured limit.
  2. Missing memory – alert when the profile or summary are absent/empty.
  3. Relevance     – basic keyword overlap between query and context body.

Returning a structured result (rather than raising exceptions) lets the pipeline
decide whether to proceed, warn, or abort – keeping policy separate from detection.

"AI systems don't fail because models are weak.
 They fail because context is poorly managed."
"""

from context_manager import estimate_token_count
from config import MAX_CONTEXT_TOKENS


# ── Individual checks ─────────────────────────────────────────────────────────

def _check_context_size(context: str) -> list[str]:
    """
    Warn when the context is approaching or exceeding the token budget.

    Returns a list of issue strings (empty if all is well).
    """
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


def _check_missing_memory(user_data: dict) -> list[str]:
    """
    Verify that the user record has the expected memory fields populated.

    Returns a list of issue strings.
    """
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


def _check_relevance(context: str, query: str) -> list[str]:
    """
    Rudimentary relevance check: at least one significant query keyword should
    appear somewhere in the non-query part of the context.

    This catches cases where the context is stale or completely unrelated to
    what the user is asking.

    Returns a list of issue strings.
    """
    issues = []

    # Split off the query block so we only search the memory layers
    context_body = context.split("User Query:")[0].lower()

    # Tokenise query into meaningful words (4+ chars, no stop words)
    stop_words = {"what", "when", "where", "which", "with", "from", "that",
                  "this", "have", "been", "will", "your", "about", "tell"}
    keywords = [
        word for word in query.lower().split()
        if len(word) >= 4 and word not in stop_words
    ]

    if not keywords:
        return issues  # query too short to evaluate

    found = any(kw in context_body for kw in keywords)
    if not found:
        issues.append(
            f"[RELEVANCE] None of the query keywords {keywords[:5]} were found in the "
            "context memory. The agent may lack relevant background for this question."
        )

    return issues


# ── Public API ────────────────────────────────────────────────────────────────

def validate_context(context: str, user_data: dict, query: str = "") -> dict:
    """
    Run all validation checks and return a structured result.

    Args:
        context:   The fully assembled MCP context string.
        user_data: The raw user memory record (profile, summary, history).
        query:     The current user query (used for relevance check).

    Returns:
        {
            "valid":  bool,     # False if any ERROR-level issue exists
            "issues": [str],    # list of warning / error messages
            "token_estimate": int,
        }
    """
    issues: list[str] = []

    issues.extend(_check_context_size(context))
    issues.extend(_check_missing_memory(user_data))

    if query:
        issues.extend(_check_relevance(context, query))

    # Classify severity: SIZE issues are warnings; the rest are informational
    has_error = any("[SIZE] Context is too large" in i for i in issues)

    return {
        "valid": not has_error,
        "issues": issues,
        "token_estimate": estimate_token_count(context),
    }
