"""Local Ollama integration abstraction."""

from __future__ import annotations

from typing import Any


class OllamaModel:
    """A thin wrapper around local Ollama-compatible requests."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen3") -> None:
        self.base_url = base_url
        self.model = model

    def generate(self, prompt: str) -> dict[str, Any]:
        """Return a simple structured response when Ollama is unavailable."""
        return {"model": self.model, "prompt": prompt, "response": "Local model not running"}
