"""Local Ollama integration abstraction."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


class OllamaModel:
    """A thin wrapper around local Ollama-compatible requests."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen3",
        timeout: int = 30,
    ) -> None:
        self.base_url = base_url
        self.model = model
        self.timeout = timeout

    def generate(self, prompt: str) -> dict[str, Any]:
        """Generate a response through the local Ollama HTTP API."""
        payload = json.dumps(
            {"model": self.model, "prompt": prompt, "stream": False}
        ).encode("utf-8")
        request = Request(
            f"{self.base_url.rstrip('/')}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, json.JSONDecodeError) as exc:
            return {
                "model": self.model,
                "prompt": prompt,
                "error": f"Ollama request failed: {exc}",
            }

        return {
            "model": self.model,
            "prompt": prompt,
            "response": data.get("response", ""),
        }
