"""Filesystem inspection tool for local project understanding."""

from __future__ import annotations

import logging
from pathlib import Path
from time import perf_counter
from typing import Any

from assistant.core.base_tool import BaseTool


class FilesystemTool(BaseTool):
    """Inspect a directory tree and summarize it."""

    name = "filesystem"
    description = "Inspect a directory tree and return a summary."
    permission_level = "SAFE"
    timeout = 15

    def schema(self) -> dict[str, Any]:
        """Return the argument schema for filesystem inspection."""
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "max_items": {"type": "integer"},
            },
            "required": ["path"],
        }

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Inspect a directory without exposing exceptions to users."""
        started_at = perf_counter()
        path = Path(kwargs.get("path", ".")).expanduser()
        try:
            max_items = max(0, int(kwargs.get("max_items", 20)))
            entries = [entry.name for entry in sorted(path.iterdir())[:max_items]]
            result = {"path": str(path), "entries": entries}
            logging.getLogger(__name__).info(
                "tool=%s elapsed=%.6f args=%s result=%s",
                self.name,
                perf_counter() - started_at,
                {"path": str(path), "max_items": max_items},
                result,
            )
            return result
        except (OSError, ValueError) as exc:
            result = {"path": str(path), "error": str(exc)}
            logging.getLogger(__name__).error(
                "tool=%s elapsed=%.6f args=%s error=%s",
                self.name,
                perf_counter() - started_at,
                {"path": str(path), "max_items": kwargs.get("max_items", 20)},
                exc,
            )
            return result
