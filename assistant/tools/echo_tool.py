"""A simple safe echo tool for initial integration."""

from __future__ import annotations

import logging
from time import perf_counter
from typing import Any

from assistant.core.base_tool import BaseTool, ToolResult


class EchoTool(BaseTool):
    """Echo a user message back as a structured tool result."""

    name = "echo"
    description = "Echo a message back to the user."
    category = "utility"
    version = "1.0.0"
    author = "Linux AI Assistant"
    permission_level = "SAFE"
    timeout = 5
    enabled = True
    parameter_schema = {
        "type": "object",
        "properties": {"message": {"type": "string"}},
        "required": ["message"],
    }
    result_schema = {
        "type": "object",
        "properties": {"result": {"type": "string"}},
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the echo operation and log the structured result."""
        started_at = perf_counter()
        message = kwargs.get("message", "")
        data = {"result": f"Echo: {message}"}
        result = self.result(
            success=True,
            message="Echo completed",
            data=data,
            started_at=started_at,
        )
        logging.getLogger(__name__).info(
            "tool=%s elapsed=%.6f args=%s result=%s",
            self.name,
            result.execution_time,
            {"message": message},
            data,
        )
        return result
