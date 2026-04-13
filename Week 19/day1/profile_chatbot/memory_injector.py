"""
memory_injector.py
------------------
Transforms a user profile dictionary into a formatted string that is
injected directly into the LLM system prompt.

This module is the bridge between stored data and active model behaviour.
A profile is just data until it reaches the model. The MemoryInjector
turns it into context the model can read and act upon.

Keeping this logic in its own module means the format of the injected
memory can be changed without touching the chatbot or profile manager.
"""


class MemoryInjector:
    """
    Builds the memory context block that gets inserted into the system prompt.

    The context block tells the model who the user is, how they prefer
    to be spoken to, and what they were last discussing. This is what
    makes the chatbot adaptive rather than stateless.
    """

    def build_memory_context(self, profile: dict) -> str:
        """
        Convert a user profile dictionary into a formatted context string.

        The returned string is placed inside the system prompt so the model
        treats it as background knowledge about the user before reading
        any part of the conversation.

        Args:
            profile: A user profile dictionary with keys:
                     name, preferred_tone, last_topic.

        Returns:
            str: A multi-line formatted context block ready for prompt injection.

        Example output:
            User Profile:
            Name: Rahul
            Preferred Tone: Friendly
            Last Discussed Topic: LangGraph
        """
        name = profile.get("name", "User")
        tone = profile.get("preferred_tone", "friendly").capitalize()
        last_topic = profile.get("last_topic")

        # Build the last topic line conditionally — if no topic has been
        # stored yet, we omit the line entirely rather than showing "None"
        topic_line = f"Last Discussed Topic: {last_topic}" if last_topic else "Last Discussed Topic: None yet"

        return (
            f"User Profile:\n"
            f"Name: {name}\n"
            f"Preferred Tone: {tone}\n"
            f"{topic_line}"
        )
