"""High-level terminal subsystem facade."""

from __future__ import annotations

from pathlib import Path

from assistant.terminal.config import TerminalConfiguration
from assistant.terminal.context import TerminalContext, TerminalResult
from assistant.terminal.executor import CommandExecutor
from assistant.terminal.history import CommandHistory
from assistant.terminal.parser import CommandParser
from assistant.terminal.validator import CommandValidator


class TerminalManager:
    """Coordinate parsing, validation, execution, and history."""

    def __init__(
        self,
        configuration: TerminalConfiguration | None = None,
        parser: CommandParser | None = None,
        validator: CommandValidator | None = None,
        executor: CommandExecutor | None = None,
        history: CommandHistory | None = None,
    ) -> None:
        self.configuration = configuration or TerminalConfiguration()
        self.parser = parser or CommandParser()
        self.validator = validator or CommandValidator(self.configuration)
        self.executor = executor or CommandExecutor(self.configuration)
        self.history = history or CommandHistory(self.configuration.history_limit)

    def run(
        self,
        command: str | list[str],
        *,
        working_directory: str | Path | None = None,
        timeout: int | None = None,
    ) -> TerminalResult:
        """Run a safe command and return its result."""
        arguments = self.parser.parse(command)
        cwd = self._working_directory(working_directory)
        self.validator.validate(arguments, cwd)
        context = TerminalContext(working_directory=cwd, timeout=timeout)
        result = self.executor.execute(arguments, context)
        self.history.add(result)
        return result

    def _working_directory(self, working_directory: str | Path | None = None) -> Path:
        """Return an absolute working directory."""
        directory = working_directory or self.configuration.default_working_directory
        return Path(directory).expanduser().resolve()
