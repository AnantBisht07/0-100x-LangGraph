"""
learning_path.py
----------------
Determines the next topic a student should study based on their
current last_topic and difficulty level.

Supports a linear progression through Python fundamentals, with
branching suggestions for advanced students.
"""

# Ordered topic progression
TOPIC_SEQUENCE = [
    "Python Basics",
    "Variables and Data Types",
    "Python Loops",
    "Conditionals",
    "Functions",
    "Lists and Tuples",
    "Dictionaries",
    "String Manipulation",
    "File Handling",
    "Error Handling",
    "Object-Oriented Programming",
    "Modules and Packages",
    "List Comprehensions",
    "Generators and Iterators",
    "Decorators",
    "Advanced Python",
]

# Extra challenge topics unlocked at 'hard' difficulty
HARD_TOPICS = [
    "Concurrency and Threading",
    "Async Programming",
    "Design Patterns",
    "Testing and TDD",
    "Performance Optimization",
]


def get_next_topic(profile: dict) -> str:
    """
    Suggest the next learning topic for a student.

    Logic:
      - Find the current last_topic in the sequence.
      - Return the topic immediately after it.
      - If the student is at 'hard' difficulty and nearing the end,
        suggest advanced challenge topics.
      - If the topic is not in the sequence, restart from the beginning.

    Args:
        profile: a student profile dict from ProfileManager

    Returns:
        The name of the next recommended topic (str)
    """
    last_topic = profile.get("last_topic", "Python Basics")
    difficulty  = profile.get("difficulty", "easy").lower()

    if last_topic in TOPIC_SEQUENCE:
        current_index = TOPIC_SEQUENCE.index(last_topic)
        next_index = current_index + 1

        # Reached end of main sequence
        if next_index >= len(TOPIC_SEQUENCE):
            if difficulty == "hard":
                return HARD_TOPICS[0]
            return TOPIC_SEQUENCE[-1]   # stay on last topic

        return TOPIC_SEQUENCE[next_index]

    # Topic found in hard extensions
    if last_topic in HARD_TOPICS:
        idx = HARD_TOPICS.index(last_topic)
        next_idx = idx + 1
        if next_idx < len(HARD_TOPICS):
            return HARD_TOPICS[next_idx]
        return "Advanced Python — Mastery Achieved!"

    # Unknown topic — restart sequence
    return TOPIC_SEQUENCE[0]


def get_topic_progress(profile: dict) -> str:
    """Return a human-readable progress string for the student's position."""
    last_topic = profile.get("last_topic", "Python Basics")
    sequence = TOPIC_SEQUENCE + HARD_TOPICS

    if last_topic in sequence:
        idx = sequence.index(last_topic) + 1
        total = len(sequence)
        return f"{idx}/{total} topics covered"
    return "Starting out"
