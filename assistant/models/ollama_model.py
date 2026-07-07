"""Local Ollama integration abstraction."""

from __future__ import annotations

import json
import shutil
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class OllamaModelInfo:
    """Installed Ollama model metadata."""

    name: str
    size: int | None = None
    modified_at: str | None = None


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

    def is_installed(self) -> bool:
        """Return whether the Ollama executable is available."""
        return shutil.which("ollama") is not None

    def is_running(self) -> bool:
        """Return whether the local Ollama service responds."""
        try:
            self._request_json("/api/tags", method="GET")
        except (OSError, URLError, HTTPError, json.JSONDecodeError, ValueError):
            return False
        return True

    def list_models(self) -> list[OllamaModelInfo]:
        """List installed local Ollama models."""
        data = self._request_json("/api/tags", method="GET")
        models = data.get("models", [])
        if not isinstance(models, list):
            raise ValueError("Unexpected Ollama model list response.")

        result: list[OllamaModelInfo] = []
        for item in models:
            if not isinstance(item, dict):
                continue
            name = item.get("name") or item.get("model")
            if isinstance(name, str):
                size = item.get("size")
                result.append(
                    OllamaModelInfo(
                        name=name,
                        size=size if isinstance(size, int) else None,
                        modified_at=item.get("modified_at")
                        if isinstance(item.get("modified_at"), str)
                        else None,
                    )
                )
        return result

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float,
        top_p: float,
        context_size: int,
    ) -> dict[str, Any]:
        """Generate a complete chat response through the local Ollama API."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "num_ctx": context_size,
            },
        }
        data = self._request_json("/api/chat", payload=payload)
        message = data.get("message", {})
        content = message.get("content", "") if isinstance(message, dict) else ""
        return {"model": self.model, "response": content, "raw": data}

    def stream_chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float,
        top_p: float,
        context_size: int,
    ) -> Iterator[str]:
        """Stream chat response chunks from the local Ollama API."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "num_ctx": context_size,
            },
        }
        request = self._build_request("/api/chat", payload=payload)
        with urlopen(request, timeout=self.timeout) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue
                data = json.loads(line)
                if not isinstance(data, dict):
                    continue
                message = data.get("message", {})
                if isinstance(message, dict):
                    content = message.get("content", "")
                    if isinstance(content, str) and content:
                        yield content
                if data.get("done"):
                    break

    def generate(self, prompt: str) -> dict[str, Any]:
        """Generate a response through the local Ollama HTTP API."""
        payload = {"model": self.model, "prompt": prompt, "stream": False}

        try:
            data = self._request_json("/api/generate", payload=payload)
        except (OSError, URLError, HTTPError, json.JSONDecodeError) as exc:
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

    def _request_json(
        self,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        method: str = "POST",
    ) -> dict[str, Any]:
        """Send a request and decode the JSON response."""
        request = self._build_request(path, payload=payload, method=method)
        with urlopen(request, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Unexpected Ollama response.")
        return data

    def _build_request(
        self,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        method: str = "POST",
    ) -> Request:
        """Build an Ollama HTTP request."""
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        return Request(
            f"{self.base_url.rstrip('/')}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method=method,
        )
