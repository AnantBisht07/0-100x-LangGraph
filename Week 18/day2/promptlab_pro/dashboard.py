"""
dashboard.py
------------
Streamlit dashboard for visualising PromptLab Pro A/B test results.

Run with:
    streamlit run dashboard.py

The dashboard reads results_log.json written by main.py and renders:
  1. Input summary
  2. Side-by-side metrics comparison table
  3. Bar charts for every metric
  4. Regression detection banner
"""

import json
import os

import pandas as pd
import streamlit as st

from aggregator import aggregate_metrics, detect_regression

RESULTS_FILE = "results_log.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_results() -> dict | None:
    """Load batch results from the JSON file written by main.py."""
    if not os.path.exists(RESULTS_FILE):
        return None
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_comparison_df(summary: dict) -> pd.DataFrame:
    """
    Convert the aggregated summary into a DataFrame suitable for display
    and charting. Rows = metrics, Columns = control / variation.
    """
    labels = {
        "average_word_count":  "Avg Word Count",
        "average_latency":     "Avg Latency (s)",
        "average_tokens":      "Avg Tokens",
        "average_user_rating": "Avg User Rating",
    }
    rows = []
    for key, label in labels.items():
        rows.append({
            "Metric":    label,
            "Control":   summary.get("control",   {}).get(key, 0),
            "Variation": summary.get("variation", {}).get(key, 0),
        })
    return pd.DataFrame(rows).set_index("Metric")


# ---------------------------------------------------------------------------
# Dashboard layout
# ---------------------------------------------------------------------------

def render_dashboard() -> None:
    st.set_page_config(page_title="PromptLab Pro", layout="wide")
    st.title("PromptLab Pro — A/B Evaluation Dashboard")

    results = _load_results()

    if results is None:
        st.warning(
            f"No results file found (`{RESULTS_FILE}`). "
            "Run `python main.py` first to generate results."
        )
        return

    summary = aggregate_metrics(results)

    # ── 1. Input Summary ────────────────────────────────────────────────────
    st.header("1. Input Summary")
    n_inputs = len(results.get("control", []))
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Test Inputs", n_inputs)
    col2.metric("Prompt Versions", 2)
    col3.metric("Total LLM Calls", n_inputs * 2)

    st.divider()

    # ── 2. Metrics Comparison Table ──────────────────────────────────────────
    st.header("2. Metrics Comparison")
    df = _build_comparison_df(summary)
    st.dataframe(df.style.format("{:.3f}"), use_container_width=True)

    st.divider()

    # ── 3. Bar Charts ────────────────────────────────────────────────────────
    st.header("3. Visual Comparison")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Avg User Rating")
        rating_data = pd.DataFrame({
            "Version": ["Control", "Variation"],
            "Avg User Rating": [
                summary["control"]["average_user_rating"],
                summary["variation"]["average_user_rating"],
            ],
        }).set_index("Version")
        st.bar_chart(rating_data)

        st.subheader("Avg Word Count")
        word_data = pd.DataFrame({
            "Version": ["Control", "Variation"],
            "Avg Word Count": [
                summary["control"]["average_word_count"],
                summary["variation"]["average_word_count"],
            ],
        }).set_index("Version")
        st.bar_chart(word_data)

    with chart_col2:
        st.subheader("Avg Latency (seconds)")
        latency_data = pd.DataFrame({
            "Version": ["Control", "Variation"],
            "Avg Latency (s)": [
                summary["control"]["average_latency"],
                summary["variation"]["average_latency"],
            ],
        }).set_index("Version")
        st.bar_chart(latency_data)

        st.subheader("Avg Token Usage")
        token_data = pd.DataFrame({
            "Version": ["Control", "Variation"],
            "Avg Tokens": [
                summary["control"]["average_tokens"],
                summary["variation"]["average_tokens"],
            ],
        }).set_index("Version")
        st.bar_chart(token_data)

    st.divider()

    # ── 4. Regression Detection ──────────────────────────────────────────────
    st.header("4. Regression Detection")
    regression_msg = detect_regression(summary)
    if regression_msg:
        st.error(regression_msg)
    else:
        st.success(
            "✅  No regression detected. Variation is performing as well as or "
            "better than control on user rating."
        )


if __name__ == "__main__":
    render_dashboard()
