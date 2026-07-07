"""High-level facade for the filesystem subsystem."""

from __future__ import annotations

from pathlib import Path
from typing import Any

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
        return self.indexer.rebuild(self.roots())

    def index_status(self) -> dict[str, Any]:
        """Return index status and detected roots."""
        status = self.indexer.status()
        status["roots"] = [str(path) for path in self.roots()]
        return status

    def search(self, **kwargs: Any) -> dict[str, Any]:
        """Search indexed files."""
        return self.searcher.search(**kwargs)

    def search_content(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Search inside indexed text files."""
        return self.searcher.search_content(query, **kwargs)

    def read(self, path: str | Path, preview_rows: int = 20) -> dict[str, Any]:
        """Read a supported file."""
        return self.reader.read(Path(path), preview_rows)

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
