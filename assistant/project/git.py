"""Read-only Git repository helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from assistant.project.config import ProjectConfiguration


class GitRepositoryManager:
    """Run non-mutating Git inspection commands."""

    def __init__(self, configuration: ProjectConfiguration | None = None) -> None:
        self.configuration = configuration or ProjectConfiguration()

    def root(self, path: Path) -> Path | None:
        """Return the repository root for a path when it is in Git."""
        result = self._git(path, ["rev-parse", "--show-toplevel"])
        if result["returncode"] != 0:
            return None
        return Path(result["stdout"].strip())

    def is_repository(self, path: Path) -> bool:
        """Return whether the path is inside a Git repository."""
        return self.root(path) is not None

    def status(self, path: Path) -> dict[str, Any]:
        """Return branch, changed files, untracked files, and ignored files."""
        root = self.root(path) or path
        branch = self._git(root, ["branch", "--show-current"])["stdout"].strip()
        porcelain = self._git(root, ["status", "--porcelain=v1"])["stdout"].splitlines()
        ignored = self._git(root, ["status", "--ignored", "--porcelain=v1"])["stdout"].splitlines()
        return {
            "repository_root": str(root),
            "current_branch": branch or "HEAD",
            "changed_files": [line[3:] for line in porcelain if not line.startswith("??")],
            "untracked_files": [line[3:] for line in porcelain if line.startswith("??")],
            "ignored_files": [line[3:] for line in ignored if line.startswith("!!")],
            "clean": not porcelain,
        }

    def history(self, path: Path, depth: int | None = None) -> dict[str, Any]:
        """Return recent commit history."""
        root = self.root(path) or path
        limit = depth or self.configuration.git_history_depth
        result = self._git(root, ["log", f"-n{limit}", "--pretty=format:%h%x09%an%x09%ad%x09%s", "--date=short"])
        commits = []
        for line in result["stdout"].splitlines():
            parts = line.split("\t", 3)
            if len(parts) == 4:
                commits.append({"hash": parts[0], "author": parts[1], "date": parts[2], "subject": parts[3]})
        return {"repository_root": str(root), "commits": commits}

    def diff(self, path: Path) -> dict[str, Any]:
        """Return current working tree diff and changed file names."""
        root = self.root(path) or path
        names = self._git(root, ["diff", "--name-only"])["stdout"].splitlines()
        diff = self._git(root, ["diff", "--stat"])["stdout"]
        return {"repository_root": str(root), "changed_files": names, "diff_stat": diff}

    def _git(self, path: Path, args: list[str]) -> dict[str, Any]:
        command = ["git", "-C", str(path), *args]
        completed = subprocess.run(
            command,
            capture_output=True,
            check=False,
            encoding="utf-8",
            errors="ignore",
            timeout=10,
        )
        return {
            "command": command,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "returncode": completed.returncode,
        }


class GitStatusReader(GitRepositoryManager):
    """Compatibility reader for Git status."""


class GitHistoryReader(GitRepositoryManager):
    """Compatibility reader for Git history."""


class GitDiffReader(GitRepositoryManager):
    """Compatibility reader for Git diff."""
