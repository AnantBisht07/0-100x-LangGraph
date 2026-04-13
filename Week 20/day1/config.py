"""
config.py — Environment setup and LangSmith tracing configuration.

This module must be imported FIRST in every file that uses tracing.
Setting LANGCHAIN_TRACING_V2=true before any LangChain/LangSmith import
ensures all @traceable decorators are active from the start.
"""

import os
from dotenv import load_dotenv

# Load .env file values into environment
load_dotenv()

# ── LangSmith Configuration ──────────────────────────────────────────────────
LANGCHAIN_API_KEY     = os.getenv("LANGCHAIN_API_KEY", "")
LANGCHAIN_PROJECT     = os.getenv("LANGCHAIN_PROJECT", "Week20-Production-Agent")
LANGCHAIN_TRACING_V2  = os.getenv("LANGCHAIN_TRACING_V2", "true")

# These must be set as env vars — LangSmith SDK reads them automatically
os.environ["LANGCHAIN_API_KEY"]    = LANGCHAIN_API_KEY
os.environ["LANGCHAIN_PROJECT"]    = LANGCHAIN_PROJECT
os.environ["LANGCHAIN_TRACING_V2"] = LANGCHAIN_TRACING_V2

# ── OpenRouter Configuration ──────────────────────────────────────────────────
# OpenRouter is OpenAI-compatible — same SDK, different base URL + key.
OPENROUTER_API_KEY  = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "")   # optional, shown in OR dashboard
OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME", "Week20-Production-Agent")

# ── App Settings ─────────────────────────────────────────────────────────────
LLM_MODEL           = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
MAX_RECENT_MESSAGES = int(os.getenv("MAX_RECENT_MESSAGES", "5"))
SUMMARY_THRESHOLD   = int(os.getenv("SUMMARY_THRESHOLD", "10"))  # compress after N messages
MEMORY_FILE         = os.getenv("MEMORY_FILE", "data/memory.json")


def validate_config() -> None:
    """Raise an error early if required keys are missing."""
    missing = []
    if not LANGCHAIN_API_KEY:
        missing.append("LANGCHAIN_API_KEY")
    if not OPENROUTER_API_KEY:
        missing.append("OPENROUTER_API_KEY")
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            "Copy .env.example → .env and fill in your keys."
        )
