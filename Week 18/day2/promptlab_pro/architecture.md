# PromptLab Pro — Architecture Explanation

## What This System Is

PromptLab Pro is an A/B testing engine for LLM prompts. The core idea is simple: you have two versions of a system prompt — a control and a variation. You want to know, scientifically, which one produces better responses. To answer that you need to run both versions against the same set of inputs, measure every response, aggregate the numbers, and compare. That is exactly what this system does.

---

## The Problem It Solves

When you change a system prompt, you cannot tell by looking at one or two responses whether the change helped or hurt. Human perception is biased. A single good response from the variation might be luck. What you need is 20, 50, or 100 inputs run through both versions — with consistent metrics recorded for every single one — so you can compare averages and make a data-driven decision.

That is A/B testing. PromptLab Pro implements it for LLMs.

---

## Module Responsibilities

Every file in this project has exactly one job. This is called separation of concerns.

```
prompts.py      → Stores what the prompts say
evaluator.py    → Knows how to measure one response
batch_runner.py → Knows how to run all the calls
aggregator.py   → Knows how to compute averages and detect problems
dashboard.py    → Knows how to display results visually
main.py         → Connects everything together
```

None of these modules know about each other's internals. batch_runner knows evaluator exists, but it does not care how evaluator counts words. If you change the metric formula inside evaluator, batch_runner does not change at all.

---

## Data Flow — Step by Step

```
Step 1: main.py defines TEST_INPUTS (20 questions)
        and reads both prompt strings from PROMPT_VERSIONS

        ↓

Step 2: batch_runner.run_batch_test() receives
        the inputs and both prompt strings.

        For each input (20 iterations):
          → Call LLM with control prompt   → get text_a, latency_a, tokens_a
          → Call LLM with variation prompt → get text_b, latency_b, tokens_b
          → evaluator.evaluate(text_a, latency_a, tokens_a) → metrics dict A
          → evaluator.evaluate(text_b, latency_b, tokens_b) → metrics dict B
          → Append both to results["control"] and results["variation"]

        Returns: {
          "control":   [ {word_count, latency, tokens, rating}, × 20 ],
          "variation": [ {word_count, latency, tokens, rating}, × 20 ]
        }

        ↓

Step 3: aggregator.aggregate_metrics(results)
        Loops through both lists.
        Computes the average of each metric across all 20 inputs.

        Returns: {
          "control":   { average_word_count, average_latency, average_tokens, average_user_rating },
          "variation": { average_word_count, average_latency, average_tokens, average_user_rating }
        }

        ↓

Step 4: aggregator.detect_regression(summary)
        Compares variation rating against control rating.
        If variation < control → returns a warning string.
        If variation >= control → returns None.

        ↓

Step 5: main.py prints the summary table and regression result.
        Writes results_log.json (raw per-input data, 40 entries).
        Writes summary_log.json (aggregated averages, 2 entries).

        ↓

Step 6: dashboard.py (run separately via streamlit)
        Reads results_log.json.
        Calls aggregate_metrics() again on the loaded data.
        Renders 4 sections: summary metrics, comparison table,
        4 bar charts, regression detection banner.
```

---

## Why Each Module Is Separate

**prompts.py is separate** so that the prompt text lives in one place. If you need to edit the variation prompt, you open prompts.py. You do not search through batch_runner or main to find where the text is defined.

**evaluator.py is separate** so that metric logic is isolated. If you want to add a new metric — say, sentence count or average word length — you add it inside evaluator.py and nowhere else. The batch runner just calls evaluate() and gets the new metric automatically.

**batch_runner.py is separate** so that the loop logic is isolated from the aggregation logic. Running calls and computing averages are two different responsibilities. If you wanted to add rate limiting or retry logic, you add it to batch_runner. You do not touch aggregator.

**aggregator.py is separate** so that you can re-aggregate without re-running the LLM calls. If you save results_log.json and run the dashboard the next day, it reads the saved file and re-aggregates. The expensive API calls already happened. You do not pay for them again.

**dashboard.py is separate** so that the visual layer is completely independent from the data layer. The dashboard does not care how results were produced. It only reads a JSON file and renders it.

---

## The A/B Testing Logic in Detail

An A/B test has two conditions: a control (the existing version, your baseline) and a variation (the new version you want to test). You run both conditions against the same stimuli — in this case, the same 20 input questions — so that the only variable that changes between the two groups is the system prompt. Everything else is identical: same model, same inputs, same measurement method.

By holding everything else constant, any difference you observe in the metrics is attributable to the prompt difference. That is the scientific discipline that makes the comparison valid.

---

## The Four Metrics and What They Tell You

**word_count** measures verbosity. The control prompt is designed to be concise, so its word count should be lower. The variation prompt asks for detailed structured reasoning, so its word count should be higher. If both prompts produce similar word counts, the variation prompt is not doing what it was designed to do.

**latency_seconds** measures response time. Longer, more detailed responses generally take longer to generate because more tokens are being produced. If the variation prompt increases latency significantly, that is a cost: users wait longer. You need to weigh the quality improvement against the speed cost.

**total_tokens** measures API cost. Every token costs money. A variation that produces twice as many tokens costs approximately twice as much per call. This metric lets you quantify that cost before you decide to deploy the variation.

**user_rating** is the quality signal. In this project it is simulated as a random integer between 3 and 5, which stands in for a human reviewer's score. In a real system you would replace the simulation with actual user feedback — the same feedback collection pattern we built in day one. The rating is the primary signal for regression detection.

---

## Regression Detection

A regression means the new version is performing worse than the baseline. In this system, regression is defined as: variation's average_user_rating is strictly less than control's average_user_rating.

This is the minimum viable regression check. It answers the question: "Did my change make things worse?" If the answer is yes, you do not ship the variation. You go back and revise it.

In production, regression detection is more sophisticated. It uses statistical significance tests, confidence intervals, and minimum sample sizes before triggering an alert. But the principle is identical to what we have here: compare a number from variation against the same number from control, and flag it if variation lost.

---

## The Dashboard's Role

The Streamlit dashboard is the presentation layer. It reads results_log.json and makes the data visual. Bar charts make it immediately obvious which version has higher ratings, lower latency, and fewer tokens. A table makes the exact numbers readable. The regression banner makes the decision clear: green means ship it, red means don't.

The dashboard does not run the experiment. It only reads the results file and renders it. This means you can re-open the dashboard days later, share the URL with a colleague, or embed it in a report — and the underlying data is always the same saved JSON file.

---

## What Can Be Extended

Adding a third prompt version requires adding one line to PROMPT_VERSIONS in prompts.py and passing it to run_batch_test as a third argument. The aggregator and dashboard would need minor additions to handle a third key, but the core logic does not change.

Adding a new metric requires adding the computation to the evaluate() method in evaluator.py and adding the corresponding average calculation to aggregate_metrics() in aggregator.py. The dashboard would then need one more chart, but the data pipeline is automatic.

Replacing simulated ratings with real user ratings requires setting simulate_rating=False in the evaluate() call inside batch_runner and collecting a human score before calling evaluate(). The rest of the system — aggregation, regression detection, dashboard — works without any changes.
