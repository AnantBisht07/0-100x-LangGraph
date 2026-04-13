"""
main.py — CLI entry point for the Production AI Agent.

This is what students run: python main.py

Flow:
    1. Validate config (API keys present)
    2. Ask for user ID
    3. Load or create user profile
    4. Conversation loop:
        a. Take user input
        b. Run pipeline (router → tool → MCP → LLM)
        c. Print response + metadata
        d. Save updated memory
    5. Exit cleanly on 'exit'
"""

import config  # MUST be first — sets env vars before any LangSmith import
import memory_store
from pipeline import run_pipeline


BANNER = """
╔══════════════════════════════════════════════════════════════════╗
║         Production AI Agent  —  Week 20 Demo                    ║
║         LangSmith Observability  +  Model Context Protocol       ║
╚══════════════════════════════════════════════════════════════════╝
"""

HELP_TEXT = """
Commands:
  exit       → quit the session
  /stats     → show your memory profile
  /clear     → clear screen
  /users     → list all known users
  (anything) → chat with the agent
"""


def show_profile(user_id: str) -> None:
    """Print the user's current memory profile."""
    profile = memory_store.load_memory(user_id)
    if not profile:
        print("  No profile found.")
        return
    print(f"\n  Name        : {profile.get('name', user_id)}")
    print(f"  Preferences : {profile.get('preferences', 'general')}")
    print(f"  Member since: {profile.get('created_at', 'unknown')}")
    summary = profile.get("summary", "")
    if summary:
        print(f"  Summary     : {summary[:120]}{'...' if len(summary) > 120 else ''}")
    print()


def get_or_create_user(user_id: str) -> dict:
    """Load existing profile or guide user through creating one."""
    profile = memory_store.load_memory(user_id)
    if profile:
        print(f"\n  Welcome back, {profile.get('name', user_id)}!")
        print(f"  Preferences : {profile.get('preferences', 'general')}")
        summary = profile.get("summary", "")
        if summary:
            print(f"  Last session: {summary[:80]}...")
        return profile

    # New user onboarding
    print(f"\n  New user detected: '{user_id}'")
    name = input("  Enter your name: ").strip() or user_id
    pref = input("  Preferences — technical or casual? [technical]: ").strip() or "technical"
    profile = memory_store.create_user(user_id, name, pref)
    print(f"\n  Profile created. Welcome, {name}!")
    return profile


def run_session(user_id: str) -> None:
    """
    Main conversation loop.

    Maintains an in-session message history.
    The pipeline handles slicing/summarization internally via MCP.
    """
    messages: list[dict] = []

    print(HELP_TEXT)
    print("  LangSmith tracing is ACTIVE — check your dashboard at smith.langchain.com")
    print(f"  Project: {config.LANGCHAIN_PROJECT}\n")
    print("─" * 66)

    while True:
        try:
            user_input = input("\n  You: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("\n  Session ended. Your memory has been saved.")
            break

        if user_input.lower() == "/stats":
            show_profile(user_id)
            continue

        if user_input.lower() == "/clear":
            print("\033[2J\033[H", end="")
            continue

        if user_input.lower() == "/users":
            users = memory_store.list_users()
            print(f"\n  Known users: {', '.join(users) if users else 'none'}")
            continue

        # ── Run the full pipeline ──────────────────────────────────────────
        print("\n  [Thinking...]", end="\r")

        result = run_pipeline(
            user_id  = user_id,
            messages = messages,
            query    = user_input,
        )

        response     = result["response"]
        route        = result["route"]
        tool_result  = result["tool_result"]
        token_est    = result["token_estimate"]

        # ── Print response ─────────────────────────────────────────────────
        print(f"  Agent: {response}")

        # ── Print metadata (useful for teaching observability) ─────────────
        print(f"\n  ┌─ Pipeline Metadata")
        print(f"  │  Route         : {route}")
        if tool_result:
            preview = tool_result[:60] + ("..." if len(tool_result) > 60 else "")
            print(f"  │  Tool Result   : {preview}")
        print(f"  │  Context Tokens: ~{token_est}")
        print(f"  └─ Trace visible in LangSmith → Project: {config.LANGCHAIN_PROJECT}")

        # ── Update in-memory history ───────────────────────────────────────
        messages.append({"role": "user",      "content": user_input})
        messages.append({"role": "assistant", "content": response})


def main() -> None:
    print(BANNER)

    # Validate API keys before doing anything
    try:
        config.validate_config()
    except EnvironmentError as e:
        print(f"  CONFIG ERROR: {e}")
        return

    print("  Enter your user ID (e.g. anant)")
    user_id = input("  User ID: ").strip().lower()

    if not user_id:
        print("  User ID cannot be empty.")
        return

    profile = get_or_create_user(user_id)
    run_session(user_id)


if __name__ == "__main__":
    main()
