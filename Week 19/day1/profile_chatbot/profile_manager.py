"""
profile_manager.py
------------------
Handles all reading and writing of persistent user profiles.

Every profile is stored as a key inside profiles/users.json.
The key is the username (lowercase). The value is a dictionary
containing the user's name, preferred tone, and last discussed topic.

Keeping this logic isolated means the rest of the system never touches
the file directly. If we ever change the storage format — say, moving
from JSON to a database — only this file needs to change.
"""

import json
import os

PROFILES_FILE = os.path.join(os.path.dirname(__file__), "profiles", "users.json")
#  PROFILES_FILE = C:/EADP/Week 19/day1/profile_chatbot/profiles/users.json

class ProfileManager:
    """
    Manages persistent user profiles stored in a JSON file.

    On creation, it immediately loads all existing profiles into memory.
    All operations (get, create, update) work on the in-memory dictionary
    and then write back to disk to persist the change.
    """

    def __init__(self):
        """Load all profiles from disk the moment this object is created."""
        self.profiles = self.load_profiles()

    def load_profiles(self) -> dict:
        """
        Read and parse the profiles JSON file.

        Returns an empty dictionary if the file does not exist or is corrupted,
        so the system can always start fresh without crashing.

        Returns:
            dict: All stored user profiles keyed by username.
        """
        if not os.path.exists(PROFILES_FILE):
            return {}
        try:
            with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}

    def save_profiles(self) -> None:
        """
        Write the current in-memory profiles dictionary back to disk.

        Called after every mutation (create or update) so the file is
        always in sync with the in-memory state.
        """
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(self.profiles, f, indent=2, ensure_ascii=False)

    def get_profile(self, username: str) -> dict | None:
        """
        Retrieve a user profile by username.

        Args:
            username: The lowercase username key.

        Returns:
            dict: The profile dictionary if found.
            None: If no profile exists for this username.
        """
        return self.profiles.get(username.lower())

    def create_profile(self, username: str, name: str, tone: str) -> dict:
        """
        Create a brand-new profile and persist it immediately.

        Args:
            username:  Lowercase key used to look up the profile.
            name:      Display name shown in greetings and prompts.
            tone:      Preferred response tone (e.g. 'friendly', 'formal').

        Returns:
            dict: The newly created profile dictionary.
        """
        profile = {
            "name": name,
            "preferred_tone": tone.lower(),
            "last_topic": None,
        }
        self.profiles[username.lower()] = profile
        self.save_profiles()
        return profile

    def update_last_topic(self, username: str, topic: str) -> None:
        """
        Update the last_topic field for an existing user and save.

        This is the primary mechanism for memory persistence.
        The next time the user returns, this topic is injected into
        the system prompt so the model knows the conversation history.

        Args:
            username: The lowercase username key.
            topic:    The topic string to store.
        """
        key = username.lower()
        if key in self.profiles:
            self.profiles[key]["last_topic"] = topic
            self.save_profiles()
