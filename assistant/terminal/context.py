"""Terminal execution context and results."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True, frozen=True)
class TerminalContext:
    """Runtime context for a terminal command."""

    working_directory: Path | None = None
    timeout: int | None = None
    environment: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class TerminalResult:
    """Structured result returned by terminal execution."""

    command: list[str]
    return_code: int | None
    stdout: str
    stderr: str
    timed_out: bool
    execution_time: float
    working_directory: str

    @property
    def success(self) -> bool:
        """Return whether the command completed successfully."""
        return self.return_code == 0 and not self.timed_out

    def to_dict(self) -> dict[str, object]:
        """Serialize the result for tools, logs, and tests."""
        return {
            "command": self.command,
            "return_code": self.return_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "timed_out": self.timed_out,
            "execution_time": self.execution_time,
            "working_directory": self.working_directory,
        }
