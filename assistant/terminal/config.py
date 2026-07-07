"""Terminal subsystem configuration."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class TerminalConfiguration(BaseModel):
    """User-configurable terminal execution limits."""

    model_config = ConfigDict(extra="ignore")

    allowed_commands: list[str] = Field(
        default_factory=lambda: [
            "pwd",
            "ls",
            "lsblk",
            "whoami",
            "hostname",
            "uname",
            "date",
            "free",
            "df",
            "du",
            "tree",
            "find",
            "grep",
            "cat",
            "head",
            "tail",
            "wc",
            "echo",
            "which",
            "whereis",
            "file",
            "stat",
            "id",
            "uptime",
            "env",
            "printenv",
        ]
    )
    blocked_commands: list[str] = Field(
        default_factory=lambda: [
            "sudo",
            "su",
            "rm",
            "dd",
            "mkfs",
            "fdisk",
            "shutdown",
            "reboot",
            "poweroff",
            "halt",
            "killall",
            "chmod",
            "chown",
            "systemctl",
            "journalctl",
            "apt",
            "snap",
            "flatpak",
            "mount",
            "umount",
            "curl",
            "wget",
            "ssh",
        ]
    )
    default_timeout: int = Field(default=5, ge=1)
    max_timeout: int = Field(default=15, ge=1)
    max_output_bytes: int = Field(default=20_000, ge=1)
    history_limit: int = Field(default=100, ge=1)
    default_working_directory: Path = Path.cwd()

    def bounded_timeout(self, timeout: int | None = None) -> int:
        """Return a timeout constrained by configured limits."""
        requested = timeout or self.default_timeout
        return max(1, min(requested, self.max_timeout))
