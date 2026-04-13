import os
import time

from dotenv import load_dotenv
from openai import OpenAI

from run_metadata import RunMetadata
from run_logger import RunLogger
from feedback_collector import FeedbackCollector

load_dotenv()

PROMPT_VERSIONS = {
    "v1.0": "You are a concise assistant.",
    "v2.0": "You are a detailed, structured assistant.",
    "v3.0": "You are an expert-level assistant with reasoning clarity.",
}


def run_agent_with_feedback(input_text: str, prompt_version: str, feedback_enabled: bool = True) -> str:
    # Validate prompt version
    if prompt_version not in PROMPT_VERSIONS:
        raise ValueError(f"Unknown prompt_version '{prompt_version}'. Choose from: {', '.join(PROMPT_VERSIONS)}")

    # Resolve API key
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError("No API key found. Set OPENAI_API_KEY or OPENROUTER_API_KEY in your .env file.")

    base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    model_name = os.getenv("MODEL_NAME", "openai/gpt-4o-mini")

    # Stamp run identity
    metadata = RunMetadata(prompt_version=prompt_version, model_name=model_name)

    # Call the model and measure latency
    client = OpenAI(api_key=api_key, base_url=base_url)

    start = time.perf_counter()
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": PROMPT_VERSIONS[prompt_version]},
            {"role": "user",   "content": input_text},
        ],
    )
    latency_seconds = round(time.perf_counter() - start, 4)

    # Extract output and token usage
    output_text = response.choices[0].message.content or ""

    token_usage = None
    if response.usage:
        token_usage = {
            "prompt_tokens":     response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens":      response.usage.total_tokens,
        }

    # Show the response
    print(f"\n{'='*60}")
    print("Model Response:")
    print(f"{'='*60}")
    print(output_text)
    print(f"{'='*60}\n")

    # Collect feedback
    feedback = FeedbackCollector().collect(feedback_enabled=feedback_enabled)

    # Assemble log entry
    entry = {
        **metadata.to_dict(),
        "input":           input_text,
        "output":          output_text,
        "latency_seconds": latency_seconds,
    }
    if token_usage:
        entry["token_usage"] = token_usage
    if feedback:
        entry["feedback"] = feedback

    # Save to log
    RunLogger().append(entry)
    print(f"[Logged] run_id: {metadata.run_id}")

    return output_text
