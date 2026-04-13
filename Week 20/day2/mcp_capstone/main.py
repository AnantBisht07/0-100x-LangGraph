"""
main.py – CLI entry point for the MCP Capstone agent.

Run:
    python main.py

The system will:
  • Remember you across sessions
  • Compress memory automatically when history grows long
  • Inject structured MCP context on every turn
  • Validate context quality before each LLM call
  • Respond intelligently using your profile and history

"AI systems don't fail because models are weak.
 They fail because context is poorly managed."
"""

import sys

from agent_pipeline import run_pipeline
from memory_store import load_user, update_profile


# ── Setup helpers ─────────────────────────────────────────────────────────────

def _greet_user(user_id: str, user_data: dict) -> None:
    """Print a personalised welcome message."""
    name        = user_data["profile"].get("name", user_id)
    has_history = bool(user_data["history"] or user_data["summary"])

    if has_history:
        summary_snippet = user_data.get("summary", "")
        if summary_snippet:
            print(f"\nWelcome back, {name}!")
            print(f"  Last time we spoke about: {summary_snippet[:120]}…"
                  if len(summary_snippet) > 120 else
                  f"  Last session summary: {summary_snippet}")
        else:
            print(f"\nWelcome back, {name}! Continuing our conversation.")
    else:
        print(f"\nHello, {name}! I'm your context-aware AI assistant.")
        print("  I'll remember you across sessions and get smarter over time.")


def _onboard_new_user(user_id: str, user_data: dict) -> dict:
    """
    For brand-new users, collect a display name and preference style.
    This enriches the profile so responses are personalised from the start.
    """
    if user_data["history"] or user_data["summary"]:
        return user_data   # returning user – skip onboarding

    print("\nLooks like you're new here. Let me set up your profile.")

    name = input("  What should I call you? (press Enter to keep your ID): ").strip()
    if not name:
        name = user_id

    prefs = input(
        "  Response style preference – technical / casual / detailed [technical]: "
    ).strip().lower() or "technical"

    update_profile(user_id, {"name": name, "preferences": prefs})
    user_data["profile"]["name"]        = name
    user_data["profile"]["preferences"] = prefs

    print(f"  Profile saved: {name} ({prefs} mode).")
    return user_data


# ── Main loop ─────────────────────────────────────────────────────────────────

def main() -> None:
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   MCP Capstone – Context-Aware Scalable AI Agent         ║")
    print("╚══════════════════════════════════════════════════════════╝")

    # Identify the user
    user_id = input("\nEnter your user ID (or press Enter for 'demo_user'): ").strip()
    if not user_id:
        user_id = "demo_user"

    # Load or create memory, then onboard if new
    user_data = load_user(user_id)
    user_data = _onboard_new_user(user_id, user_data)
    _greet_user(user_id, user_data)

    print("\nType your message below. Type 'exit' to quit.\n")

    # Conversation loop
    while True:
        try:
            query = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            sys.exit(0)

        if not query:
            continue

        if query.lower() in {"exit", "quit", "bye"}:
            name = user_data["profile"].get("name", user_id)
            print(f"\nGoodbye, {name}! Your memory has been saved. See you next time.")
            sys.exit(0)

        # Run the full pipeline
        reply = run_pipeline(user_id, query)

        print(f"\nAgent: {reply}\n")

        # Refresh local user_data reference after pipeline may have mutated it
        user_data = load_user(user_id)


if __name__ == "__main__":
    main()
