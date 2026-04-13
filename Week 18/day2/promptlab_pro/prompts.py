"""
prompts.py
----------
Central registry of all prompt versions available for A/B testing.

Adding a new prompt version requires only adding one entry to PROMPT_VERSIONS.
No other file needs to change. The keys are used throughout the system as
version identifiers — in batch results, aggregated metrics, and the dashboard.
"""

PROMPT_VERSIONS = {
    "control": (
        "You are a concise assistant. Answer clearly and briefly."
    ),
    "variation": (
        "You are a structured, detailed assistant that explains reasoning clearly. "
        "Break down your answer step by step where appropriate."
    ),
}


def get_prompt(version: str) -> str:
    """
    Retrieve the system prompt for a given version key.

    Args:
        version: A key from PROMPT_VERSIONS (e.g. 'control', 'variation').

    Returns:
        str: The system prompt string.

    Raises:
        ValueError: If the version key does not exist.
    """
    if version not in PROMPT_VERSIONS:
        raise ValueError(
            f"Unknown prompt version '{version}'. "
            f"Available: {list(PROMPT_VERSIONS.keys())}"
        )
    return PROMPT_VERSIONS[version]
