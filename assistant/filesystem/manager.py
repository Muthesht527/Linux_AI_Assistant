"""High-level facade for the filesystem subsystem."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Any

from assistant.core.production import get_runtime
from assistant.filesystem.cache import FilesystemCache
from assistant.filesystem.config import FilesystemConfiguration
from assistant.filesystem.indexer import FilesystemIndexer
from assistant.filesystem.metadata import FilesystemMetadata
from assistant.filesystem.reader import FilesystemReader
from assistant.filesystem.searcher import FilesystemSearcher


class FilesystemManager:
    """Coordinate roots, index, search, readers, metadata, and cache."""

    def __init__(
        self,
        configuration: FilesystemConfiguration | None = None,
        project_root: Path | None = None,
    ) -> None:
        self.project_root = project_root or Path(__file__).resolve().parents[2]
        self.configuration = configuration or FilesystemConfiguration()
        index_path = self.configuration.resolved_index_location(self.project_root)
        self.cache = FilesystemCache(self.configuration.cache_size)
        self.metadata_reader = FilesystemMetadata()
        self.reader = FilesystemReader(self.configuration.maximum_file_size)
        self.indexer = FilesystemIndexer(index_path, self.configuration)
        self.searcher = FilesystemSearcher(index_path, self.configuration)

    def roots(self) -> list[Path]:
        """Return automatically detected roots."""
        return self.configuration.detected_roots()

    def index(self) -> dict[str, Any]:
        """Incrementally index configured roots."""
        return self.indexer.update(self.roots())

    def rebuild_index(self) -> dict[str, Any]:
        """Rebuild the index when explicitly approved."""
        get_runtime().cache.invalidate()
        return self.indexer.rebuild(self.roots())

    def index_status(self) -> dict[str, Any]:
        """Return index status and detected roots."""
        status = self.indexer.status()
        status["roots"] = [str(path) for path in self.roots()]
        return status

    def search(self, **kwargs: Any) -> dict[str, Any]:
        """Search indexed files."""
        started_at = perf_counter()
        runtime = get_runtime()
        cache_key = f"filesystem:search:{sorted(kwargs.items())}"
        cached = runtime.cache.get(cache_key)
        if isinstance(cached, dict):
            return cached
        data = self.searcher.search(**kwargs)
        runtime.cache.set(cache_key, data)
        runtime.statistics.record_filesystem_search(str(kwargs))
        runtime.statistics.performance.record(perf_counter() - started_at)
        return data

    def search_content(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Search inside indexed text files."""
        started_at = perf_counter()
        runtime = get_runtime()
        cache_key = f"filesystem:content:{query}:{sorted(kwargs.items())}"
        cached = runtime.cache.get(cache_key)
        if isinstance(cached, dict):
            return cached
        data = self.searcher.search_content(query, **kwargs)
        runtime.cache.set(cache_key, data)
        runtime.statistics.record_filesystem_search(query)
        runtime.statistics.performance.record(perf_counter() - started_at)
        return data

    def read(self, path: str | Path, preview_rows: int = 20) -> dict[str, Any]:
        """Read a supported file."""
        runtime = get_runtime()
        resolved = Path(path).expanduser().resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"Path does not exist: {resolved}")
        stat = resolved.stat()
        cache_key = f"filesystem:read:{resolved}:{stat.st_mtime_ns}:{preview_rows}"
        cached = runtime.cache.get(cache_key)
        if isinstance(cached, dict):
            return cached
        data = self.reader.read(resolved, preview_rows)
        runtime.cache.set(cache_key, data)
        runtime.memory.session.remember_file(str(resolved))
        return data

    def metadata(self, path: str | Path) -> dict[str, Any]:
        """Return cached metadata for a path."""
        resolved = str(Path(path).expanduser().resolve())
        cached = self.cache.get(resolved)
        if cached is not None:
            cached["cache_hit"] = True
            return cached
        data = self.metadata_reader.get(Path(resolved))
        data["cache_hit"] = False
        self.cache.set(resolved, data)
        return data

    def list_directory(self, path: str | Path, limit: int = 100) -> dict[str, Any]:
        """List directory entries with basic metadata."""
        resolved = Path(path).expanduser().resolve()
        get_runtime().memory.record_folder(str(resolved))
        if not resolved.exists():
            raise FileNotFoundError(f"Path does not exist: {resolved}")
        if not resolved.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {resolved}")
        entries = []
        for entry in sorted(resolved.iterdir(), key=lambda item: item.name.lower())[: max(1, limit)]:
            try:
                entries.append(self.metadata(entry))
            except OSError:
                entries.append({"path": str(entry), "error": "Unreadable entry"})
        return {"path": str(resolved), "entries": entries}

    def clear_cache(self) -> dict[str, Any]:
        """Clear cached filesystem metadata."""
        self.cache.clear()
        return {"cleared": True, "size": self.cache.size()}
