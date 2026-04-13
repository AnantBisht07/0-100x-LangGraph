"""
quiz_engine.py
--------------
Generates quiz questions based on difficulty level.
Three levels: easy, medium, hard.
Each level targets a different depth of Python knowledge.
"""

import random

# ── Question Banks ───────────────────────────────────────────────────────────

QUESTIONS = {
    "easy": [
        {
            "question": "What keyword is used to define a function in Python?",
            "answer": "def",
        },
        {
            "question": "What data type stores True or False in Python?",
            "answer": "bool",
        },
        {
            "question": "What is the output of: print(2 + 3)?",
            "answer": "5",
        },
        {
            "question": "Which symbol is used to write a comment in Python?",
            "answer": "#",
        },
        {
            "question": "What built-in function reads user input from the keyboard?",
            "answer": "input",
        },
        {
            "question": "What keyword is used to create a variable holding nothing?",
            "answer": "none",
        },
        {
            "question": "What function returns the number of items in a list?",
            "answer": "len",
        },
        {
            "question": "What is the correct file extension for Python scripts?",
            "answer": ".py",
        },
    ],

    "medium": [
        {
            "question": "What does range(1, 5) produce? (list the values)",
            "answer": "1 2 3 4",
        },
        {
            "question": "What is the output of: [x for x in range(5) if x % 2 == 0]?",
            "answer": "[0, 2, 4]",
        },
        {
            "question": "How do you access the last element of a list called 'items'?",
            "answer": "items[-1]",
        },
        {
            "question": "What keyword exits a loop immediately?",
            "answer": "break",
        },
        {
            "question": "What does the 'continue' statement do in a loop?",
            "answer": "skips current iteration",
        },
        {
            "question": "What loop iterates a fixed number of times using range()?",
            "answer": "for",
        },
        {
            "question": "What method adds an item to the end of a list?",
            "answer": "append",
        },
        {
            "question": "How do you check if a key exists in a dictionary 'd'?",
            "answer": "key in d",
        },
    ],

    "hard": [
        {
            "question": "What is the time complexity of binary search?",
            "answer": "o(log n)",
        },
        {
            "question": "What does *args allow in a Python function?",
            "answer": "variable number of positional arguments",
        },
        {
            "question": "What is a decorator in Python? (one sentence)",
            "answer": "a function that wraps another function to modify its behavior",
        },
        {
            "question": "What is the difference between a shallow copy and a deep copy?",
            "answer": "shallow copy copies references, deep copy copies all nested objects",
        },
        {
            "question": "What keyword turns a function into a generator?",
            "answer": "yield",
        },
        {
            "question": "What built-in method returns key-value pairs from a dictionary?",
            "answer": "items",
        },
        {
            "question": "What does the @staticmethod decorator do?",
            "answer": "defines a method that does not receive self or cls",
        },
        {
            "question": "What is a lambda function?",
            "answer": "an anonymous single-expression function",
        },
    ],
}

# ── Public API ────────────────────────────────────────────────────────────────

def generate_question(difficulty: str) -> dict:
    """
    Return a random question dict for the given difficulty level.

    Args:
        difficulty: one of 'easy', 'medium', 'hard'

    Returns:
        {"question": str, "answer": str}
    """
    level = difficulty.lower()
    if level not in QUESTIONS: # defensive programming
        level = "easy"
    return random.choice(QUESTIONS[level])


def check_answer(user_answer: str, correct_answer: str) -> bool:
    """
    Case-insensitive, strip-whitespace answer comparison.
    Returns True if the student's answer is correct.
    """
    return user_answer.strip().lower() == correct_answer.strip().lower()

