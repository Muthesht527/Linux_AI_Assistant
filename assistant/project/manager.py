"""Repository scanning and summary orchestration."""

from __future__ import annotations

import logging
from pathlib import Path
from time import perf_counter
from typing import Any

from assistant.project.config import ProjectConfiguration
from assistant.project.git import GitRepositoryManager
from assistant.project.languages import LanguageDetector, ProjectTypeDetector
from assistant.project.readers import DependencyReader, DocumentationReader, SourceCodeReader

logger = logging.getLogger(__name__)


class ProjectScanner:
    """Scan a repository directory with read-only file inspection."""

    def __init__(self, configuration: ProjectConfiguration | None = None) -> None:
        self.configuration = configuration or ProjectConfiguration()
        self.detector = LanguageDetector()

    def files(self, root: Path) -> list[Path]:
        """Return supported files within configured limits."""
        started_at = perf_counter()
        root = root.expanduser().resolve()
        collected: list[Path] = []
        total_size = 0
        ignored = set(self.configuration.ignored_folders)
        ignored_languages = set(self.configuration.ignored_languages)
        for path in root.rglob("*"):
            if len(collected) >= self.configuration.maximum_files_analyzed:
                break
            if any(part in ignored for part in path.parts):
                continue
            if not path.is_file():
                continue
            try:
                size = path.stat().st_size
            except OSError:
                continue
            language = self.detector.detect_file(path)
            if not language or language in ignored_languages:
                continue
            if size > self.configuration.maximum_file_size:
                continue
            total_size += size
            if total_size > self.configuration.maximum_repository_size:
                break
            collected.append(path)
        logger.info("Repository scanned", extra={"root": str(root), "files": len(collected), "seconds": perf_counter() - started_at})
        return collected


class RepositoryAnalyzer:
    """Analyze project type, languages, docs, dependencies, source, and Git."""

    def __init__(self, configuration: ProjectConfiguration | None = None) -> None:
        self.configuration = configuration or ProjectConfiguration()
        self.scanner = ProjectScanner(self.configuration)
        self.languages = LanguageDetector()
        self.types = ProjectTypeDetector()
        self.source = SourceCodeReader(self.configuration)
        self.dependencies = DependencyReader()
        self.docs = DocumentationReader()
        self.git = GitRepositoryManager(self.configuration)

    def analyze(self, path: Path) -> dict[str, Any]:
        """Return a complete read-only repository analysis."""
        root = path.expanduser().resolve()
        git_root = self.git.root(root)
        if git_root:
            root = git_root
        files = self.scanner.files(root)
        source_summaries = [self._source_summary(file) for file in files[:50]]
        data = {
            "root": str(root),
            "is_git_repository": git_root is not None,
            "project_types": self.types.detect(root),
            "languages": self.languages.summarize(files),
            "files_analyzed": len(files),
            "dependencies": self.dependencies.read(root),
            "readme": self.docs.read(root),
            "source_files": source_summaries,
        }
        if git_root:
            data["git"] = self.git.status(root)
        return data

    def search_symbols(self, path: Path, query: str, kind: str) -> list[dict[str, Any]]:
        """Search functions, classes, TODOs, or content in scanned files."""
        rows: list[dict[str, Any]] = []
        for file in self.scanner.files(path):
            try:
                text = file.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if kind == "code":
                for number, line in enumerate(text.splitlines(), start=1):
                    if query.lower() in line.lower():
                        rows.append({"path": str(file), "line": number, "text": line.strip()})
            elif kind == "function":
                rows.extend(self._matching_symbols(file, self.source.functions(file, text), query))
            elif kind == "class":
                rows.extend(self._matching_symbols(file, self.source.classes(file, text), query))
            elif kind == "todo":
                rows.extend(self.source.todos(file, text))
        return rows[:100]

    def _source_summary(self, path: Path) -> dict[str, Any]:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            return {
                "path": str(path),
                "language": self.languages.detect_file(path),
                "summary": self.source.summarize(path, text),
            }
        except OSError as exc:
            return {"path": str(path), "error": str(exc)}

    def _matching_symbols(self, path: Path, symbols: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
        return [
            {"path": str(path), **symbol}
            for symbol in symbols
            if query.lower() in str(symbol.get("name", "")).lower()
        ]


class RepositorySummary:
    """Build compact repository summaries."""

    def summarize(self, data: dict[str, Any]) -> str:
        """Return a factual summary sentence."""
        types = ", ".join(data.get("project_types", [])) or "unknown project"
        languages = ", ".join(data.get("languages", {}).keys()) or "no detected languages"
        return f"{data.get('root')} is a {types} using {languages}."
