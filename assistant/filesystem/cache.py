"""Small bounded cache for filesystem metadata."""

from __future__ import annotations

from collections import OrderedDict
from typing import Any


class FilesystemCache:
    """Cache frequently accessed metadata with bounded size."""

    def __init__(self, max_size: int = 256) -> None:
        self.max_size = max(1, max_size)
        self._items: OrderedDict[str, dict[str, Any]] = OrderedDict()

    def get(self, key: str) -> dict[str, Any] | None:
        """Return a cached item and mark it recently used."""
        item = self._items.get(key)
        if item is None:
            return None
        self._items.move_to_end(key)
        return dict(item)

    def set(self, key: str, value: dict[str, Any]) -> None:
        """Store an item, evicting the oldest item if needed."""
        self._items[key] = dict(value)
        self._items.move_to_end(key)
        while len(self._items) > self.max_size:
            self._items.popitem(last=False)

    def clear(self) -> None:
        """Clear all cached metadata."""
        self._items.clear()

    def size(self) -> int:
        """Return the current number of cached entries."""
        return len(self._items)
