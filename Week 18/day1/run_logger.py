import json
import os

LOG_FILE = "runs_log.json"


class RunLogger:
    """Appends run entries to an append-only JSON log file."""

    def __init__(self, log_path: str = LOG_FILE):
        self.log_path = log_path

    def _load_existing(self) -> list:
        if not os.path.exists(self.log_path):
            return []
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []  # corrupted file — start fresh

    def append(self, entry: dict) -> None:
        entries = self._load_existing()
        entries.append(entry)
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)

    def compute_average_rating(self) -> None:
        """Group runs by prompt_version and print the average rating for each."""
        entries = self._load_existing()

        if not entries:
            print("No runs logged yet.")
            return

        version_ratings = {}
        for entry in entries:
            version = entry.get("prompt_version", "unknown")
            feedback = entry.get("feedback")
            if feedback and isinstance(feedback.get("rating"), int):
                version_ratings.setdefault(version, []).append(feedback["rating"])

        if not version_ratings:
            print("No rated runs found.")
            return

        print("\n=== Average Ratings by Prompt Version ===")
        for version, ratings in sorted(version_ratings.items()):
            avg = sum(ratings) / len(ratings)
            print(f"  {version}: {avg:.2f}  (n={len(ratings)} runs)")
        print("==========================================\n")
