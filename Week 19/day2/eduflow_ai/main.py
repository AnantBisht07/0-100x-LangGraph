"""
main.py
-------
CLI entry point for EduFlow AI – Adaptive Learning System.

Usage:
    python main.py

The user is prompted for their name, then placed into an adaptive
learning session.  Type 'exit' at any prompt to quit.
"""

import sys
import os

# Ensure local modules are found when running from any directory
sys.path.insert(0, os.path.dirname(__file__))

from profile_manager   import ProfileManager
from eduflow_core      import run_learning_session
from difficulty_manager import get_accuracy


BANNER = """
╔══════════════════════════════════════════════════╗
║          EduFlow AI – Adaptive Learning          ║
║        Personalized Python Quiz System           ║
╚══════════════════════════════════════════════════╝
"""

MENU = """
  Options:
    [1] Start learning session
    [2] View my profile / stats
    [3] Switch student
    [4] Exit
"""


def show_profile(name: str) -> None:
    """Print a detailed profile summary for a student."""
    pm = ProfileManager()
    profile = pm.get_student(name)
    if not profile:
        print(f"  No profile found for '{name}'.")
        return

    correct = profile["correct_answers"]
    wrong   = profile["wrong_answers"]
    total   = correct + wrong
    acc     = get_accuracy(profile)

    print(f"\n  ── Profile: {profile['name']} ──────────────────────")
    print(f"  Difficulty      : {profile['difficulty'].upper()}")
    print(f"  Last topic      : {profile['last_topic']}")
    print(f"  Total answered  : {total}")
    print(f"  Correct         : {correct}  ✓")
    print(f"  Wrong           : {wrong}   ✗")
    print(f"  Accuracy        : {acc:.0%}")
    print()


def get_num_questions() -> int:
    """Ask user how many questions they want (default 5)."""
    try:
        raw = input("  How many questions? (default 5): ").strip()
        if raw == "":
            return 5
        n = int(raw)
        return max(1, min(n, 20))   # clamp between 1 and 20
    except ValueError:
        return 5


def main() -> None:
    print(BANNER)

    # ── Get student name ──────────────────────────────────────────────────────
    while True:
        name = input("  Enter your name (or 'exit' to quit): ").strip()
        if name.lower() == "exit" or name == "":
            print("  Goodbye!\n")
            return
        break

    pm = ProfileManager()
    profile = pm.get_or_create(name)
    print(f"\n  Hello, {profile['name']}! Let's learn Python together.")

    # ── Main menu loop ────────────────────────────────────────────────────────
    while True:
        print(MENU)
        choice = input("  Choose an option: ").strip()

        if choice == "1":
            num_q = get_num_questions()
            run_learning_session(name, num_questions=num_q)

        elif choice == "2":
            show_profile(name)

        elif choice == "3":
            name = input("  Enter new student name: ").strip()
            if name:
                profile = pm.get_or_create(name)
                print(f"\n  Switched to profile: {profile['name']}")

        elif choice == "4" or choice.lower() == "exit":
            print("\n  Progress saved. See you next time!\n")
            break

        else:
            print("  Invalid option. Please choose 1–4.")


if __name__ == "__main__":
    main()
