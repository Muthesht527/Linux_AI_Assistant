"""Session-local conversation history and prompt construction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from assistant.config.settings import ConversationSettings

MessageRole = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class ChatMessage:
    """Single chat message sent to or received from the model."""

    role: MessageRole
    content: str

    def as_payload(self) -> dict[str, str]:
        """Return the Ollama API representation."""
        return {"role": self.role, "content": self.content}


@dataclass(frozen=True)
class TokenUsage:
    """Local token usage estimate for a chat exchange."""

    prompt_tokens: int
    response_tokens: int
    total_tokens: int


class MessageHistory:
    """Maintain bounded in-session message history."""

    def __init__(self, max_messages: int, enabled: bool = True) -> None:
        self.max_messages = max_messages
        self.enabled = enabled
        self._messages: list[ChatMessage] = []

    @property
    def messages(self) -> list[ChatMessage]:
        """Return a copy of stored messages."""
        return list(self._messages)

    def add(self, role: MessageRole, content: str) -> None:
        """Add a message if history is enabled."""
        if not self.enabled:
            return
        self._messages.append(ChatMessage(role=role, content=content))
        if self.max_messages > 0:
            self._messages = self._messages[-self.max_messages :]

    def clear(self) -> None:
        """Remove all stored messages."""
        self._messages.clear()


class PromptBuilder:
    """Build Ollama chat messages from settings and history."""

    def __init__(self, system_prompt: str) -> None:
        self.system_prompt = system_prompt.strip()

    def build(self, history: list[ChatMessage], user_input: str) -> list[dict[str, str]]:
        """Build a payload-safe message list."""
        messages: list[ChatMessage] = []
        if self.system_prompt:
            messages.append(ChatMessage(role="system", content=self.system_prompt))
        messages.extend(history)
        messages.append(ChatMessage(role="user", content=user_input))
        return [message.as_payload() for message in messages]


class ChatSession:
    """Conversation context for one local CLI session."""

    def __init__(self, settings: ConversationSettings) -> None:
        self.settings = settings
        self.history = MessageHistory(
            max_messages=settings.max_history,
            enabled=settings.history_enabled,
        )
        self.prompt_builder = PromptBuilder(settings.system_prompt)

    def build_messages(self, user_input: str) -> list[dict[str, str]]:
        """Build model-ready messages for the next user prompt."""
        return self.prompt_builder.build(self.history.messages, user_input)

    def remember_exchange(self, user_input: str, assistant_response: str) -> None:
        """Store the latest exchange in session history."""
        self.history.add("user", user_input)
        self.history.add("assistant", assistant_response)

    def reset(self) -> None:
        """Clear session history."""
        self.history.clear()

    def estimate_usage(self, prompt: str, response: str) -> TokenUsage:
        """Estimate token usage locally without requiring provider metadata."""
        prompt_tokens = _estimate_tokens(prompt)
        response_tokens = _estimate_tokens(response)
        return TokenUsage(
            prompt_tokens=prompt_tokens,
            response_tokens=response_tokens,
            total_tokens=prompt_tokens + response_tokens,
        )


def _estimate_tokens(text: str) -> int:
    """Return a small local token estimate from character count."""
    if not text:
        return 0
    return max(1, len(text) // 4)
