"""Subprocess-backed terminal command execution."""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from time import perf_counter

from assistant.terminal.config import TerminalConfiguration
from assistant.terminal.context import TerminalContext, TerminalResult


class CommandExecutor:
    """Execute validated commands with subprocess and no shell."""

    def __init__(self, configuration: TerminalConfiguration | None = None) -> None:
        self.configuration = configuration or TerminalConfiguration()
        self.logger = logging.getLogger(__name__)

    def execute(self, arguments: list[str], context: TerminalContext) -> TerminalResult:
        """Run a command and return a structured terminal result."""
        working_directory = self._working_directory(context)
        timeout = self.configuration.bounded_timeout(context.timeout)
        environment = os.environ.copy()
        environment.update(context.environment)
        started_at = perf_counter()

        try:
            completed = subprocess.run(
                arguments,
                cwd=working_directory,
                env=environment,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                shell=False,
            )
            result = TerminalResult(
                command=arguments,
                return_code=completed.returncode,
                stdout=self._trim(completed.stdout),
                stderr=self._trim(completed.stderr),
                timed_out=False,
                execution_time=perf_counter() - started_at,
                working_directory=str(working_directory),
            )
        except subprocess.TimeoutExpired as exc:
            result = TerminalResult(
                command=arguments,
                return_code=None,
                stdout=self._trim(exc.stdout or ""),
                stderr=self._trim(exc.stderr or f"Command timed out after {timeout} seconds"),
                timed_out=True,
                execution_time=perf_counter() - started_at,
                working_directory=str(working_directory),
            )

        self.logger.info(
            "terminal_command command=%s cwd=%s return_code=%s timed_out=%s elapsed=%.6f",
            arguments,
            working_directory,
            result.return_code,
            result.timed_out,
            result.execution_time,
        )
        return result

    def _working_directory(self, context: TerminalContext) -> Path:
        """Resolve the command working directory."""
        directory = context.working_directory or self.configuration.default_working_directory
        return directory.expanduser().resolve()

    def _trim(self, value: str | bytes) -> str:
        """Bound captured output to the configured byte limit."""
        text = value.decode(errors="replace") if isinstance(value, bytes) else value
        encoded = text.encode("utf-8", errors="replace")
        limit = self.configuration.max_output_bytes
        if len(encoded) <= limit:
            return text
        return encoded[:limit].decode("utf-8", errors="replace") + "\n[output truncated]"
