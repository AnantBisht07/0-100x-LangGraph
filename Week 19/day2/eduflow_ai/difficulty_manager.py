"""
difficulty_manager.py
---------------------
Adaptive difficulty logic.
Computes accuracy from a student profile and upgrades or downgrades
the difficulty level accordingly.
"""

LEVELS = ["easy", "medium", "hard"]

# Thresholds
HIGH_ACCURACY = 0.80   # → move up (80%)
LOW_ACCURACY  = 0.50   # → move down (50%)


def adjust_difficulty(profile: dict) -> str:
    """
    Determine the new difficulty level for a student based on their
    overall accuracy across all recorded answers.

    Rules:
        accuracy > 0.80  → increase difficulty (up to 'hard')
        accuracy < 0.50  → decrease difficulty (down to 'easy')
        otherwise        → keep current level

    Args:
        profile: a student profile dict from ProfileManager

    Returns:
        The (possibly updated) difficulty string: 'easy', 'medium', or 'hard'
    """
    correct = profile.get("correct_answers", 0)
    wrong   = profile.get("wrong_answers", 0)
    total   = correct + wrong

    current = profile.get("difficulty", "easy").lower()

    # Not enough data yet — keep current level
    if total == 0:
        return current

    accuracy = correct / total
    current_index = LEVELS.index(current) if current in LEVELS else 0

    if accuracy > HIGH_ACCURACY:
        new_index = min(current_index + 1, len(LEVELS) - 1)
    elif accuracy < LOW_ACCURACY:
        new_index = max(current_index - 1, 0)
    else:
        new_index = current_index

    new_level = LEVELS[new_index]

    if new_level != current:
        direction = "UP" if new_index > current_index else "DOWN"
        print(f"  Difficulty adjusted {direction}: {current.upper()} → {new_level.upper()} "
              f"(accuracy: {accuracy:.0%})")
    else:
        print(f"  Difficulty unchanged: {current.upper()} (accuracy: {accuracy:.0%})")

    return new_level


def get_accuracy(profile: dict) -> float:
    """Return overall accuracy as a float between 0 and 1."""
    correct = profile.get("correct_answers", 0)
    total   = correct + profile.get("wrong_answers", 0)
    return correct / total if total > 0 else 0.0
