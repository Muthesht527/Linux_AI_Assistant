"""Example plugin exposing a simple tool."""

from __future__ import annotations

import logging
from time import perf_counter
from typing import Any

from assistant.core.base_tool import BaseTool


class ExampleTool(BaseTool):
    """A minimal plugin-provided tool."""

    name = "example"
    description = "Example plugin tool"
    permission_level = "SAFE"
    timeout = 5

    def schema(self) -> dict[str, Any]:
        """Return the argument schema for the example plugin tool."""
        return {"type": "object", "properties": {"value": {"type": "string"}}}

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the example plugin tool and log its result."""
        started_at = perf_counter()
        value = kwargs.get("value", "")
        result = {"result": f"Example plugin received: {value}"}
        logging.getLogger(__name__).info(
            "tool=%s elapsed=%.6f args=%s result=%s",
            self.name,
            perf_counter() - started_at,
            {"value": value},
            result,
        )
        return result
