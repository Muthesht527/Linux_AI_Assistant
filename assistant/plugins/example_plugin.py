"""Example plugin exposing a simple tool."""

from __future__ import annotations

from typing import Any

from assistant.core.base_tool import BaseTool


class ExampleTool(BaseTool):
    """A minimal plugin-provided tool."""

    name = "example"
    description = "Example plugin tool"
    permission_level = "SAFE"
    timeout = 5

    def schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {"value": {"type": "string"}}}

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        return {"result": f"Example plugin received: {kwargs.get('value', '')}"}
