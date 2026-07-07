"""Filesystem inspection tool for local project understanding."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from assistant.core.base_tool import BaseTool


class FilesystemTool(BaseTool):
    """Inspect a directory tree and summarize it."""

    name = "filesystem"
    description = "Inspect a directory tree and return a summary."
    permission_level = "SAFE"
    timeout = 15

    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "max_items": {"type": "integer"},
            },
            "required": ["path"],
        }

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        path = Path(kwargs.get("path", ".")).expanduser()
        max_items = int(kwargs.get("max_items", 20))
        entries = [entry.name for entry in sorted(path.iterdir())[:max_items]]
        return {"path": str(path), "entries": entries}
