class FeedbackCollector:
    """Collects a 1–5 rating and an optional comment from the user."""

    def collect(self, feedback_enabled: bool = True):
        if not feedback_enabled:
            return None

        print("\n--- Feedback ---")
        rating = self._get_rating()
        comment = input("Optional comment (press Enter to skip): ").strip()

        return {"rating": rating, "comment": comment}

    def _get_rating(self) -> int:
        while True:
            raw = input("Rate this response (1–5): ").strip()
            try:
                rating = int(raw)
                if 1 <= rating <= 5:
                    return rating
                print("  Please enter a number between 1 and 5.")
            except ValueError:
                print("  Invalid input. Enter a whole number.")
