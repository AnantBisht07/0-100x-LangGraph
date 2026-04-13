"""
memory_store.py — Persistent JSON-based long-term memory.

This simulates a production user memory store (could be replaced with
Redis or a database in a real deployment). Each user gets a persistent
profile that survives across sessions.

Structure per user:
    {
        "name":        "Rahul",
        "preferences": "technical",
        "summary":     "User learning about AI systems...",
        "created_at":  "2026-03-21"
    }
"""

import json
import os
from datetime import datetime


# Resolve path relative to this file so it works from any cwd
_BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
_MEMORY_DIR = os.path.join(_BASE_DIR, "data")
_MEMORY_FILE = os.path.join(_MEMORY_DIR, "memory.json")


def _ensure_file() -> None:
    """Create the data directory and memory file if they don't exist."""
    os.makedirs(_MEMORY_DIR, exist_ok=True)
    if not os.path.exists(_MEMORY_FILE):
        with open(_MEMORY_FILE, "w") as f:
            json.dump({}, f, indent=2)


def _read_all() -> dict:
    _ensure_file()
    with open(_MEMORY_FILE, "r") as f:
        return json.load(f)


def _write_all(data: dict) -> None:
    _ensure_file()
    with open(_MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ── Public API ────────────────────────────────────────────────────────────────

def load_memory(user_id: str) -> dict:
    """
    Load a user's memory profile.

    Returns the stored profile dict, or an empty dict if the user
    is not yet in the system.
    """
    all_data = _read_all()
    return all_data.get(user_id, {})


def save_memory(user_id: str, data: dict) -> None:
    """
    Persist a user's full memory profile.

    Overwrites any existing data for that user_id.
    """
    all_data = _read_all()
    all_data[user_id] = data
    _write_all(all_data)


def update_summary(user_id: str, new_summary: str) -> None:
    """
    Update only the conversation summary field.

    Called by the context manager when old messages are compressed.
    """
    all_data = _read_all()
    if user_id not in all_data:
        all_data[user_id] = {}
    all_data[user_id]["summary"] = new_summary
    _write_all(all_data)


def create_user(user_id: str, name: str, preferences: str = "general") -> dict:
    """
    Create a new user profile and persist it.

    Returns the created profile.
    """
    profile = {
        "name":        name,
        "preferences": preferences,
        "summary":     "",
        "created_at":  datetime.now().strftime("%Y-%m-%d"),
    }
    save_memory(user_id, profile)
    return profile


def list_users() -> list[str]:
    """Return all known user IDs."""
    return list(_read_all().keys())
