"""Tool execution engine for the assistant."""

from __future__ import annotations

from typing import Any

from assistant.core.base_tool import BaseTool


class ToolEngine:
    """Coordinate validated tool execution."""

    def __init__(self, tools: list[BaseTool] | None = None) -> None:
        self.tools = tools or []

    def register(self, tool: BaseTool) -> None:
        """Register a tool with the engine."""
        self.tools.append(tool)

    def execute(self, tool_name: str, **kwargs: Any) -> dict[str, Any]:
        """Execute a tool by name, validating its existence."""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool.execute(**kwargs)
        return {"error": f"Tool {tool_name} not found"}
