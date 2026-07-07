"""Application bootstrap workflow for the foundation phase."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from assistant.config.config_loader import ConfigLoader
from assistant.config.settings import Settings
from assistant.core.paths import PathManager
from assistant.utils.dependencies import require_dependencies
from assistant.utils.environment import EnvironmentInfo, detect_environment, validate_python_version
from assistant.utils.logging_config import configure_logging


@dataclass(frozen=True)
class StartupContext:
    """Initialized runtime state created during startup."""

    settings: Settings
    paths: PathManager
    environment: EnvironmentInfo
    created_directories: list[Path]


def build_startup_context(config_path: Path | None = None) -> StartupContext:
    """Validate the environment and initialize foundation services.

    Args:
        config_path: Optional YAML configuration path.

    Returns:
        Fully initialized startup context.
    """
    validate_python_version()
    settings = ConfigLoader(config_path).load_settings()
    require_dependencies(settings.dependencies.packages)

    paths = PathManager.from_project_root(settings.directories)
    created_directories = paths.ensure_directories()
    configure_logging(
        log_level=settings.logging.level,
        log_dir=paths.resolve(settings.directories.logs),
        log_file=settings.logging.file_name,
        max_bytes=settings.logging.max_bytes,
        backup_count=settings.logging.backup_count,
        console=settings.logging.console,
    )
    environment = detect_environment()
    logging.getLogger(__name__).info(
        "startup_complete app=%s version=%s python=%s",
        settings.application.name,
        settings.application.version,
        environment.python_version,
    )
    return StartupContext(
        settings=settings,
        paths=paths,
        environment=environment,
        created_directories=created_directories,
    )


def startup_banner(context: StartupContext) -> str:
    """Return the startup banner displayed to CLI users."""
    return (
        f"{context.settings.application.name} "
        f"{context.settings.application.version}\n"
        f"Python {context.environment.python_version} | {context.environment.distribution}"
    )
