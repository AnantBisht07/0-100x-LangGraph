"""
evaluator.py
------------
Computes evaluation metrics for a single LLM response.

Keeping evaluation logic isolated here means the metrics we compute
can be changed or extended without touching the batch runner or aggregator.
Any new metric (e.g. sentence count, readability score) is added here only.
"""

import random
from typing import Optional


class Evaluator:
    """
    Computes a standard set of quality and performance metrics
    for one LLM response.

    Metrics:
        word_count          — length proxy for verbosity
        latency_seconds     — response time from the API call
        total_tokens        — API cost proxy (if provider returns usage)
        simulated_rating    — random int 3–5 standing in for human feedback
    """

    def evaluate(
        self,
        response_text: str,
        latency_seconds: float,
        total_tokens: Optional[int] = None,
        simulate_rating: bool = True,
    ) -> dict:
        """
        Compute metrics for one response.

        Args:
            response_text:    The raw text returned by the model.
            latency_seconds:  Wall-clock time of the API call in seconds.
            total_tokens:     Total tokens consumed (prompt + completion).
                              Pass None if the provider did not return usage.
            simulate_rating:  When True, generate a random rating 3–5 to
                              simulate user feedback. Set False for real ratings.

        Returns:
            dict: Structured metrics ready for storage and aggregation.
        """
        word_count = self._count_words(response_text)
        user_rating = random.randint(3, 5) if simulate_rating else None

        metrics = {
            "word_count": word_count,
            "latency_seconds": round(latency_seconds, 4),
            "user_rating": user_rating,
        }

        # Only include total_tokens if the provider returned usage data
        if total_tokens is not None:
            metrics["total_tokens"] = total_tokens

        return metrics

    def _count_words(self, text: str) -> int:
        """
        Count whitespace-delimited words in a string.

        Args:
            text: The response text to count.

        Returns:
            int: Number of words. Returns 0 for empty or whitespace-only text.
        """
        return len(text.split()) if text.strip() else 0
