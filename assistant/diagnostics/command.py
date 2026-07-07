"""Safe read-only command runner for diagnostics collectors."""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from time import perf_counter

from assistant.diagnostics.config import DiagnosticsConfiguration


@dataclass(slots=True)
class CommandResult:
    """Captured command result."""

    command: list[str]
    stdout: str
    stderr: str
    returncode: int
    elapsed: float
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        """Return whether the command exited successfully."""
        return self.returncode == 0 and not self.timed_out


class DiagnosticsCommandRunner:
    """Run approved non-mutating Linux commands without a shell."""

    ALLOWED = {
        "cat",
        "df",
        "free",
        "hostname",
        "ip",
        "journalctl",
        "lsblk",
        "lscpu",
        "lspci",
        "lsusb",
        "ps",
        "systemctl",
        "uname",
        "uptime",
    }

    def __init__(self, config: DiagnosticsConfiguration) -> None:
        self.config = config
        self.logger = logging.getLogger(__name__)

    def run(self, command: list[str], timeout: int | None = None) -> CommandResult:
        """Run an allowed read-only command and capture text output."""
        started_at = perf_counter()
        if not command or command[0] not in self.ALLOWED:
            elapsed = perf_counter() - started_at
            return CommandResult(command, "", "Command not allowed", 126, elapsed)

        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout or self.config.timeout,
            )
            result = CommandResult(
                command=command,
                stdout=completed.stdout,
                stderr=completed.stderr,
                returncode=completed.returncode,
                elapsed=perf_counter() - started_at,
            )
        except subprocess.TimeoutExpired as exc:
            result = CommandResult(
                command=command,
                stdout=exc.stdout or "",
                stderr=exc.stderr or "Command timed out",
                returncode=124,
                elapsed=perf_counter() - started_at,
                timed_out=True,
            )
        except OSError as exc:
            result = CommandResult(
                command=command,
                stdout="",
                stderr=str(exc),
                returncode=127,
                elapsed=perf_counter() - started_at,
            )

        self.logger.info(
            "diagnostics_command command=%s elapsed=%.6f success=%s",
            command,
            result.elapsed,
            result.ok,
        )
        return result
