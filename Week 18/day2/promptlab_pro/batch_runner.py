"""
batch_runner.py
---------------
Executes LLM calls for every combination of (input, prompt_version)
and returns structured per-input metrics for both versions.

This is the engine of the A/B test. It loops through every test input,
runs it against both the control and variation prompt, measures everything,
and returns a results dictionary that the aggregator and dashboard consume.
"""

import os
import time

from dotenv import load_dotenv
from openai import OpenAI

from evaluator import Evaluator
from prompts import PROMPT_VERSIONS

load_dotenv()


def _get_client() -> tuple[OpenAI, str]:
    """
    Resolve API credentials and return a configured OpenAI client
    along with the model name to use.

    Returns:
        Tuple of (OpenAI client, model name string).

    Raises:
        EnvironmentError: If no API key is found in the environment.
    """
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "No API key found. Set OPENAI_API_KEY or OPENROUTER_API_KEY in your .env file."
        )
    base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    model_name = os.getenv("MODEL_NAME", "openai/gpt-4o-mini")
    client = OpenAI(api_key=api_key, base_url=base_url)
    return client, model_name


def _call_llm(client: OpenAI, model: str, system_prompt: str, user_input: str) -> tuple[str, float, int | None]:
    """
    Make a single LLM call and return the response text, latency, and token count.

    Args:
        client:        Configured OpenAI client.
        model:         Model identifier string.
        system_prompt: The system prompt for this version.
        user_input:    The user's question or test input.

    Returns:
        Tuple of (response_text, latency_seconds, total_tokens or None).
    """
    start = time.perf_counter()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_input},
        ],
    )
    latency = round(time.perf_counter() - start, 4)

    text = response.choices[0].message.content or ""
    tokens = response.usage.total_tokens if response.usage else None

    return text, latency, tokens


def run_batch_test(inputs: list[str], prompt_a: str, prompt_b: str) -> dict:
    """
    Run every input against both prompt versions and collect metrics.

    For each input in `inputs`:
      1. Call the LLM with prompt_a (control).
      2. Call the LLM with prompt_b (variation).
      3. Evaluate both responses with the Evaluator.
      4. Append the metrics to the corresponding results list.

    Args:
        inputs:   List of test input strings.
        prompt_a: System prompt string for the control version.
        prompt_b: System prompt string for the variation version.

    Returns:
        dict with two keys — "control" and "variation" — each mapping
        to a list of per-input metric dictionaries.

        Example:
        {
            "control":   [ {"word_count": 42, "latency_seconds": 1.2, ...}, ... ],
            "variation": [ {"word_count": 91, "latency_seconds": 1.8, ...}, ... ]
        }
    """
    client, model = _get_client()
    evaluator = Evaluator()

    results = {"control": [], "variation": []}
    total = len(inputs)

    for i, user_input in enumerate(inputs, start=1):
        print(f"  Running input {i}/{total}: {user_input[:60]}...")

        # --- Control ---
        text_a, latency_a, tokens_a = _call_llm(client, model, prompt_a, user_input)
        metrics_a = evaluator.evaluate(text_a, latency_a, tokens_a)
        metrics_a["input"] = user_input
        metrics_a["output"] = text_a
        results["control"].append(metrics_a)

        # --- Variation ---
        text_b, latency_b, tokens_b = _call_llm(client, model, prompt_b, user_input)
        metrics_b = evaluator.evaluate(text_b, latency_b, tokens_b)
        metrics_b["input"] = user_input
        metrics_b["output"] = text_b
        results["variation"].append(metrics_b)

    return results
