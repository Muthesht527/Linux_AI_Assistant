"""Tool Engine adapters for read-only coding and Git assistance."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Any

from assistant.config.config_loader import ConfigLoader
from assistant.core.base_tool import BaseTool, PermissionLevel, ToolResult
from assistant.project import (
    DependencyReader,
    DocumentationReader,
    ErrorAnalyzer,
    GitRepositoryManager,
    LanguageDetector,
    ProjectConfiguration,
    RepositoryAnalyzer,
    RepositorySummary,
)


def _configuration() -> ProjectConfiguration:
    settings = ConfigLoader().load_settings()
    data = getattr(settings, "project", ProjectConfiguration()).model_dump()
    return ProjectConfiguration(**data)


def _analyzer() -> RepositoryAnalyzer:
    return RepositoryAnalyzer(_configuration())


class ProjectSummaryTool(BaseTool):
    name = "project_summary"
    description = "Summarize a local project or repository without modifying it."
    category = "project"
    permission_level = PermissionLevel.SAFE
    timeout = 30
    parameter_schema = {"type": "object", "properties": {"path": {"type": "string"}}}

    def execute(self, **kwargs: Any) -> ToolResult:
        started_at = perf_counter()
        try:
            data = _analyzer().analyze(Path(kwargs.get("path", ".")))
            data["summary"] = RepositorySummary().summarize(data)
            return self.result(success=True, message="Project summary completed", data=data, started_at=started_at)
        except Exception as exc:
            return self.result(success=False, message="Project summary failed", data={"error": str(exc)}, started_at=started_at, error=str(exc))


class RepositorySummaryTool(ProjectSummaryTool):
    name = "repository_summary"
    description = "Summarize a Git repository without modifying it."


class CodeSearchTool(BaseTool):
    name = "code_search"
    description = "Search source code text in a local project."
    category = "project"
    permission_level = PermissionLevel.SAFE
    timeout = 30
    parameter_schema = {
        "type": "object",
        "properties": {"path": {"type": "string"}, "query": {"type": "string"}},
        "required": ["query"],
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        return _search("code", kwargs, self)


class FunctionSearchTool(CodeSearchTool):
    name = "function_search"
    description = "Search functions and methods in a local project."

    def execute(self, **kwargs: Any) -> ToolResult:
        return _search("function", kwargs, self)


class ClassSearchTool(CodeSearchTool):
    name = "class_search"
    description = "Search classes in a local project."

    def execute(self, **kwargs: Any) -> ToolResult:
        return _search("class", kwargs, self)


class TodoTool(BaseTool):
    name = "todo_search"
    description = "List TODO and FIXME comments in a local project."
    category = "project"
    permission_level = PermissionLevel.SAFE
    timeout = 30
    parameter_schema = {"type": "object", "properties": {"path": {"type": "string"}}}

    def execute(self, **kwargs: Any) -> ToolResult:
        return _search("todo", {"path": kwargs.get("path", "."), "query": ""}, self)


class DependencyTool(BaseTool):
    name = "dependency_reader"
    description = "Read dependency manifests without installing anything."
    category = "project"
    permission_level = PermissionLevel.SAFE
    parameter_schema = {"type": "object", "properties": {"path": {"type": "string"}}}

    def execute(self, **kwargs: Any) -> ToolResult:
        started_at = perf_counter()
        root = Path(kwargs.get("path", ".")).expanduser().resolve()
        data = DependencyReader().read(root)
        return self.result(success=True, message="Dependencies read", data={"dependencies": data}, started_at=started_at)


class StackTraceTool(BaseTool):
    name = "stack_trace"
    description = "Parse and explain compiler errors, runtime errors, and stack traces."
    category = "project"
    permission_level = PermissionLevel.SAFE
    parameter_schema = {
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        started_at = perf_counter()
        data = ErrorAnalyzer().analyze(str(kwargs["text"]))
        return self.result(success=True, message="Error analyzed", data=data, started_at=started_at)


class GitStatusTool(BaseTool):
    name = "git_status"
    description = "Read Git status, branch, changed files, untracked files, and ignored files."
    category = "git"
    permission_level = PermissionLevel.SAFE
    parameter_schema = {"type": "object", "properties": {"path": {"type": "string"}}}

    def execute(self, **kwargs: Any) -> ToolResult:
        return _git("status", kwargs, self)


class GitHistoryTool(GitStatusTool):
    name = "git_history"
    description = "Read recent Git commit history."
    parameter_schema = {"type": "object", "properties": {"path": {"type": "string"}, "depth": {"type": "integer"}}}

    def execute(self, **kwargs: Any) -> ToolResult:
        return _git("history", kwargs, self)


class GitDiffTool(GitStatusTool):
    name = "git_diff"
    description = "Read Git diff statistics and changed file names."

    def execute(self, **kwargs: Any) -> ToolResult:
        return _git("diff", kwargs, self)


class ReadmeTool(BaseTool):
    name = "readme_reader"
    description = "Read and summarize README documentation."
    category = "project"
    permission_level = PermissionLevel.SAFE
    parameter_schema = {"type": "object", "properties": {"path": {"type": "string"}}}

    def execute(self, **kwargs: Any) -> ToolResult:
        started_at = perf_counter()
        root = Path(kwargs.get("path", ".")).expanduser().resolve()
        data = DocumentationReader().read(root)
        return self.result(success=True, message="README read", data=data, started_at=started_at)


class LanguageDetectorTool(BaseTool):
    name = "language_detector"
    description = "Detect supported source languages in a project."
    category = "project"
    permission_level = PermissionLevel.SAFE
    parameter_schema = {"type": "object", "properties": {"path": {"type": "string"}}}

    def execute(self, **kwargs: Any) -> ToolResult:
        started_at = perf_counter()
        analyzer = _analyzer()
        files = analyzer.scanner.files(Path(kwargs.get("path", ".")))
        data = {"languages": LanguageDetector().summarize(files)}
        return self.result(success=True, message="Languages detected", data=data, started_at=started_at)


def _search(kind: str, kwargs: dict[str, Any], tool: BaseTool) -> ToolResult:
    started_at = perf_counter()
    try:
        rows = _analyzer().search_symbols(Path(kwargs.get("path", ".")), str(kwargs.get("query", "")), kind)
        return tool.result(success=True, message="Search completed", data={"results": rows, "total": len(rows)}, started_at=started_at)
    except Exception as exc:
        return tool.result(success=False, message="Search failed", data={"error": str(exc)}, started_at=started_at, error=str(exc))


def _git(action: str, kwargs: dict[str, Any], tool: BaseTool) -> ToolResult:
    started_at = perf_counter()
    try:
        manager = GitRepositoryManager(_configuration())
        path = Path(kwargs.get("path", "."))
        if action == "history":
            data = manager.history(path, kwargs.get("depth"))
        else:
            data = getattr(manager, action)(path)
        return tool.result(success=True, message=f"Git {action} read", data=data, started_at=started_at)
    except Exception as exc:
        return tool.result(success=False, message=f"Git {action} failed", data={"error": str(exc)}, started_at=started_at, error=str(exc))
