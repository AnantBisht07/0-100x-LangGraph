"""
main.py
-------
Entry point for PromptLab Pro.

Steps:
  1. Define 20 diverse test inputs.
  2. Run the A/B batch test (control vs variation).
  3. Aggregate results into summary metrics.
  4. Detect regression.
  5. Save raw results and summary to JSON.
  6. Instruct the user to launch the Streamlit dashboard.
"""

import json

from aggregator import aggregate_metrics, detect_regression
from batch_runner import run_batch_test
from prompts import PROMPT_VERSIONS

# ---------------------------------------------------------------------------
# Test Inputs — 20 diverse questions covering different reasoning types
# ---------------------------------------------------------------------------
TEST_INPUTS = [
    "What is machine learning?",
    "Explain the difference between supervised and unsupervised learning.",
    "What is a neural network and how does it work?",
    "How does backpropagation work?",
    "What is overfitting and how do you prevent it?",
    "Explain the concept of gradient descent.",
    "What is a transformer model?",
    "How does attention mechanism work in transformers?",
    "What is the difference between GPT and BERT?",
    "Explain tokenization in NLP.",
    "What is prompt engineering?",
    "How do vector embeddings represent meaning?",
    "What is retrieval-augmented generation (RAG)?",
    "Explain the concept of fine-tuning a language model.",
    "What is the difference between zero-shot and few-shot learning?",
    "How do you evaluate the quality of an LLM response?",
    "What is hallucination in AI and why does it happen?",
    "Explain the role of temperature in language model sampling.",
    "What is the context window of a language model?",
    "How does chain-of-thought prompting improve reasoning?",
]

RESULTS_FILE  = "results_log.json"
SUMMARY_FILE  = "summary_log.json"


def main() -> None:
    print("=" * 60)
    print("  PromptLab Pro — A/B Batch Evaluation")
    print("=" * 60)
    print(f"\nTest inputs : {len(TEST_INPUTS)}")
    print(f"Versions    : control vs variation")
    print(f"Total calls : {len(TEST_INPUTS) * 2}\n")

    # ------------------------------------------------------------------
    # 1. Run batch test
    # ------------------------------------------------------------------
    print("Running batch test...")
    prompt_a = PROMPT_VERSIONS["control"]
    prompt_b = PROMPT_VERSIONS["variation"]

    try:
        results = run_batch_test(TEST_INPUTS, prompt_a, prompt_b)
    except EnvironmentError as e:
        print(f"\n[Config Error] {e}")
        return

    # ------------------------------------------------------------------
    # 2. Aggregate metrics
    # ------------------------------------------------------------------
    summary = aggregate_metrics(results)

    # ------------------------------------------------------------------
    # 3. Regression detection — print to console immediately
    # ------------------------------------------------------------------
    regression_msg = detect_regression(summary)

    print("\n" + "=" * 60)
    print("  Results Summary")
    print("=" * 60)

    for version, metrics in summary.items():
        print(f"\n  [{version.upper()}]")
        for metric, value in metrics.items():
            print(f"    {metric:<25}: {value}")

    print()
    if regression_msg:
        print(regression_msg)
    else:
        print("✅  No regression detected.")

    # ------------------------------------------------------------------
    # 4. Save raw results and summary to JSON
    # ------------------------------------------------------------------
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to : {RESULTS_FILE}")
    print(f"Summary saved to : {SUMMARY_FILE}")

    # ------------------------------------------------------------------
    # 5. Dashboard instructions
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Launch Dashboard")
    print("=" * 60)
    print("\nTo view the visual comparison dashboard, run:")
    print("\n    streamlit run dashboard.py\n")


if __name__ == "__main__":
    main()
