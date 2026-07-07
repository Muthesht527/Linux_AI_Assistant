"""Local SQLite-backed memory for session and persistent notes."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class SQLiteMemory:
    """Simple key-value memory backed by SQLite."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or Path(__file__).resolve().parent / "assistant_memory.sqlite"
        self._initialize()

    def _initialize(self) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS memories (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )

    def set(self, key: str, value: Any) -> None:
        """Store a value under a key."""
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                "INSERT OR REPLACE INTO memories (key, value) VALUES (?, ?)",
                (key, str(value)),
            )

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a stored value by key."""
        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT value FROM memories WHERE key = ?",
                (key,),
            ).fetchone()
        return default if row is None else row[0]
