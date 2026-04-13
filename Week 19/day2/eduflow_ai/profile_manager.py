"""
profile_manager.py
------------------
Manages persistent student profiles stored in students.json.
Handles loading, saving, creating, and updating student records.
"""

import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "students.json")


class ProfileManager:
    """Handles all CRUD operations for student profiles."""

    def __init__(self):
        self.profiles = self.load_profiles()

    def load_profiles(self) -> dict:
        """Load all student profiles from the JSON file."""
        if not os.path.exists(DATA_PATH):
            os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
            return {}
        with open(DATA_PATH, "r") as f:
            return json.load(f)

    def save_profiles(self) -> None:
        """Persist all profiles back to the JSON file."""
        with open(DATA_PATH, "w") as f:
            json.dump(self.profiles, f, indent=2) #homework.

    def get_student(self, name: str) -> dict | None:
        """Retrieve a student profile by name (case-insensitive)."""
        return self.profiles.get(name.lower())

    def create_student(self, name: str) -> dict:
        """
        Create a new student profile with default values.
        Returns the newly created profile.
        """
        key = name.lower()
        self.profiles[key] = {
            "name": name.title(),
            "difficulty": "easy",
            "correct_answers": 0,
            "wrong_answers": 0,
            "last_topic": "Python Basics",
        }
        self.save_profiles()
        print(f"  New profile created for {name.title()}!")
        return self.profiles[key]

    def update_progress(self, name: str, correct: int, wrong: int) -> None:
        """Increment correct and wrong answer counts for a student."""
        key = name.lower()
        if key in self.profiles:
            self.profiles[key]["correct_answers"] += correct
            self.profiles[key]["wrong_answers"] += wrong
            self.save_profiles()

    def update_topic(self, name: str, topic: str) -> None:
        """Update the last studied topic for a student."""
        key = name.lower()
        if key in self.profiles:
            self.profiles[key]["last_topic"] = topic
            self.save_profiles()

    def update_difficulty(self, name: str, difficulty: str) -> None:
        """Update the difficulty level for a student."""
        key = name.lower()
        if key in self.profiles:
            self.profiles[key]["difficulty"] = difficulty
            self.save_profiles()

    def get_or_create(self, name: str) -> dict:
        """Return existing profile or create a new one."""
        profile = self.get_student(name)
        if profile is None:
            profile = self.create_student(name)
        return profile
