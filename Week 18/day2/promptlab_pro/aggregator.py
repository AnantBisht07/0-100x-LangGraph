"""
aggregator.py
-------------
Computes summary statistics across all batch results and detects regressions.

The aggregator is intentionally separate from the batch runner so that
aggregation can be run on saved JSON results without re-running the LLM calls.
This makes it possible to re-analyze historical runs at any time.
"""


def _average(values: list) -> float:
    """
    Compute the arithmetic mean of a list of numbers.
    Returns 0.0 if the list is empty to avoid ZeroDivisionError.
    """
    valid = [v for v in values if v is not None]
    return round(sum(valid) / len(valid), 4) if valid else 0.0


def aggregate_metrics(results: dict) -> dict:
    """
    Compute per-version averages across all batch inputs.

    Reads the list of per-input metric dicts for each version and
    computes the mean of word_count, latency_seconds, total_tokens,
    and user_rating.

    Args:
        results: The dictionary returned by run_batch_test().
                 Structure: {"control": [...], "variation": [...]}

    Returns:
        dict: Nested summary with one entry per version.

        Example:
        {
            "control": {
                "average_word_count": 42.3,
                "average_latency": 1.21,
                "average_tokens": 118.0,
                "average_user_rating": 3.8
            },
            "variation": { ... }
        }
    """
    summary = {}

    for version, entries in results.items():
        summary[version] = {
            "average_word_count":   _average([e.get("word_count")      for e in entries]),
            "average_latency":      _average([e.get("latency_seconds") for e in entries]),
            "average_tokens":       _average([e.get("total_tokens")    for e in entries]),
            "average_user_rating":  _average([e.get("user_rating")     for e in entries]),
        }

    return summary


def detect_regression(summary: dict) -> str | None:
    """
    Compare variation against control on the user_rating metric.

    A regression is flagged when the variation's average rating is
    strictly lower than the control's. This is the minimal regression
    signal — production systems would add confidence intervals and
    sample-size thresholds before alerting.

    Args:
        summary: The dictionary returned by aggregate_metrics().

    Returns:
        str: A warning message if a regression is detected.
        None: If no regression is found or data is missing.
    """
    control_rating   = summary.get("control",   {}).get("average_user_rating")
    variation_rating = summary.get("variation", {}).get("average_user_rating")

    if control_rating is None or variation_rating is None:
        return None

    if variation_rating < control_rating:
        diff = round(control_rating - variation_rating, 4)
        return (
            f"⚠  Potential regression detected. "
            f"Variation rating ({variation_rating}) is {diff} points "
            f"below control ({control_rating})."
        )

    return None
