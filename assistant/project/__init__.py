"""Read-only project, repository, code, error, and Git analysis."""

from assistant.project.config import ProjectConfiguration
from assistant.project.errors import ErrorAnalyzer, StackTraceParser
from assistant.project.git import GitDiffReader, GitHistoryReader, GitRepositoryManager, GitStatusReader
from assistant.project.languages import LanguageDetector
from assistant.project.manager import ProjectScanner, RepositoryAnalyzer, RepositorySummary
from assistant.project.readers import DependencyReader, DocumentationReader, SourceCodeReader

__all__ = [
    "DependencyReader",
    "DocumentationReader",
    "ErrorAnalyzer",
    "GitDiffReader",
    "GitHistoryReader",
    "GitRepositoryManager",
    "GitStatusReader",
    "LanguageDetector",
    "ProjectConfiguration",
    "ProjectScanner",
    "RepositoryAnalyzer",
    "RepositorySummary",
    "SourceCodeReader",
    "StackTraceParser",
]
