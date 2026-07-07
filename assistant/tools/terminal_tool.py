"""Tool Engine adapter for safe terminal commands."""

from __future__ import annotations

import logging
from time import perf_counter
from typing import Any

from assistant.config.config_loader import ConfigLoader
from assistant.core.base_tool import BaseTool, PermissionLevel, ToolResult
from assistant.terminal import TerminalConfiguration, TerminalManager


def _manager() -> TerminalManager:
    """Create a terminal manager from application settings."""
    settings = ConfigLoader().load_settings()
    configuration = TerminalConfiguration(**settings.terminal.model_dump())
    return TerminalManager(configuration)


class TerminalTool(BaseTool):
    """Execute a whitelisted Linux command through the terminal engine."""

    name = "terminal"
    description = "Execute safe whitelisted Linux commands."
    category = "terminal"
    permission_level = PermissionLevel.SAFE
    timeout = 20
    parameter_schema = {
        "type": "object",
        "properties": {
            "command": {"type": "string"},
            "working_directory": {"type": "string"},
            "timeout": {"type": "integer"},
        },
        "required": ["command"],
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute a safe command and return captured output."""
        started_at = perf_counter()
        command = str(kwargs.get("command", ""))
        try:
            result = _manager().run(
                command,
                working_directory=kwargs.get("working_directory"),
                timeout=kwargs.get("timeout"),
            )
            data = result.to_dict()
            tool_result = self.result(
                success=result.success,
                message="Terminal command completed"
                if result.success
                else "Terminal command failed",
                data=data,
                started_at=started_at,
                error=None if result.success else data.get("stderr") or "Command failed",
            )
        except Exception as exc:
            tool_result = self.result(
                success=False,
                message="Terminal command rejected",
                data={"command": command, "error": str(exc)},
                started_at=started_at,
                error=str(exc),
            )

        logging.getLogger(__name__).info(
            "tool=%s elapsed=%.6f args=%s success=%s",
            self.name,
            tool_result.execution_time,
            {
                "command": command,
                "working_directory": kwargs.get("working_directory"),
                "timeout": kwargs.get("timeout"),
            },
            tool_result.success,
        )
        return tool_result
