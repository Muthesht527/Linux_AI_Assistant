"""Conversation layer tests that do not require a running Ollama service."""

from __future__ import annotations

from collections.abc import Iterator

from assistant.config.settings import ConversationSettings
from assistant.core.conversation_manager import ConversationManager
from assistant.models.ollama_model import OllamaModelInfo


class FakeOllama:
    """Minimal fake Ollama client for conversation tests."""

    def __init__(self) -> None:
        self.model = "qwen3"

    def is_installed(self) -> bool:
        return True

    def is_running(self) -> bool:
        return True

    def list_models(self) -> list[OllamaModelInfo]:
        return [OllamaModelInfo(name="qwen3:latest")]

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float,
        top_p: float,
        context_size: int,
    ) -> dict[str, str]:
        del temperature, top_p, context_size
        return {"response": f"reply to {messages[-1]['content']}"}

    def stream_chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float,
        top_p: float,
        context_size: int,
    ) -> Iterator[str]:
        del messages, temperature, top_p, context_size
        yield "hello"
        yield " world"


def test_conversation_manager_resolves_default_model_tag() -> None:
    """Verify qwen3 resolves to qwen3:latest when installed that way."""
    manager = ConversationManager(ConversationSettings(), model=FakeOllama())

    status = manager.status()

    assert status["ok"] is True
    assert manager.models.current_model == "qwen3:latest"


def test_conversation_manager_records_history() -> None:
    """Verify non-streaming chat stores session history."""
    manager = ConversationManager(ConversationSettings(streaming_enabled=False), model=FakeOllama())

    result = manager.respond("hello")

    assert result.response == "reply to hello"
    assert [message.role for message in manager.session.history.messages] == [
        "user",
        "assistant",
    ]


def test_conversation_manager_streams_and_records_history() -> None:
    """Verify streaming chat yields chunks and stores the final response."""
    manager = ConversationManager(ConversationSettings(), model=FakeOllama())

    chunks = list(manager.stream_response("hello"))

    assert chunks == ["hello", " world"]
    assert manager.session.history.messages[-1].content == "hello world"
