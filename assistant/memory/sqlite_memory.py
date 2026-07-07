"""Local session and persistent memory backed by SQLite."""

from __future__ import annotations

import json
import sqlite3
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    """Return an ISO timestamp in UTC."""
    return datetime.now(UTC).isoformat(timespec="seconds")


@dataclass(slots=True)
class SessionMemory:
    """In-memory state that is cleared when the process exits."""

    max_recent_items: int = 25
    current_working_directory: str | None = None
    current_project: str | None = None
    current_repository: str | None = None
    current_model: str | None = None
    current_configuration: dict[str, Any] = field(default_factory=dict)
    recently_opened_files: deque[str] = field(default_factory=deque)
    recently_executed_tools: deque[str] = field(default_factory=deque)
    recent_conversations: deque[dict[str, str]] = field(default_factory=deque)

    def remember_file(self, path: str) -> None:
        """Remember a recently opened file."""
        self._append_unique(self.recently_opened_files, path)

    def remember_tool(self, name: str) -> None:
        """Remember a recently executed tool."""
        self._append_unique(self.recently_executed_tools, name)

    def remember_conversation(self, role: str, content: str) -> None:
        """Remember a recent conversation turn."""
        self.recent_conversations.append({"role": role, "content": content, "time": _utc_now()})
        self._trim(self.recent_conversations)

    def snapshot(self) -> dict[str, Any]:
        """Return a JSON-friendly session memory snapshot."""
        return {
            "current_working_directory": self.current_working_directory,
            "current_project": self.current_project,
            "current_repository": self.current_repository,
            "current_model": self.current_model,
            "current_configuration": self.current_configuration,
            "recently_opened_files": list(self.recently_opened_files),
            "recently_executed_tools": list(self.recently_executed_tools),
            "recent_conversations": list(self.recent_conversations),
        }

    def clear(self) -> None:
        """Clear all session-only memory."""
        self.current_working_directory = None
        self.current_project = None
        self.current_repository = None
        self.current_model = None
        self.current_configuration = {}
        self.recently_opened_files.clear()
        self.recently_executed_tools.clear()
        self.recent_conversations.clear()

    def _append_unique(self, target: deque[str], value: str) -> None:
        if value in target:
            target.remove(value)
        target.appendleft(value)
        self._trim(target)

    def _trim(self, target: deque[Any]) -> None:
        while len(target) > self.max_recent_items:
            target.pop()


class MemoryDatabase:
    """SQLite storage for persistent assistant memory."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or Path(__file__).resolve().parent / "assistant_memory.sqlite"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _initialize(self) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    namespace TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (namespace, key)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    name TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def set(self, namespace: str, key: str, value: Any) -> None:
        """Store a JSON-serializable value."""
        now = _utc_now()
        encoded = json.dumps(value, sort_keys=True)
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO memories (namespace, key, value, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(namespace, key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
                """,
                (namespace, key, encoded, now, now),
            )

    def get(self, namespace: str, key: str, default: Any = None) -> Any:
        """Return a stored value."""
        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT value FROM memories WHERE namespace = ? AND key = ?",
                (namespace, key),
            ).fetchone()
        if row is None:
            return default
        return json.loads(row[0])

    def list(self, namespace: str | None = None) -> list[dict[str, Any]]:
        """List stored memories."""
        sql = "SELECT namespace, key, value, created_at, updated_at FROM memories"
        args: tuple[str, ...] = ()
        if namespace is not None:
            sql += " WHERE namespace = ?"
            args = (namespace,)
        sql += " ORDER BY updated_at DESC, key ASC"
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute(sql, args).fetchall()
        return [
            {
                "namespace": namespace,
                "key": key,
                "value": json.loads(value),
                "created_at": created_at,
                "updated_at": updated_at,
            }
            for namespace, key, value, created_at, updated_at in rows
        ]

    def delete(self, namespace: str, key: str) -> None:
        """Delete one persistent memory value."""
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                "DELETE FROM memories WHERE namespace = ? AND key = ?",
                (namespace, key),
            )

    def clear(self, namespace: str | None = None) -> None:
        """Clear persistent memory."""
        with sqlite3.connect(self.db_path) as connection:
            if namespace is None:
                connection.execute("DELETE FROM memories")
                return
            connection.execute("DELETE FROM memories WHERE namespace = ?", (namespace,))

    def record_event(self, category: str, name: str, metadata: dict[str, Any] | None = None) -> None:
        """Record a lightweight usage event."""
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                "INSERT INTO events (category, name, metadata, created_at) VALUES (?, ?, ?, ?)",
                (category, name, json.dumps(metadata or {}, sort_keys=True), _utc_now()),
            )

    def event_counts(self) -> dict[str, int]:
        """Return event counts grouped by category and name."""
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute(
                "SELECT category, name, COUNT(*) FROM events GROUP BY category, name"
            ).fetchall()
        return {f"{category}:{name}": count for category, name, count in rows}

    def export(self) -> dict[str, Any]:
        """Export all persistent memory."""
        return {"memories": self.list(), "event_counts": self.event_counts()}

    def import_data(self, data: dict[str, Any]) -> None:
        """Import persistent memory data produced by export."""
        for row in data.get("memories", []):
            if isinstance(row, dict) and "namespace" in row and "key" in row:
                self.set(str(row["namespace"]), str(row["key"]), row.get("value"))


class PersistentMemory:
    """High-level persistent memory API."""

    def __init__(self, database: MemoryDatabase) -> None:
        self.database = database

    def set(self, key: str, value: Any, namespace: str = "user") -> None:
        """Store a persistent value."""
        self.database.set(namespace, key, value)

    def get(self, key: str, default: Any = None, namespace: str = "user") -> Any:
        """Retrieve a persistent value."""
        return self.database.get(namespace, key, default)

    def list(self, namespace: str | None = None) -> list[dict[str, Any]]:
        """List persistent values."""
        return self.database.list(namespace)

    def clear(self, namespace: str | None = None) -> None:
        """Clear persistent values."""
        self.database.clear(namespace)


class PreferenceManager:
    """Manage user preferences in persistent memory."""

    NAMESPACE = "preferences"

    def __init__(self, memory: PersistentMemory) -> None:
        self.memory = memory

    def set(self, key: str, value: Any) -> None:
        """Store one preference."""
        self.memory.set(key, value, self.NAMESPACE)

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve one preference."""
        return self.memory.get(key, default, self.NAMESPACE)

    def list(self) -> dict[str, Any]:
        """Return all preferences as a mapping."""
        return {row["key"]: row["value"] for row in self.memory.list(self.NAMESPACE)}

    def reset(self) -> None:
        """Remove all preferences."""
        self.memory.clear(self.NAMESPACE)


class ConversationSummarizer:
    """Create compact local summaries from recent conversation turns."""

    def summarize(self, turns: list[dict[str, str]], max_items: int = 6) -> str:
        """Return a short extractive summary without calling a model."""
        selected = turns[-max_items:]
        parts = []
        for turn in selected:
            role = turn.get("role", "unknown")
            content = turn.get("content", "").strip().replace("\n", " ")
            if len(content) > 120:
                content = content[:117] + "..."
            parts.append(f"{role}: {content}")
        return "\n".join(parts)


class MemoryManager:
    """Coordinate session memory, persistent memory, and preferences."""

    def __init__(
        self,
        db_path: Path | None = None,
        max_recent_items: int = 25,
        sensitive_keys: list[str] | None = None,
    ) -> None:
        self.session = SessionMemory(max_recent_items=max_recent_items)
        self.database = MemoryDatabase(db_path)
        self.persistent = PersistentMemory(self.database)
        self.preferences = PreferenceManager(self.persistent)
        self.summarizer = ConversationSummarizer()
        self.sensitive_keys = sensitive_keys or ["password", "token", "secret", "key"]

    def remember(self, key: str, value: Any, namespace: str = "user") -> bool:
        """Persist a value unless its key looks sensitive."""
        if self._is_sensitive(key):
            return False
        self.persistent.set(key, value, namespace)
        return True

    def list_memory(self) -> dict[str, Any]:
        """Return session and persistent memory."""
        return {"session": self.session.snapshot(), "persistent": self.persistent.list()}

    def clear(self, include_persistent: bool = True) -> None:
        """Clear session memory and optionally persistent memory."""
        self.session.clear()
        if include_persistent:
            self.persistent.clear()

    def export(self) -> dict[str, Any]:
        """Export memory without session-only process state."""
        return self.database.export()

    def import_data(self, data: dict[str, Any]) -> None:
        """Import persistent memory."""
        self.database.import_data(data)

    def _is_sensitive(self, key: str) -> bool:
        lowered = key.lower()
        return any(marker.lower() in lowered for marker in self.sensitive_keys)


class SQLiteMemory:
    """Backward-compatible key-value memory wrapper."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.database = MemoryDatabase(db_path)

    def set(self, key: str, value: Any) -> None:
        """Store a value under a key."""
        self.database.set("legacy", key, str(value))

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a stored value by key."""
        return self.database.get("legacy", key, default)
