"""
eduflow_core.py
---------------
Central orchestration module for EduFlow AI.
Coordinates the full adaptive learning pipeline:

  1. Load student profile
  2. Generate question based on current difficulty
  3. Present question to student
  4. Evaluate answer
  5. Update progress counters
  6. Adjust difficulty based on updated accuracy
  7. Save profile
  8. Suggest next topic
"""

from profile_manager  import ProfileManager
from quiz_engine       import generate_question, check_answer
from difficulty_manager import adjust_difficulty
from learning_path     import get_next_topic, get_topic_progress


def run_learning_session(student_name: str, num_questions: int = 5) -> None:
    """
    Run a complete adaptive learning session for one student.

    Args:
        student_name:  The student's name (looked up case-insensitively).
        num_questions: Number of questions to ask per session (default 5).
    """
    pm = ProfileManager()

    # ── Step 1: Load or create profile ───────────────────────────────────────
    profile = pm.get_or_create(student_name)
    name    = profile["name"]

    print(f"\n{'='*50}")
    print(f"  Welcome back, {name}!")
    print(f"  Current difficulty : {profile['difficulty'].upper()}")
    print(f"  Last topic studied : {profile['last_topic']}")
    print(f"  Progress           : {get_topic_progress(profile)}")
    correct_total = profile['correct_answers']
    wrong_total   = profile['wrong_answers']
    total_so_far  = correct_total + wrong_total
    if total_so_far > 0:
        acc = correct_total / total_so_far
        print(f"  Overall accuracy   : {acc:.0%}  ({correct_total}✓  {wrong_total}✗)")
    print(f"{'='*50}\n")

    session_correct = 0
    session_wrong   = 0

    # ── Steps 2–5: Question loop ──────────────────────────────────────────────
    for q_num in range(1, num_questions + 1):
        # Always read the freshest difficulty from the saved profile
        current_profile = pm.get_student(student_name)
        difficulty      = current_profile["difficulty"]

        question_data = generate_question(difficulty)

        print(f"  Q{q_num} [{difficulty.upper()}]  {question_data['question']}")
        user_answer = input("  Your answer: ").strip()

        if user_answer.lower() == "exit":
            print("\n  Session ended early. Progress saved.")
            break

        is_correct = check_answer(user_answer, question_data["answer"])

        if is_correct:
            print("  Correct!\n")
            session_correct += 1
        else:
            print(f"  Wrong. Correct answer: {question_data['answer']}\n")
            session_wrong += 1

        # ── Step 6: Update progress after every answer ────────────────────────
        pm.update_progress(student_name, correct=int(is_correct), wrong=int(not is_correct))

        # ── Step 7: Re-evaluate difficulty after every answer ─────────────────
        refreshed = pm.get_student(student_name)
        new_difficulty = adjust_difficulty(refreshed)
        pm.update_difficulty(student_name, new_difficulty)

    # ── Steps 8–9: Save and suggest next topic ────────────────────────────────
    final_profile = pm.get_student(student_name)
    next_topic    = get_next_topic(final_profile)
    pm.update_topic(student_name, next_topic)

    print(f"\n{'─'*50}")
    print(f"  Session complete for {name}!")
    print(f"  This session  : {session_correct} correct,  {session_wrong} wrong")
    print(f"  Next topic    : {next_topic}")
    print(f"  New difficulty: {final_profile['difficulty'].upper()}")
    print(f"{'─'*50}\n")
