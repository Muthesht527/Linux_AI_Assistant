"""Logging configuration helpers for the local assistant."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging(
    log_level: str = "INFO",
    log_dir: Path | None = None,
    log_file: str = "assistant.log",
    max_bytes: int = 1_048_576,
    backup_count: int = 3,
    console: bool = True,
) -> None:
    """Configure console and rotating file logging.

    Args:
        log_level: Logging level name.
        log_dir: Directory where log files are written.
        log_file: Log file name inside the directory.
        max_bytes: Maximum size before rotation.
        backup_count: Number of rotated files to keep.
        console: Whether to also log to the console.
    """
    target_dir = log_dir or Path(__file__).resolve().parents[1] / "logs"
    target_dir.mkdir(parents=True, exist_ok=True)
    log_path = target_dir / log_file

    level = getattr(logging, log_level.upper(), logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    root_logger.addHandler(file_handler)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        root_logger.addHandler(console_handler)
