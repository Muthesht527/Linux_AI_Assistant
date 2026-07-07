"""SQLite-backed filesystem indexer."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from assistant.filesystem.config import FilesystemConfiguration

ProgressCallback = Callable[[dict[str, Any]], None]


class FilesystemIndexer:
    """Incrementally index files into SQLite."""

    def __init__(self, database_path: Path, configuration: FilesystemConfiguration) -> None:
        self.database_path = database_path
        self.configuration = configuration
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def initialize(self) -> None:
        """Create index tables when missing."""
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS files (
                    path TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    extension TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    modified REAL NOT NULL,
                    created REAL,
                    directory TEXT NOT NULL,
                    file_hash TEXT,
                    last_indexed REAL NOT NULL
                )
                """
            )
            connection.execute("CREATE INDEX IF NOT EXISTS idx_files_name ON files(filename)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_files_ext ON files(extension)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_files_dir ON files(directory)")

    def update(self, roots: list[Path], progress: ProgressCallback | None = None) -> dict[str, Any]:
        """Incrementally update index rows for supplied roots."""
        indexed = 0
        skipped = 0
        errors: list[str] = []
        with self._connect() as connection:
            for root in roots:
                for path in self._walk(root):
                    try:
                        info = path.stat()
                        if info.st_size > self.configuration.maximum_file_size:
                            skipped += 1
                            continue
                        row = self._existing(connection, path)
                        if row and row["size"] == info.st_size and row["modified"] == info.st_mtime:
                            continue
                        connection.execute(
                            """
                            INSERT OR REPLACE INTO files (
                                path, filename, extension, size, modified, created,
                                directory, file_hash, last_indexed
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                str(path),
                                path.name,
                                path.suffix.lower(),
                                info.st_size,
                                info.st_mtime,
                                getattr(info, "st_birthtime", info.st_ctime),
                                str(path.parent),
                                None,
                                datetime.now().timestamp(),
                            ),
                        )
                        indexed += 1
                        if progress and indexed % 100 == 0:
                            progress({"indexed": indexed, "root": str(root)})
                    except OSError as exc:
                        errors.append(f"{path}: {exc}")
        return {"indexed": indexed, "skipped": skipped, "errors": errors}

    def rebuild(self, roots: list[Path], progress: ProgressCallback | None = None) -> dict[str, Any]:
        """Clear and rebuild the index on explicit request."""
        with self._connect() as connection:
            connection.execute("DELETE FROM files")
        return self.update(roots, progress)

    def status(self) -> dict[str, Any]:
        """Return index health and row counts."""
        try:
            with self._connect() as connection:
                count = connection.execute("SELECT COUNT(*) FROM files").fetchone()[0]
            return {"path": str(self.database_path), "files": count, "available": True}
        except sqlite3.DatabaseError as exc:
            return {"path": str(self.database_path), "files": 0, "available": False, "error": str(exc)}

    def _walk(self, root: Path) -> list[Path]:
        """Collect indexable files under a root while skipping ignored folders."""
        files: list[Path] = []
        ignored = set(self.configuration.ignored_folders)
        ignored.update({"proc", "sys", "dev", "run", "snap"})
        ignored_ext = {ext.lower() for ext in self.configuration.ignored_extensions}
        try:
            for path in root.rglob("*"):
                if any(part in ignored for part in path.parts):
                    continue
                if path.is_symlink() or not path.is_file():
                    continue
                if path.suffix.lower() in ignored_ext:
                    continue
                files.append(path.resolve())
        except OSError:
            return files
        return files

    def _existing(self, connection: sqlite3.Connection, path: Path) -> sqlite3.Row | None:
        """Return an existing index row for a path."""
        return connection.execute(
            "SELECT size, modified FROM files WHERE path = ?",
            (str(path),),
        ).fetchone()

    def _connect(self) -> sqlite3.Connection:
        """Open a SQLite connection configured for dict-like rows."""
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection
