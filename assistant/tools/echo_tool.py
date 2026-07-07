"""A simple safe echo tool for initial integration."""

from __future__ import annotations

import logging
from time import perf_counter
from typing import Any

from assistant.core.base_tool import BaseTool


class EchoTool(BaseTool):
    """Echo a user message back as a structured tool result."""

    name = "echo"
    description = "Echo a message back to the user."
    permission_level = "SAFE"
    timeout = 5

    def schema(self) -> dict[str, Any]:
        """Return the argument schema for the echo tool."""
        return {
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        }

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the echo operation and log the structured result."""
        started_at = perf_counter()
        message = kwargs.get("message", "")
        result = {"result": f"Echo: {message}"}
        logging.getLogger(__name__).info(
            "tool=%s elapsed=%.6f args=%s result=%s",
            self.name,
            perf_counter() - started_at,
            {"message": message},
            result,
        )
        return result
