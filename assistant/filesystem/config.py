"""Filesystem subsystem configuration and mount discovery."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class FilesystemConfiguration(BaseModel):
    """User-configurable filesystem behavior."""

    model_config = ConfigDict(extra="ignore")

    indexed_paths: list[Path] = Field(default_factory=list)
    ignored_folders: list[str] = Field(
        default_factory=lambda: [
            ".git",
            ".venv",
            "__pycache__",
            "node_modules",
            ".cache",
            "Trash",
        ]
    )
    ignored_extensions: list[str] = Field(default_factory=list)
    maximum_file_size: int = Field(default=10_485_760, ge=1)
    cache_size: int = Field(default=256, ge=1)
    index_location: Path = Path("assistant/cache/filesystem_index.sqlite3")
    disabled_locations: list[Path] = Field(default_factory=list)
    include_root: bool = True
    include_home: bool = True
    include_mnt: bool = True
    include_media: bool = True

    def resolved_index_location(self, project_root: Path) -> Path:
        """Return an absolute SQLite index path."""
        location = self.index_location.expanduser()
        if location.is_absolute():
            return location
        return project_root / location

    def detected_roots(self) -> list[Path]:
        """Return configured or automatically detected searchable roots."""
        if self.indexed_paths:
            candidates = [path.expanduser() for path in self.indexed_paths]
        else:
            candidates = self._default_candidates()
        disabled = {
            path.expanduser().resolve()
            for path in self.disabled_locations
            if path.exists()
        }
        roots: list[Path] = []
        seen: set[Path] = set()
        for candidate in candidates:
            try:
                resolved = candidate.expanduser().resolve()
            except OSError:
                continue
            if (
                not resolved.exists()
                or not resolved.is_dir()
                or resolved in seen
                or resolved in disabled
            ):
                continue
            roots.append(resolved)
            seen.add(resolved)
        return roots

    def _default_candidates(self) -> list[Path]:
        """Build default root candidates without assuming they exist."""
        candidates: list[Path] = []
        if self.include_root:
            candidates.append(Path("/"))
        if self.include_home:
            candidates.append(Path.home())
            candidates.append(Path("/home"))
        if self.include_mnt:
            candidates.extend(self._children(Path("/mnt")))
        if self.include_media:
            candidates.extend(self._children(Path("/media")))
        candidates.extend(self._mounted_partitions())
        return candidates

    def _children(self, parent: Path) -> list[Path]:
        """Return direct child paths for a mount parent."""
        try:
            return [path for path in parent.iterdir() if path.exists()]
        except OSError:
            return []

    def _mounted_partitions(self) -> list[Path]:
        """Read Linux mount points from /proc/mounts."""
        mounts = Path("/proc/mounts")
        if not mounts.exists():
            return []
        candidates: list[Path] = []
        try:
            ignored_types = {
                "autofs",
                "bpf",
                "cgroup",
                "cgroup2",
                "configfs",
                "debugfs",
                "devpts",
                "devtmpfs",
                "fusectl",
                "nsfs",
                "proc",
                "pstore",
                "securityfs",
                "squashfs",
                "sysfs",
                "tmpfs",
                "tracefs",
            }
            for line in mounts.read_text(encoding="utf-8", errors="ignore").splitlines():
                parts = line.split()
                if len(parts) >= 3 and parts[2] not in ignored_types:
                    path = Path(parts[1].replace("\\040", " "))
                    if self._is_user_visible_mount(path):
                        candidates.append(path)
        except OSError:
            return []
        return candidates

    def _is_user_visible_mount(self, path: Path) -> bool:
        """Return whether a mount is useful to expose to filesystem search."""
        text = str(path)
        if text.startswith("/run/user/") and "/gvfs" in text:
            return True
        hidden_prefixes = ("/proc", "/sys", "/dev", "/run", "/tmp", "/boot")
        return not text.startswith(hidden_prefixes)
