"""Validation for safe terminal commands."""

from __future__ import annotations

from pathlib import Path

from assistant.terminal.config import TerminalConfiguration


class CommandValidator:
    """Validate command names, arguments, and working directories."""

    SHELL_TOKENS = {
        "|",
        "||",
        "&",
        "&&",
        ";",
        ">",
        ">>",
        "<",
        "`",
        "$(",
        ")",
    }

    def __init__(self, configuration: TerminalConfiguration | None = None) -> None:
        self.configuration = configuration or TerminalConfiguration()

    def validate(self, arguments: list[str], working_directory: Path) -> None:
        """Raise ValueError when a command is unsafe or invalid."""
        if not arguments:
            raise ValueError("Command cannot be empty")

        command_name = Path(arguments[0]).name
        blocked = set(self.configuration.blocked_commands)
        allowed = set(self.configuration.allowed_commands)
        if command_name in blocked:
            raise ValueError(f"Command is blocked: {command_name}")
        if command_name not in allowed:
            raise ValueError(f"Command is not allowed: {command_name}")
        if not working_directory.exists() or not working_directory.is_dir():
            raise ValueError(f"Working directory is invalid: {working_directory}")

        for part in arguments:
            self._validate_argument(part)

    def _validate_argument(self, value: str) -> None:
        """Reject shell syntax that has no place in argv execution."""
        if value in self.SHELL_TOKENS:
            raise ValueError(f"Shell operator is not allowed: {value}")
        if any(token in value for token in ("`", "$(", "\x00")):
            raise ValueError("Shell expansion syntax is not allowed")
