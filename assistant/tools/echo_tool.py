"""A simple safe echo tool for initial integration."""

from __future__ import annotations

from typing import Any

from assistant.core.base_tool import BaseTool


class EchoTool(BaseTool):
    """Echo a user message back as a structured tool result."""

    name = "echo"
    description = "Echo a message back to the user."
    permission_level = "SAFE"
    timeout = 5

    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        }

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        message = kwargs.get("message", "")
        return {"result": f"Echo: {message}"}
