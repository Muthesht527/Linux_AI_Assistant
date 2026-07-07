"""Read-only source, dependency, and documentation readers."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from assistant.project.config import ProjectConfiguration
from assistant.project.languages import LanguageDetector


class SourceCodeReader:
    """Read and inspect source files without modifying them."""

    def __init__(self, configuration: ProjectConfiguration | None = None) -> None:
        self.configuration = configuration or ProjectConfiguration()
        self.detector = LanguageDetector()

    def read(self, path: Path) -> dict[str, Any]:
        """Return source content and detected symbols for a single file."""
        text = self._read_text(path)
        return {
            "path": str(path),
            "language": self.detector.detect_file(path),
            "line_count": len(text.splitlines()),
            "imports": self.imports(path, text),
            "functions": self.functions(path, text),
            "classes": self.classes(path, text),
            "todos": self.todos(path, text),
            "summary": self.summarize(path, text),
            "content": text,
        }

    def imports(self, path: Path, text: str | None = None) -> list[str]:
        """Locate imports in supported source files."""
        content = text if text is not None else self._read_text(path)
        if path.suffix == ".py":
            try:
                tree = ast.parse(content)
            except SyntaxError:
                return []
            imports: list[str] = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)
            return sorted(dict.fromkeys(imports))
        patterns = [r"^\s*import\s+(.+?);?$", r"^\s*#include\s+[<\"](.+?)[>\"]"]
        return self._regex_lines(content, patterns)

    def functions(self, path: Path, text: str | None = None) -> list[dict[str, Any]]:
        """Locate functions and methods."""
        content = text if text is not None else self._read_text(path)
        if path.suffix == ".py":
            return self._python_nodes(content, (ast.FunctionDef, ast.AsyncFunctionDef))
        pattern = r"\b([A-Za-z_][\w]*)\s*\([^;{}]*\)\s*\{?"
        return self._symbol_matches(content, pattern)

    def classes(self, path: Path, text: str | None = None) -> list[dict[str, Any]]:
        """Locate classes."""
        content = text if text is not None else self._read_text(path)
        if path.suffix == ".py":
            return self._python_nodes(content, (ast.ClassDef,))
        return self._symbol_matches(content, r"\bclass\s+([A-Za-z_][\w]*)")

    def todos(self, path: Path, text: str | None = None) -> list[dict[str, Any]]:
        """Locate TODO and FIXME comments."""
        content = text if text is not None else self._read_text(path)
        rows = []
        for number, line in enumerate(content.splitlines(), start=1):
            if "TODO" in line or "FIXME" in line:
                rows.append({"path": str(path), "line": number, "text": line.strip()})
        return rows

    def summarize(self, path: Path, text: str | None = None) -> str:
        """Summarize a source file in a compact, factual sentence."""
        content = text if text is not None else self._read_text(path)
        funcs = len(self.functions(path, content))
        classes = len(self.classes(path, content))
        language = self.detector.detect_file(path) or "Unknown"
        return f"{language} file with {classes} classes and {funcs} functions."

    def _read_text(self, path: Path) -> str:
        if path.stat().st_size > self.configuration.maximum_file_size:
            raise ValueError(f"File exceeds maximum size: {path}")
        return path.read_text(encoding="utf-8", errors="ignore")

    def _python_nodes(self, text: str, node_types: tuple[type[ast.AST], ...]) -> list[dict[str, Any]]:
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return []
        return [
            {"name": getattr(node, "name"), "line": getattr(node, "lineno", 0)}
            for node in ast.walk(tree)
            if isinstance(node, node_types)
        ]

    def _symbol_matches(self, text: str, pattern: str) -> list[dict[str, Any]]:
        rows = []
        for number, line in enumerate(text.splitlines(), start=1):
            match = re.search(pattern, line)
            if match:
                rows.append({"name": match.group(1), "line": number})
        return rows

    def _regex_lines(self, text: str, patterns: list[str]) -> list[str]:
        values: list[str] = []
        for line in text.splitlines():
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    values.append(match.group(1).strip())
        return sorted(dict.fromkeys(values))


class DependencyReader:
    """Read dependency manifests without installing anything."""

    FILES = (
        "requirements.txt",
        "pyproject.toml",
        "package.json",
        "pom.xml",
        "build.gradle",
        "Cargo.toml",
        "go.mod",
        "CMakeLists.txt",
    )

    def read(self, root: Path) -> dict[str, Any]:
        """Return dependency information from known manifests."""
        manifests: dict[str, Any] = {}
        for name in self.FILES:
            path = root / name
            if path.exists() and path.is_file():
                manifests[name] = self._read_manifest(path)
        return manifests

    def _read_manifest(self, path: Path) -> Any:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if path.name == "requirements.txt":
            return [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]
        if path.name == "package.json":
            data = json.loads(text)
            return {
                "dependencies": data.get("dependencies", {}),
                "devDependencies": data.get("devDependencies", {}),
                "scripts": data.get("scripts", {}),
            }
        if path.name == "pom.xml":
            return self._pom_dependencies(text)
        return {"content": text[:4000]}

    def _pom_dependencies(self, text: str) -> list[str]:
        try:
            root = ElementTree.fromstring(text)
        except ElementTree.ParseError:
            return []
        dependencies = []
        for node in root.iter():
            if node.tag.endswith("dependency"):
                parts = [child.text or "" for child in node if child.tag.endswith(("groupId", "artifactId", "version"))]
                value = ":".join(part for part in parts if part)
                if value:
                    dependencies.append(value)
        return dependencies


class DocumentationReader:
    """Read and summarize README documentation."""

    NAMES = ("README.md", "README.rst", "README.txt", "README")

    def read(self, root: Path) -> dict[str, Any]:
        """Return README text and extracted sections."""
        path = next((root / name for name in self.NAMES if (root / name).exists()), None)
        if path is None:
            return {"found": False, "path": None}
        text = path.read_text(encoding="utf-8", errors="ignore")
        return {
            "found": True,
            "path": str(path),
            "purpose": self._first_paragraph(text),
            "setup": self._section(text, ("install", "setup", "running", "usage")),
            "dependencies": self._section(text, ("depend", "requirement")),
            "summary": self._first_paragraph(text),
            "content": text,
        }

    def _first_paragraph(self, text: str) -> str:
        for block in re.split(r"\n\s*\n", text.strip()):
            cleaned = re.sub(r"^#+\s*", "", block.strip())
            if cleaned:
                return cleaned[:500]
        return ""

    def _section(self, text: str, names: tuple[str, ...]) -> str:
        lines = text.splitlines()
        for index, line in enumerate(lines):
            lowered = line.strip().lower()
            if lowered.startswith("#") and any(name in lowered for name in names):
                collected = []
                for row in lines[index + 1 :]:
                    if row.startswith("#") and collected:
                        break
                    collected.append(row)
                return "\n".join(collected).strip()[:1500]
        return ""
