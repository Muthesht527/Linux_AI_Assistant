"""Validation helpers for safe filesystem operations."""

from __future__ import annotations

from pathlib import Path


class FilesystemValidators:
    """Validate paths and search inputs before filesystem work."""

    @staticmethod
    def path_exists(path: Path) -> None:
        """Require an existing path."""
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")

    @staticmethod
    def readable_file(path: Path, maximum_size: int) -> None:
        """Require an existing readable file below the configured size."""
        FilesystemValidators.path_exists(path)
        if not path.is_file():
            raise IsADirectoryError(f"Path is not a file: {path}")
        if path.stat().st_size > maximum_size:
            raise ValueError(f"File exceeds maximum size: {path}")

    @staticmethod
    def normalize_extension(extension: str | None) -> str | None:
        """Normalize extension filters to a lowercase dot-prefixed form."""
        if not extension:
            return None
        value = extension.strip().lower()
        if not value:
            return None
        return value if value.startswith(".") else f".{value}"
