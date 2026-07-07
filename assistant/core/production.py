"""Production-readiness helpers for runtime cache, stats, and release checks."""

from __future__ import annotations

import time
import resource
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from assistant.core.constants import APP_VERSION
from assistant.memory import MemoryManager


@dataclass(slots=True)
class CacheEntry:
    """One in-memory cache entry."""

    value: Any
    created_at: float
    ttl_seconds: int

    @property
    def stale(self) -> bool:
        """Return whether this entry has expired."""
        return time.monotonic() - self.created_at > self.ttl_seconds


class CacheManager:
    """Small bounded cache with TTL invalidation."""

    def __init__(self, max_entries: int = 256, ttl_seconds: int = 300) -> None:
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self._items: dict[str, CacheEntry] = {}
        self.hits = 0
        self.misses = 0

    def get(self, key: str, default: Any = None) -> Any:
        """Return a cached value when present and fresh."""
        entry = self._items.get(key)
        if entry is None or entry.stale:
            self.misses += 1
            if entry is not None:
                self._items.pop(key, None)
            return default
        self.hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """Cache one value."""
        if len(self._items) >= self.max_entries:
            oldest = min(self._items, key=lambda item: self._items[item].created_at)
            self._items.pop(oldest, None)
        self._items[key] = CacheEntry(value, time.monotonic(), ttl_seconds or self.ttl_seconds)

    def invalidate(self, key: str | None = None) -> None:
        """Invalidate one key or the full cache."""
        if key is None:
            self._items.clear()
            return
        self._items.pop(key, None)

    def stats(self) -> dict[str, int]:
        """Return cache statistics."""
        stale = sum(1 for item in self._items.values() if item.stale)
        return {
            "entries": len(self._items),
            "hits": self.hits,
            "misses": self.misses,
            "stale_entries": stale,
            "max_entries": self.max_entries,
        }


class PerformanceMonitor:
    """Track response timings for application operations."""

    def __init__(self) -> None:
        self._timings: list[float] = []

    def record(self, seconds: float) -> None:
        """Record one elapsed duration."""
        self._timings.append(max(0.0, seconds))

    @property
    def average_response_time(self) -> float:
        """Return the average recorded duration."""
        if not self._timings:
            return 0.0
        return sum(self._timings) / len(self._timings)


@dataclass(slots=True)
class ApplicationStatistics:
    """Process-local application statistics."""

    started_at: float = field(default_factory=time.monotonic)
    commands: Counter[str] = field(default_factory=Counter)
    tools: Counter[str] = field(default_factory=Counter)
    errors: Counter[str] = field(default_factory=Counter)
    plugins: Counter[str] = field(default_factory=Counter)
    repositories: Counter[str] = field(default_factory=Counter)
    filesystem_searches: Counter[str] = field(default_factory=Counter)
    performance: PerformanceMonitor = field(default_factory=PerformanceMonitor)
    cache: CacheManager = field(default_factory=CacheManager)

    def record_command(self, name: str) -> None:
        """Track one CLI or chat command."""
        self.commands[name] += 1

    def record_tool(self, name: str) -> None:
        """Track one tool execution."""
        self.tools[name] += 1

    def record_error(self, name: str) -> None:
        """Track one error category."""
        self.errors[name] += 1

    def record_plugin(self, name: str) -> None:
        """Track one plugin operation."""
        self.plugins[name] += 1

    def record_repository_scan(self, path: str) -> None:
        """Track one repository scan."""
        self.repositories[path] += 1

    def record_filesystem_search(self, query: str) -> None:
        """Track one filesystem search."""
        self.filesystem_searches[query] += 1

    def snapshot(self) -> dict[str, Any]:
        """Return current statistics."""
        return {
            "uptime_seconds": round(time.monotonic() - self.started_at, 3),
            "commands_executed": sum(self.commands.values()),
            "tools_executed": sum(self.tools.values()),
            "average_response_time": round(self.performance.average_response_time, 6),
            "most_frequent_tools": self.tools.most_common(5),
            "plugins": dict(self.plugins),
            "repository_scans": sum(self.repositories.values()),
            "filesystem_searches": sum(self.filesystem_searches.values()),
            "memory_usage_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "cache": self.cache.stats(),
            "errors": dict(self.errors),
        }


@dataclass(slots=True)
class RuntimeServices:
    """Shared process-local production services."""

    cache: CacheManager = field(default_factory=CacheManager)
    statistics: ApplicationStatistics = field(default_factory=ApplicationStatistics)
    memory: MemoryManager = field(default_factory=MemoryManager)

    def __post_init__(self) -> None:
        self.statistics.cache = self.cache


_RUNTIME = RuntimeServices()


def get_runtime() -> RuntimeServices:
    """Return shared process-local production services."""
    return _RUNTIME


def configure_runtime_memory(memory: MemoryManager) -> None:
    """Install the configured memory manager into shared runtime services."""
    _RUNTIME.memory = memory


class VersionManager:
    """Expose application version metadata."""

    def __init__(self, version: str = APP_VERSION) -> None:
        self.version = version

    def info(self) -> dict[str, str]:
        """Return version information."""
        return {"name": "Linux AI Assistant", "version": self.version}


class ReleaseManager:
    """Check local release packaging inputs."""

    REQUIRED_FILES = (
        "README.md",
        "LICENSE",
        "requirements.txt",
        "requirements-dev.txt",
        "pyproject.toml",
    )

    def __init__(self, root: Path | None = None, version_manager: VersionManager | None = None) -> None:
        self.root = root or Path.cwd()
        self.version_manager = version_manager or VersionManager()

    def check(self) -> dict[str, Any]:
        """Return a conservative local release readiness report."""
        files = {name: (self.root / name).exists() for name in self.REQUIRED_FILES}
        missing = [name for name, exists in files.items() if not exists]
        return {
            "version": self.version_manager.info()["version"],
            "required_files": files,
            "missing_files": missing,
            "ready": not missing,
        }
