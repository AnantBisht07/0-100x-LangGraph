"""
memory_store.py – JSON-based persistent memory system.

Stores per-user profile, conversation summary, and raw message history so that
the agent can pick up exactly where it left off across separate Python sessions.

"AI systems don't fail because models are weak.
 They fail because context is poorly managed."
"""

import json
import os
from typing import Any

from config import MEMORY_FILE


# ── Internal helpers ──────────────────────────────────────────────────────────

def _load_db() -> dict:
    """Read the entire memory file from disk; return an empty dict if missing."""
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _save_db(db: dict) -> None:
    """Persist the entire memory database to disk."""
    with open(MEMORY_FILE, "w", encoding="utf-8") as fh:
        json.dump(db, fh, indent=2, ensure_ascii=False)


def _default_user(user_id: str) -> dict:
    """Return a blank user record."""
    return {
        "profile": {
            "name": user_id,
            "preferences": "general",
        },
        "summary": "",
        "history": [],
    }


# ── Public API ────────────────────────────────────────────────────────────────

def load_user(user_id: str) -> dict:
    """
    Load a user's memory record.

    Creates a fresh record if the user has never been seen before.

    Args:
        user_id: Unique identifier for the user (e.g. "rahul").

    Returns:
        dict with keys: profile, summary, history.
    """
    db = _load_db()
    if user_id not in db:
        db[user_id] = _default_user(user_id)
        _save_db(db)
    return db[user_id]


def save_user(user_id: str, data: dict) -> None:
    """
    Overwrite the entire user record in the database.

    Args:
        user_id: Unique identifier for the user.
        data:    Full user dict (profile, summary, history).
    """
    db = _load_db()
    db[user_id] = data
    _save_db(db)


def update_summary(user_id: str, summary: str) -> None:
    """
    Replace the stored conversation summary for a user.

    Called by the summarizer after compressing old messages.

    Args:
        user_id: Unique identifier for the user.
        summary: New compressed summary string.
    """
    db = _load_db()
    if user_id not in db:
        db[user_id] = _default_user(user_id)
    db[user_id]["summary"] = summary
    _save_db(db)


def append_message(user_id: str, message: dict) -> None:
    """
    Add a single message dict to the user's history list.

    Message format: {"role": "user" | "assistant", "content": "..."}

    Args:
        user_id: Unique identifier for the user.
        message: Message dict to append.
    """
    db = _load_db()
    if user_id not in db:
        db[user_id] = _default_user(user_id)
    db[user_id]["history"].append(message)
    _save_db(db)


def update_profile(user_id: str, profile: dict) -> None:
    """
    Merge new profile fields into the existing profile.

    Args:
        user_id: Unique identifier for the user.
        profile: Dict of fields to update (e.g. {"name": "Rahul"}).
    """
    db = _load_db()
    if user_id not in db:
        db[user_id] = _default_user(user_id)
    db[user_id]["profile"].update(profile)
    _save_db(db)
