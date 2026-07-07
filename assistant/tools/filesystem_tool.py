"""Tool Engine adapters for filesystem operations."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Any

from assistant.config.config_loader import ConfigLoader
from assistant.core.base_tool import BaseTool, PermissionLevel, ToolResult
from assistant.filesystem import FilesystemConfiguration, FilesystemManager


def _manager() -> FilesystemManager:
    """Create a filesystem manager from application settings."""
    settings = ConfigLoader().load_settings()
    configuration = FilesystemConfiguration(**settings.filesystem.model_dump())
    return FilesystemManager(configuration)


class SearchFileTool(BaseTool):
    """Search indexed files by name, extension, directory, regex, or content."""

    name = "search_file"
    description = "Search indexed files and optionally search inside text files."
    category = "filesystem"
    permission_level = PermissionLevel.SAFE
    timeout = 20
    parameter_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "extension": {"type": "string"},
            "directory": {"type": "string"},
            "regex": {"type": "string"},
            "partial": {"type": "string"},
            "content": {"type": "string"},
            "case_sensitive": {"type": "boolean"},
            "fuzzy": {"type": "boolean"},
            "min_size": {"type": "integer"},
            "max_size": {"type": "integer"},
            "limit": {"type": "integer"},
        },
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute a file or content search."""
        started_at = perf_counter()
        try:
            content = kwargs.pop("content", None)
            if content:
                data = _manager().search_content(
                    content,
                    regex=bool(kwargs.get("regex")),
                    case_sensitive=bool(kwargs.get("case_sensitive", False)),
                    limit=int(kwargs.get("limit", 50)),
                )
            else:
                data = _manager().search(**kwargs)
            return self.result(
                success=True,
                message="File search completed",
                data=data,
                started_at=started_at,
            )
        except Exception as exc:
            return self.result(
                success=False,
                message="File search failed",
                data={"error": str(exc)},
                started_at=started_at,
                error=str(exc),
            )


class ReadFileTool(BaseTool):
    """Read a supported local file."""

    name = "read_file"
    description = "Read supported text, document, and structured file formats."
    category = "filesystem"
    permission_level = PermissionLevel.SAFE
    timeout = 20
    parameter_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "preview_rows": {"type": "integer"},
        },
        "required": ["path"],
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        """Read a local file."""
        started_at = perf_counter()
        try:
            data = _manager().read(kwargs["path"], int(kwargs.get("preview_rows", 20)))
            return self.result(
                success=True,
                message="File read completed",
                data=data,
                started_at=started_at,
            )
        except Exception as exc:
            return self.result(
                success=False,
                message="File read failed",
                data={"path": kwargs.get("path"), "error": str(exc)},
                started_at=started_at,
                error=str(exc),
            )


class FileMetadataTool(BaseTool):
    """Return metadata for a file or directory."""

    name = "file_metadata"
    description = "Return path, size, owner, permissions, times, and mime type."
    category = "filesystem"
    permission_level = PermissionLevel.SAFE
    timeout = 10
    parameter_schema = {
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        """Return metadata for a path."""
        started_at = perf_counter()
        try:
            data = _manager().metadata(kwargs["path"])
            return self.result(
                success=True,
                message="Metadata lookup completed",
                data=data,
                started_at=started_at,
            )
        except Exception as exc:
            return self.result(
                success=False,
                message="Metadata lookup failed",
                data={"path": kwargs.get("path"), "error": str(exc)},
                started_at=started_at,
                error=str(exc),
            )


class DirectoryListTool(BaseTool):
    """List directory entries with metadata."""

    name = "directory_list"
    description = "List local directory entries."
    category = "filesystem"
    permission_level = PermissionLevel.SAFE
    timeout = 15
    parameter_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "limit": {"type": "integer"},
        },
        "required": ["path"],
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        """List a directory."""
        started_at = perf_counter()
        try:
            data = _manager().list_directory(kwargs["path"], int(kwargs.get("limit", 100)))
            return self.result(
                success=True,
                message="Directory listing completed",
                data=data,
                started_at=started_at,
            )
        except Exception as exc:
            return self.result(
                success=False,
                message="Directory listing failed",
                data={"path": kwargs.get("path"), "error": str(exc)},
                started_at=started_at,
                error=str(exc),
            )


class IndexStatusTool(BaseTool):
    """Return filesystem index status."""

    name = "index_status"
    description = "Return SQLite filesystem index status and detected roots."
    category = "filesystem"
    permission_level = PermissionLevel.SAFE
    timeout = 10

    def execute(self, **kwargs: Any) -> ToolResult:
        """Return index status."""
        del kwargs
        started_at = perf_counter()
        data = _manager().index_status()
        return self.result(
            success=bool(data.get("available", False)),
            message="Index status loaded",
            data=data,
            started_at=started_at,
            error=data.get("error"),
        )


class RebuildIndexTool(BaseTool):
    """Rebuild the filesystem index after permission approval."""

    name = "rebuild_index"
    description = "Rebuild the SQLite filesystem index."
    category = "filesystem"
    permission_level = PermissionLevel.ASK
    timeout = 120

    def execute(self, **kwargs: Any) -> ToolResult:
        """Rebuild the index."""
        del kwargs
        started_at = perf_counter()
        try:
            data = _manager().rebuild_index()
            return self.result(
                success=True,
                message="Index rebuild completed",
                data=data,
                started_at=started_at,
            )
        except Exception as exc:
            return self.result(
                success=False,
                message="Index rebuild failed",
                data={"error": str(exc)},
                started_at=started_at,
                error=str(exc),
            )


class FilesystemTool(DirectoryListTool):
    """Backward-compatible directory inspection tool."""

    name = "filesystem"
    description = "Inspect a directory tree and return a summary."

    def execute(self, **kwargs: Any) -> ToolResult:
        """List a directory and expose legacy entry names."""
        result = super().execute(
            path=kwargs.get("path", "."),
            limit=int(kwargs.get("max_items", kwargs.get("limit", 20))),
        )
        if result.success:
            result.data["entries"] = [
                Path(entry["path"]).name for entry in result.data.get("entries", [])
            ]
        return result
