"""Conversation manager for local Ollama chat sessions."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError

from assistant.config.settings import ConversationSettings
from assistant.core.chat_session import ChatSession, TokenUsage
from assistant.models.ollama_model import OllamaModel
from assistant.models.ollama_model import OllamaModelInfo


@dataclass(frozen=True)
class ChatResult:
    """Completed chat result."""

    model: str
    response: str
    usage: TokenUsage
    error: str | None = None


class ModelManager:
    """Discover and select installed Ollama models."""

    def __init__(self, client: OllamaModel, default_model: str) -> None:
        self.client = client
        self.current_model = default_model
        self.client.model = default_model

    def list_models(self) -> list[OllamaModelInfo]:
        """Return installed Ollama models."""
        return self.client.list_models()

    def switch(self, model_name: str) -> str:
        """Select an installed model by name or untagged base name."""
        resolved = self.resolve(model_name)
        if resolved is None:
            raise ValueError(f"Model '{model_name}' is not installed.")
        self.current_model = resolved
        self.client.model = resolved
        return self.current_model

    def resolve(self, model_name: str) -> str | None:
        """Resolve a configured or user-provided model name."""
        installed = [model.name for model in self.list_models()]
        if model_name in installed:
            return model_name
        tagged_name = f"{model_name}:latest"
        if tagged_name in installed:
            return tagged_name
        matches = [name for name in installed if name.split(":", 1)[0] == model_name]
        if len(matches) == 1:
            return matches[0]
        return None


class StreamingResponseHandler:
    """Collect streamed chunks while yielding them to callers."""

    def collect(self, chunks: Iterator[str]) -> Iterator[str]:
        """Yield non-empty response chunks."""
        for chunk in chunks:
            if chunk:
                yield chunk


class ConversationManager:
    """Coordinate local Ollama chat without tool execution."""

    def __init__(
        self,
        settings: ConversationSettings,
        model: OllamaModel | None = None,
    ) -> None:
        self.settings = settings
        self.client = model or OllamaModel(
            base_url=settings.base_url,
            model=settings.default_model,
            timeout=settings.request_timeout,
        )
        self.models = ModelManager(self.client, settings.default_model)
        self.session = ChatSession(settings)
        self.streaming = StreamingResponseHandler()

    def status(self) -> dict[str, Any]:
        """Return local Ollama availability details."""
        if not self.client.is_installed():
            return {
                "ok": False,
                "message": "Ollama is not installed. Install it from https://ollama.com/download and then run 'ollama serve'.",
            }
        if not self.client.is_running():
            return {
                "ok": False,
                "message": "Ollama is installed but not running. Start it with 'ollama serve'.",
            }
        try:
            models = self.models.list_models()
        except (OSError, URLError, HTTPError, ValueError) as exc:
            return {"ok": False, "message": f"Cannot read Ollama models: {exc}"}
        if not models:
            return {
                "ok": False,
                "message": "Ollama is running but no models are installed. Install one with 'ollama pull qwen3'.",
            }
        if self.models.resolve(self.models.current_model) is None:
            installed_names = ", ".join(model.name for model in models)
            return {
                "ok": False,
                "message": f"Configured model '{self.models.current_model}' is not installed. Available models: {installed_names}",
            }
        self.models.switch(self.models.current_model)
        return {"ok": True, "message": "Ollama is ready.", "models": models}

    def list_models(self) -> list[OllamaModelInfo]:
        """List installed Ollama models."""
        return self.models.list_models()

    def switch_model(self, model_name: str) -> str:
        """Switch to an installed Ollama model."""
        return self.models.switch(model_name)

    def reset(self) -> None:
        """Clear in-session conversation history."""
        self.session.reset()

    def respond(self, user_input: str) -> ChatResult:
        """Return a complete response for one user prompt."""
        messages = self.session.build_messages(user_input)
        try:
            result = self.client.chat(
                messages,
                temperature=self.settings.temperature,
                top_p=self.settings.top_p,
                context_size=self.settings.context_size,
            )
        except (OSError, URLError, HTTPError, ValueError) as exc:
            return self._error_result(user_input, f"Ollama chat failed: {exc}")

        response = str(result.get("response", ""))
        self.session.remember_exchange(user_input, response)
        return ChatResult(
            model=self.client.model,
            response=response,
            usage=self.session.estimate_usage(user_input, response),
        )

    def stream_response(self, user_input: str) -> Iterator[str]:
        """Stream a response and save it to history when complete."""
        messages = self.session.build_messages(user_input)
        collected: list[str] = []
        try:
            chunks = self.client.stream_chat(
                messages,
                temperature=self.settings.temperature,
                top_p=self.settings.top_p,
                context_size=self.settings.context_size,
            )
            for chunk in self.streaming.collect(chunks):
                collected.append(chunk)
                yield chunk
        except (OSError, URLError, HTTPError, ValueError) as exc:
            yield f"\n[Ollama chat failed: {exc}]"
            return

        self.session.remember_exchange(user_input, "".join(collected))

    def _error_result(self, user_input: str, message: str) -> ChatResult:
        """Build a structured failed chat result."""
        usage = self.session.estimate_usage(user_input, "")
        return ChatResult(
            model=self.client.model,
            response="",
            usage=usage,
            error=message,
        )
