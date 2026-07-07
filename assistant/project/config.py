"""Project analysis configuration."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ProjectConfiguration(BaseModel):
    """Read-only repository analysis limits."""

    model_config = ConfigDict(extra="ignore")

    ignored_folders: list[str] = Field(
        default_factory=lambda: [
            ".git",
            ".venv",
            "__pycache__",
            "node_modules",
            ".cache",
            ".pytest_cache",
            ".ruff_cache",
            "dist",
            "build",
        ]
    )
    ignored_languages: list[str] = Field(default_factory=list)
    maximum_repository_size: int = Field(default=524_288_000, ge=1)
    maximum_file_size: int = Field(default=1_048_576, ge=1)
    maximum_files_analyzed: int = Field(default=500, ge=1)
    git_history_depth: int = Field(default=10, ge=1)
