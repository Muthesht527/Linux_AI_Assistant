"""Controller that routes requests to tools and model reasoning."""

from __future__ import annotations

from typing import Any

from assistant.core.base_tool import BaseTool
from assistant.core.tool_engine import ToolEngine


class AssistantController:
    """Coordinates tool execution and conversational flow."""

    def __init__(self, tools: list[BaseTool] | None = None) -> None:
        self.tool_engine = ToolEngine(tools or [])

    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool with the controller."""
        self.tool_engine.register(tool)

    def get_tool(self, name: str) -> BaseTool | None:
        """Return a tool by name if present."""
        return self.tool_engine.registry.find(name)

    def handle(self, user_input: str) -> dict[str, Any]:
        """Handle a user request by selecting a relevant tool when available."""
        if not self.tool_engine.registry.list():
            return {"response": "No tools are available yet.", "tool_used": None}

        tool = self.get_tool("echo")
        if tool is None:
            return {"response": "No echo tool is available.", "tool_used": None}

        result = self.tool_engine.execute("echo", message=user_input)
        if not result.success:
            return {"response": result.message, "tool_used": tool.name}
        return {"response": result["result"], "tool_used": tool.name}
