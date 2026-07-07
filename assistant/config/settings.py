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


class TerminalSettings(BaseModel):
    """Safe terminal command execution settings."""

    model_config = ConfigDict(extra="ignore")

    allowed_commands: list[str] = Field(
        default_factory=lambda: [
            "pwd",
            "ls",
            "lsblk",
            "whoami",
            "hostname",
            "uname",
            "date",
            "free",
            "df",
            "du",
            "tree",
            "find",
            "grep",
            "cat",
            "head",
            "tail",
            "wc",
            "echo",
            "which",
            "whereis",
            "file",
            "stat",
            "id",
            "uptime",
            "env",
            "printenv",
        ]
    )
    blocked_commands: list[str] = Field(
        default_factory=lambda: [
            "sudo",
            "su",
            "rm",
            "dd",
            "mkfs",
            "fdisk",
            "shutdown",
            "reboot",
            "poweroff",
            "halt",
            "killall",
            "chmod",
            "chown",
            "systemctl",
            "journalctl",
            "apt",
            "snap",
            "flatpak",
            "mount",
            "umount",
            "curl",
            "wget",
            "ssh",
        ]
    )
    default_timeout: int = Field(default=5, ge=1)
    max_timeout: int = Field(default=15, ge=1)
    max_output_bytes: int = Field(default=20_000, ge=1)
    history_limit: int = Field(default=100, ge=1)
    default_working_directory: Path = Path.cwd()


class DiagnosticsSettings(BaseModel):
    """Read-only Linux diagnostics settings."""

    model_config = ConfigDict(extra="ignore")

    max_processes: int = Field(default=10, ge=1)
    journal_lines: int = Field(default=100, ge=1)
    timeout: int = Field(default=5, ge=1)
    ignored_services: list[str] = Field(default_factory=list)
    ignored_devices: list[str] = Field(default_factory=list)


class ProjectSettings(BaseModel):
    """Read-only project and repository analysis settings."""

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


class MemorySettings(BaseModel):
    """Session and persistent memory settings."""

    model_config = ConfigDict(extra="ignore")

    database_path: Path = Path("assistant/memory/assistant_memory.sqlite")
    max_recent_items: int = Field(default=25, ge=1)
    max_conversation_items: int = Field(default=50, ge=1)
    sensitive_keys: list[str] = Field(
        default_factory=lambda: ["password", "token", "secret", "key", "credential"]
    )


class CacheSettings(BaseModel):
    """Application cache settings."""

    model_config = ConfigDict(extra="ignore")

    max_entries: int = Field(default=256, ge=1)
    ttl_seconds: int = Field(default=300, ge=1)


class PluginSettings(BaseModel):
    """Plugin discovery and enablement settings."""

    model_config = ConfigDict(extra="ignore")

    locations: list[Path] = Field(default_factory=lambda: [Path("assistant/plugins")])
    enabled_plugins: list[str] = Field(default_factory=list)
    disabled_plugins: list[str] = Field(default_factory=list)


class UISettings(BaseModel):
    """Rich terminal UI settings."""

    model_config = ConfigDict(extra="ignore")

    theme: str = "default"
    history_length: int = Field(default=100, ge=1)


class StatisticsSettings(BaseModel):
    """Application statistics retention settings."""

    model_config = ConfigDict(extra="ignore")

    retention_days: int = Field(default=30, ge=1)


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
    terminal: TerminalSettings = Field(default_factory=TerminalSettings)
    diagnostics: DiagnosticsSettings = Field(default_factory=DiagnosticsSettings)
    project: ProjectSettings = Field(default_factory=ProjectSettings)
    memory: MemorySettings = Field(default_factory=MemorySettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    plugins: PluginSettings = Field(default_factory=PluginSettings)
    ui: UISettings = Field(default_factory=UISettings)
    statistics: StatisticsSettings = Field(default_factory=StatisticsSettings)


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
