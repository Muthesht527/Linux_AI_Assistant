"""Programming language and project type detection."""

from __future__ import annotations

from pathlib import Path


class LanguageDetector:
    """Detect source languages from file names and extensions."""

    EXTENSIONS = {
        ".py": "Python",
        ".java": "Java",
        ".c": "C",
        ".h": "C",
        ".cpp": "C++",
        ".cc": "C++",
        ".cxx": "C++",
        ".hpp": "C++",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".html": "HTML",
        ".htm": "HTML",
        ".css": "CSS",
        ".json": "JSON",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".md": "Markdown",
        ".xml": "XML",
        ".sh": "Shell",
        ".bash": "Shell",
        ".sql": "SQL",
        ".rs": "Rust",
        ".go": "Go",
    }
    NAMES = {
        "Dockerfile": "Dockerfile",
        "Makefile": "Makefile",
        "CMakeLists.txt": "CMake",
    }

    def detect_file(self, path: Path) -> str | None:
        """Return a language name for a path when supported."""
        if path.name in self.NAMES:
            return self.NAMES[path.name]
        return self.EXTENSIONS.get(path.suffix.lower())

    def summarize(self, files: list[Path]) -> dict[str, int]:
        """Count detected languages for files."""
        counts: dict[str, int] = {}
        for path in files:
            language = self.detect_file(path)
            if language:
                counts[language] = counts.get(language, 0) + 1
        return dict(sorted(counts.items()))


class ProjectTypeDetector:
    """Detect common repository ecosystems and frameworks."""

    MARKERS = {
        "Git repository": [".git"],
        "Python project": ["requirements.txt", "pyproject.toml", "setup.py"],
        "Java project": ["pom.xml", "build.gradle", "settings.gradle"],
        "Node project": ["package.json"],
        "CMake project": ["CMakeLists.txt"],
        "Gradle project": ["build.gradle", "settings.gradle"],
        "Maven project": ["pom.xml"],
        "Rust project": ["Cargo.toml"],
        "Go project": ["go.mod"],
    }

    def detect(self, root: Path) -> list[str]:
        """Return detected project types for a repository root."""
        found = [
            project_type
            for project_type, markers in self.MARKERS.items()
            if any((root / marker).exists() for marker in markers)
        ]
        package = root / "package.json"
        if package.exists():
            text = package.read_text(encoding="utf-8", errors="ignore").lower()
            for framework in ("react", "vue", "angular"):
                if framework in text:
                    found.append(framework.title())
        for marker, framework in {
            "manage.py": "Django",
            "app.py": "Flask/FastAPI",
            "main.py": "Python application",
        }.items():
            if (root / marker).exists():
                found.append(framework)
        return sorted(dict.fromkeys(found))
