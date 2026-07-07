"""Filesystem search backed by SQLite with recursive fallback."""

from __future__ import annotations

import re
import sqlite3
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from assistant.filesystem.config import FilesystemConfiguration
from assistant.filesystem.validators import FilesystemValidators


class FilesystemSearcher:
    """Search indexed filesystem rows and text file contents."""

    def __init__(self, database_path: Path, configuration: FilesystemConfiguration) -> None:
        self.database_path = database_path
        self.configuration = configuration

    def search(
        self,
        *,
        name: str | None = None,
        extension: str | None = None,
        directory: str | None = None,
        regex: str | None = None,
        partial: str | None = None,
        case_sensitive: bool = False,
        fuzzy: bool = False,
        min_size: int | None = None,
        max_size: int | None = None,
        modified_after: float | None = None,
        modified_before: float | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Search by filename, extension, directory, regex, date, or size."""
        rows = self._indexed_rows()
        matches = [
            row
            for row in rows
            if self._matches(
                row,
                name=name,
                extension=extension,
                directory=directory,
                regex=regex,
                partial=partial,
                case_sensitive=case_sensitive,
                fuzzy=fuzzy,
                min_size=min_size,
                max_size=max_size,
                modified_after=modified_after,
                modified_before=modified_before,
            )
        ]
        return {"results": matches[: max(1, limit)], "total": len(matches), "source": "sqlite"}

    def search_content(
        self,
        query: str,
        *,
        regex: bool = False,
        case_sensitive: bool = False,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Search inside supported text files."""
        pattern = re.compile(query, 0 if case_sensitive else re.IGNORECASE) if regex else None
        results: list[dict[str, Any]] = []
        for row in self._indexed_rows():
            path = Path(row["path"])
            if path.suffix.lower().lstrip(".") not in self._text_extensions():
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            matched = bool(pattern.search(text)) if pattern else self._contains(text, query, case_sensitive)
            if matched:
                results.append({"path": str(path), "filename": path.name})
            if len(results) >= limit:
                break
        return {"results": results, "total": len(results)}

    def _matches(self, row: dict[str, Any], **filters: Any) -> bool:
        """Apply search filters to one indexed row."""
        filename = row["filename"]
        compare_name = filename if filters["case_sensitive"] else filename.lower()
        if filters["name"]:
            value = filters["name"] if filters["case_sensitive"] else filters["name"].lower()
            if compare_name != value:
                return False
        extension = FilesystemValidators.normalize_extension(filters["extension"])
        if extension and row["extension"].lower() != extension:
            return False
        if filters["directory"] and filters["directory"] not in row["directory"]:
            return False
        if filters["regex"] and not re.search(filters["regex"], filename):
            return False
        if filters["partial"]:
            value = filters["partial"] if filters["case_sensitive"] else filters["partial"].lower()
            if value not in compare_name:
                return False
        if filters["fuzzy"] and filters["partial"]:
            ratio = SequenceMatcher(None, filters["partial"].lower(), filename.lower()).ratio()
            if ratio < 0.6:
                return False
        if filters["min_size"] is not None and row["size"] < filters["min_size"]:
            return False
        if filters["max_size"] is not None and row["size"] > filters["max_size"]:
            return False
        if filters["modified_after"] is not None and row["modified"] < filters["modified_after"]:
            return False
        if filters["modified_before"] is not None and row["modified"] > filters["modified_before"]:
            return False
        return True

    def _indexed_rows(self) -> list[dict[str, Any]]:
        """Read all index rows, returning an empty list on corruption."""
        try:
            with sqlite3.connect(self.database_path) as connection:
                connection.row_factory = sqlite3.Row
                rows = connection.execute("SELECT * FROM files ORDER BY filename").fetchall()
            return [dict(row) for row in rows]
        except sqlite3.DatabaseError:
            return []

    def _contains(self, text: str, query: str, case_sensitive: bool) -> bool:
        """Return whether text contains a query."""
        if case_sensitive:
            return query in text
        return query.lower() in text.lower()

    def _text_extensions(self) -> set[str]:
        """Return supported text-search extensions."""
        return {"txt", "md", "py", "java", "cpp", "c", "json", "yaml", "yml", "xml", "html", "css", "js", "csv"}
