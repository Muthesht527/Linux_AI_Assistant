"""Filesystem metadata extraction."""

from __future__ import annotations

import mimetypes
import pwd
import stat
from datetime import datetime
from pathlib import Path
from typing import Any


class FilesystemMetadata:
    """Expose normalized metadata for files and directories."""

    def get(self, path: Path) -> dict[str, Any]:
        """Return file metadata without leaking low-level exceptions."""
        resolved = path.expanduser().resolve()
        info = resolved.stat()
        owner = self._owner(info.st_uid)
        return {
            "path": str(resolved),
            "name": resolved.name,
            "size": info.st_size,
            "extension": resolved.suffix.lower(),
            "owner": owner,
            "permissions": stat.filemode(info.st_mode),
            "modified": self._timestamp(info.st_mtime),
            "created": self._timestamp(getattr(info, "st_birthtime", info.st_ctime)),
            "mime_type": mimetypes.guess_type(str(resolved))[0],
            "is_dir": resolved.is_dir(),
            "is_file": resolved.is_file(),
        }

    def _owner(self, uid: int) -> str:
        """Return a username for a uid when available."""
        try:
            return pwd.getpwuid(uid).pw_name
        except KeyError:
            return str(uid)

    def _timestamp(self, value: float) -> str:
        """Format a filesystem timestamp as ISO text."""
        return datetime.fromtimestamp(value).isoformat(timespec="seconds")
