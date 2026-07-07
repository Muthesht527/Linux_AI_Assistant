"""Typed application settings for Linux AI Assistant."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from assistant.core.exceptions import ConfigurationError


class ApplicationSettings(BaseModel):
    """User-facing application metadata."""

    model_config = ConfigDict(extra="ignore")

    name: str = "Linux AI Assistant"
    version: str = "0.1.0"


class RuntimeSettings(BaseModel):
    """Runtime validation settings."""

    model_config = ConfigDict(extra="ignore")

    python_min_version: str = "3.12"


class DirectorySettings(BaseModel):
    """Configurable project directory names."""

    model_config = ConfigDict(extra="ignore")

    logs: Path = Path("assistant/logs")
    cache: Path = Path("assistant/cache")
    memory: Path = Path("assistant/memory")
    config: Path = Path("assistant/config")
    plugins: Path = Path("assistant/plugins")
    tests: Path = Path("tests")


class LoggingSettings(BaseModel):
    """Logging destination and formatting settings."""

    model_config = ConfigDict(extra="ignore")

    level: str = "INFO"
    file_name: str = "assistant.log"
    max_bytes: int = Field(default=1_048_576, ge=1)
    backup_count: int = Field(default=3, ge=0)
    console: bool = True


class DependencySettings(BaseModel):
    """Required import names checked during startup."""

    model_config = ConfigDict(extra="ignore")

    packages: list[str] = Field(
        default_factory=lambda: ["yaml", "pydantic", "typer", "rich"]
    )


class ConversationSettings(BaseModel):
    """Local Ollama conversation settings."""

    model_config = ConfigDict(extra="ignore")

    base_url: str = "http://localhost:11434"
    default_model: str = "qwen3"
    system_prompt: str = "You are Linux AI Assistant, a helpful local assistant."
    temperature: float = Field(default=0.7, ge=0.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    context_size: int = Field(default=4096, ge=1)
    max_history: int = Field(default=20, ge=0)
    history_enabled: bool = True
    streaming_enabled: bool = True
    request_timeout: int = Field(default=60, ge=1)


class FilesystemSettings(BaseModel):
    """Filesystem indexing, search, and reading settings."""

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


class Settings(BaseModel):
    """Complete application settings loaded from YAML."""

    model_config = ConfigDict(extra="ignore")

    application: ApplicationSettings = Field(default_factory=ApplicationSettings)
    runtime: RuntimeSettings = Field(default_factory=RuntimeSettings)
    directories: DirectorySettings = Field(default_factory=DirectorySettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    dependencies: DependencySettings = Field(default_factory=DependencySettings)
    conversation: ConversationSettings = Field(default_factory=ConversationSettings)
    filesystem: FilesystemSettings = Field(default_factory=FilesystemSettings)


def settings_from_mapping(data: dict[str, Any]) -> Settings:
    """Validate raw configuration data and return typed settings.

    Args:
        data: Raw mapping loaded from YAML.

    Returns:
        Validated application settings.

    Raises:
        ConfigurationError: If the YAML data does not match the schema.
    """
    try:
        if hasattr(Settings, "model_validate"):
            return Settings.model_validate(data)
        return Settings.parse_obj(data)
    except ValidationError as exc:
        raise ConfigurationError(f"Invalid configuration: {exc}") from exc
