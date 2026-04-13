"""
config.py – Central configuration for MCP Capstone.

"AI systems don't fail because models are weak.
 They fail because context is poorly managed."
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── OpenRouter ────────────────────────────────────────────────────────────────
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
MODEL_NAME: str = "anthropic/claude-haiku-4-5"  # fast & cheap for demos

# ── Memory ────────────────────────────────────────────────────────────────────
MEMORY_FILE: str = "memory_store.json"           # persisted on disk
HISTORY_THRESHOLD: int = 10                      # messages before compression
RECENT_MESSAGES_LIMIT: int = 5                   # messages sent in context

# ── Context ───────────────────────────────────────────────────────────────────
MAX_CONTEXT_TOKENS: int = 4_000                  # warn above this estimate
AVG_CHARS_PER_TOKEN: int = 4                     # rough approximation

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_INSTRUCTION: str = (
    "You are a context-aware AI assistant that remembers users across sessions. "
    "Always personalise your responses using the user's profile and conversation history. "
    "Be concise, helpful, and technical when the user's preferences indicate it."
)



