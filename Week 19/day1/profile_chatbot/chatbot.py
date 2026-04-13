"""
chatbot.py
----------
Core LLM interaction logic for the Profile-Aware Chatbot.

This module owns one responsibility: given a user message and a profile,
build the right system prompt (with memory injected), call the LLM,
and return the response text.

It does not manage profiles, does not handle file I/O, and does not run
the conversation loop. Those concerns belong to other modules.
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

from memory_injector import MemoryInjector

load_dotenv()

# Tone instruction map — translates a stored tone preference into a
# concrete instruction for the model. Centralising these here means
# adding a new tone requires only one new line.
TONE_INSTRUCTIONS = {
    "friendly":   "Use a warm, friendly, and encouraging tone.",
    "formal":     "Use a professional and formal tone.",
    "concise":    "Be brief and direct. Avoid unnecessary elaboration.",
    "detailed":   "Provide thorough, step-by-step explanations.",
    "humorous":   "Be conversational and lightly humorous where appropriate.",
}

# private helper...
def _get_client() -> tuple[OpenAI, str]:
    """
    Resolve API credentials from the environment and return a
    configured OpenAI client along with the model name.

    Returns:
        Tuple of (OpenAI client, model name string).

    Raises:
        EnvironmentError: If no API key is found.
    """
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "No API key found. Set OPENAI_API_KEY or OPENROUTER_API_KEY in your .env file."
        )
    base_url  = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    model     = os.getenv("MODEL_NAME", "openai/gpt-4o-mini")
    client    = OpenAI(api_key=api_key, base_url=base_url)
    return client, model


def _build_system_prompt(profile: dict, memory_context: str) -> str:
    """
    Assemble the full system prompt with the user's memory context and
    tone instruction embedded inside it.

    The system prompt has three layers:
      1. A base instruction telling the model its role.
      2. The memory context block (name, tone, last topic) injected here.
      3. A tone instruction derived from the stored preferred_tone.
      4. A relationship instruction asking the model to connect back to
         the user's last topic where relevant.

    Args:
        profile:        The user's profile dictionary.
        memory_context: The pre-formatted string from MemoryInjector.

    Returns:
        str: The complete system prompt string.
    """
    tone_key         = profile.get("preferred_tone", "friendly").lower()
    tone_instruction = TONE_INSTRUCTIONS.get(tone_key, TONE_INSTRUCTIONS["friendly"])
    last_topic       = profile.get("last_topic")

    relationship_line = (
        f"If possible, relate your explanation to their previous topic: {last_topic}."
        if last_topic
        else "This is the user's first session — no prior topic context yet."
    )

    return (
        f"You are a helpful AI assistant.\n\n"
        f"{memory_context}\n\n"
        f"{tone_instruction}\n"
        f"{relationship_line}"
    )


def generate_response(user_input: str, profile: dict) -> str:
    """
    Generate an LLM response for the given user input, with the user's
    full profile memory injected into the system prompt.

    This is the core function of the chatbot. Every call:
      1. Builds the memory context from the profile.
      2. Assembles the system prompt with that context and tone.
      3. Calls the LLM.
      4. Returns the response text.

    Args:
        user_input: The message typed by the user.
        profile:    The current user's profile dictionary.

    Returns:
        str: The model's response text.
    """
    injector       = MemoryInjector()
    memory_context = injector.build_memory_context(profile)
    system_prompt  = _build_system_prompt(profile, memory_context)

    client, model = _get_client()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system",  "content": system_prompt},
            {"role": "user",    "content": user_input},
        ],
    )

    return response.choices[0].message.content or ""
