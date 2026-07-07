"""Example plugin exposing a simple tool."""

from __future__ import annotations

import logging
from time import perf_counter
from typing import Any

from assistant.core.base_tool import BaseTool, ToolResult


class ExampleTool(BaseTool):
    """A minimal plugin-provided tool."""

    name = "example"
    description = "Example plugin tool"
    category = "plugin"
    version = "1.0.0"
    author = "Linux AI Assistant"
    permission_level = "SAFE"
    timeout = 5
    enabled = True
    parameter_schema = {
        "type": "object",
        "properties": {"value": {"type": "string"}},
    }
    result_schema = {
        "type": "object",
        "properties": {"result": {"type": "string"}},
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the example plugin tool and log its result."""
        started_at = perf_counter()
        value = kwargs.get("value", "")
        data = {"result": f"Example plugin received: {value}"}
        result = self.result(
            success=True,
            message="Example plugin completed",
            data=data,
            started_at=started_at,
        )
        logging.getLogger(__name__).info(
            "tool=%s elapsed=%.6f args=%s result=%s",
            self.name,
            result.execution_time,
            {"value": value},
            data,
        )
        return result
