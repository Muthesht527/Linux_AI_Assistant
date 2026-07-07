"""Conversation manager for the assistant."""

from __future__ import annotations

from typing import Any

from assistant.core.assistant_controller import AssistantController
from assistant.models.ollama_model import OllamaModel


class ConversationManager:
    """Coordinate the model and tool execution around a conversation."""

    def __init__(self, controller: AssistantController, model: OllamaModel | None = None) -> None:
        self.controller = controller
        self.model = model or OllamaModel()

    def respond(self, user_input: str) -> dict[str, Any]:
        """Return a response that includes both the tool result and model reasoning."""
        tool_result = self.controller.handle(user_input)
        model_result = self.model.generate(user_input)
        return {
            "tool_result": tool_result,
            "model_result": model_result,
        }
