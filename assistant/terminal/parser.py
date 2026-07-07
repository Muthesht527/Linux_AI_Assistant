"""Safe command parsing for terminal execution."""

from __future__ import annotations

import shlex


class CommandParser:
    """Parse a user command string into subprocess arguments."""

    def parse(self, command: str | list[str]) -> list[str]:
        """Return normalized command arguments."""
        if isinstance(command, list):
            return [str(part) for part in command if str(part)]
        value = command.strip()
        if not value:
            raise ValueError("Command cannot be empty")
        return shlex.split(value, posix=True)
