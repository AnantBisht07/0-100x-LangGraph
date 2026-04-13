from agent_executor import PROMPT_VERSIONS, run_agent_with_feedback
from run_logger import RunLogger


def main():
    print("=" * 60)
    print("  Feedback-Aware Evaluation Pipeline")
    print("=" * 60)

    query = input("\nEnter your query: ").strip()
    if not query:
        print("Query cannot be empty. Exiting.")
        return

    print("\nAvailable prompt versions:")
    for version, description in PROMPT_VERSIONS.items():
        print(f"  {version}: \"{description}\"")

    while True:
        prompt_version = input("\nSelect prompt version: ").strip()
        if prompt_version in PROMPT_VERSIONS:
            break
        print(f"  Invalid. Choose from: {', '.join(PROMPT_VERSIONS)}")

    try:
        run_agent_with_feedback(query, prompt_version)
    except EnvironmentError as e:
        print(f"\n[Config Error] {e}")
        return
    except Exception as e:
        print(f"\n[Error] {e}")
        return

    show = input("\nShow average ratings by prompt version? (y/n): ").strip().lower()
    if show == "y":
        RunLogger().compute_average_rating()


if __name__ == "__main__":
    main()
