"""Controller that routes requests to tools and model reasoning."""

from __future__ import annotations

from typing import Any

from assistant.core.base_tool import BaseTool


class AssistantController:
    """Coordinates tool execution and conversational flow."""

    def __init__(self, tools: list[BaseTool] | None = None) -> None:
        self.tools = tools or []

    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool with the controller."""
        self.tools.append(tool)

    def get_tool(self, name: str) -> BaseTool | None:
        """Return a tool by name if present."""
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None

    def handle(self, user_input: str) -> dict[str, Any]:
        """Handle a user request by selecting a relevant tool when available."""
        if not self.tools:
            return {"response": "No tools are available yet.", "tool_used": None}

        tool = self.get_tool("echo")
        if tool is None:
            return {"response": "No echo tool is available.", "tool_used": None}

        result = tool.execute(message=user_input)
        return {"response": result["result"], "tool_used": tool.name}
