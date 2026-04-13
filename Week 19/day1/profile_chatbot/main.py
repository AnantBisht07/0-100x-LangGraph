"""
main.py
-------
CLI entry point for the Profile-Aware Chatbot.

Conversation flow:
  1. Ask for username.
  2. Load existing profile or create a new one.
  3. Greet the user — mention last topic if returning.
  4. Enter conversation loop:
       - Accept user input.
       - Generate memory-injected response.
       - Print response.
       - Repeat until user types 'exit'.
  5. Ask what topic was discussed today.
  6. Save topic to profile for the next session.
"""

from profile_manager import ProfileManager
from chatbot import generate_response

VALID_TONES = ["friendly", "formal", "concise", "detailed", "humorous"]


def _ask_username() -> str:
    """Prompt for a username and return it stripped and lowercased."""
    username = input("\nEnter your username: ").strip().lower()
    while not username:
        print("  Username cannot be empty.")
        username = input("Enter your username: ").strip().lower()
    return username


def _ask_tone() -> str:
    """
    Prompt a new user to select a preferred response tone.
    Re-prompts until a valid choice is made.
    """
    print("\nAvailable tones:")
    for tone in VALID_TONES:
        print(f"  - {tone}")

    while True:
        tone = input("Choose your preferred tone: ").strip().lower()
        if tone in VALID_TONES:
            return tone
        print(f"  Invalid tone. Choose from: {', '.join(VALID_TONES)}")


def _greet_user(profile: dict, is_new: bool) -> None:
    """
    Print a personalised greeting based on whether the user is new
    or returning, and surface the last discussed topic if available.

    Args:
        profile: The user's profile dictionary.
        is_new:  True if the profile was just created this session.
    """
    name       = profile["name"]
    last_topic = profile.get("last_topic")

    if is_new:
        print(f"\nNice to meet you, {name}! Your profile has been created.")
        print(f"Preferred tone set to: {profile['preferred_tone'].capitalize()}")
    else:
        print(f"\nWelcome back, {name}!")
        if last_topic:
            print(f"Last time we discussed: {last_topic}")
        else:
            print("No previous topic on record — let's start fresh.")

    print("\nType your question below. Type 'exit' to end the session.\n")


def _conversation_loop(username: str, profile: dict, manager: ProfileManager) -> None:
    """
    Run the interactive conversation until the user types 'exit'.

    After the loop ends, ask the user what topic was discussed and
    persist it to the profile for the next session.

    Args:
        username: The lowercase key used to update the profile.
        profile:  The current user's profile dictionary.
        manager:  The ProfileManager instance used to save updates.
    """
    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("\nEnding session...")
            break

        try:
            response = generate_response(user_input, profile)
            print(f"\nAssistant: {response}\n")
        except EnvironmentError as e:
            print(f"\n[Config Error] {e}")
            return
        except Exception as e:
            print(f"\n[Error] {e}")
            return

    # After the loop — save today's topic to the profile
    print("-" * 50)
    topic = input("What topic did we discuss today? (press Enter to skip): ").strip()
    if topic:
        manager.update_last_topic(username, topic)
        print(f"Got it. I'll remember '{topic}' for next time.")
    else:
        print("No topic saved. See you next time!")


def main() -> None:
    """
    Orchestrate the full session: load or create profile, greet,
    converse, then save the updated profile.
    """
    print("=" * 50)
    print("  Profile-Aware Chatbot")
    print("=" * 50)

    manager  = ProfileManager()
    username = _ask_username()
    profile  = manager.get_profile(username)

    if profile is None:
        # New user — collect display name and tone preference
        name    = input("We don't have a profile for you yet. What is your name? ").strip()
        if not name:
            name = username.capitalize()
        tone    = _ask_tone()
        profile = manager.create_profile(username, name, tone)
        is_new  = True
    else:
        is_new = False

    _greet_user(profile, is_new)
    _conversation_loop(username, profile, manager)

    print("\nSession complete. Goodbye!\n")


if __name__ == "__main__":
    main()
