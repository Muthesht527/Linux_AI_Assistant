"""In-memory terminal command history."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime

from assistant.terminal.context import TerminalResult


@dataclass(slots=True, frozen=True)
class CommandHistoryEntry:
    """A completed terminal command history record."""

    created_at: datetime
    result: TerminalResult


class CommandHistory:
    """Bounded in-memory command history."""

    def __init__(self, limit: int = 100) -> None:
        self._entries: deque[CommandHistoryEntry] = deque(maxlen=max(1, limit))

    def add(self, result: TerminalResult) -> None:
        """Append a completed command result."""
        self._entries.append(CommandHistoryEntry(datetime.now(UTC), result))

    def list(self) -> list[CommandHistoryEntry]:
        """Return command history in insertion order."""
        return list(self._entries)
