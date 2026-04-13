import uuid
from datetime import datetime, timezone


class RunMetadata:
    """Stamps each run with a unique ID, timestamp, prompt version, and model name."""

    def __init__(self, prompt_version: str, model_name: str):
        self.run_id = str(uuid.uuid4())
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.prompt_version = prompt_version
        self.model_name = model_name

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "prompt_version": self.prompt_version,
            "model": self.model_name,
        }
