"""Path management for configurable project directories."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from assistant.config.settings import DirectorySettings


@dataclass(frozen=True)
class PathManager:
    """Resolve and create application directories from settings."""

    project_root: Path
    directories: DirectorySettings

    @classmethod
    def from_project_root(cls, directories: DirectorySettings) -> "PathManager":
        """Create a manager using the repository root discovered from this file."""
        root = Path(__file__).resolve().parents[2]
        return cls(project_root=root, directories=directories)

    def resolve(self, path: Path) -> Path:
        """Resolve a configured path relative to the project root."""
        expanded = path.expanduser()
        if expanded.is_absolute():
            return expanded
        return self.project_root / expanded

    def required_directories(self) -> list[Path]:
        """Return all foundation directories that must exist."""
        return [
            self.resolve(self.directories.logs),
            self.resolve(self.directories.cache),
            self.resolve(self.directories.memory),
            self.resolve(self.directories.config),
            self.resolve(self.directories.plugins),
            self.resolve(self.directories.tests),
        ]

    def ensure_directories(self) -> list[Path]:
        """Create missing foundation directories and return their paths."""
        paths = self.required_directories()
        for path in paths:
            path.mkdir(parents=True, exist_ok=True)
        return paths

    def log_file(self, file_name: str) -> Path:
        """Return the configured log file path."""
        return self.resolve(self.directories.logs) / file_name
