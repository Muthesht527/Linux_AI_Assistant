"""Utilities for loading typed local YAML configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from assistant.config.settings import Settings, settings_from_mapping
from assistant.core.constants import DEFAULT_CONFIG_FILE, DEFAULT_ENCODING
from assistant.core.exceptions import ConfigurationError


class ConfigLoader:
    """Load and retrieve configuration values from a YAML file."""

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or Path(__file__).resolve().parent / DEFAULT_CONFIG_FILE

    def load(self) -> dict[str, Any]:
        """Read the YAML configuration into memory.

        Returns:
            Raw configuration mapping.

        Raises:
            ConfigurationError: If the file cannot be read or parsed.
        """
        if not self.config_path.exists():
            return {}

        stat = self.config_path.stat()
        cache_key = f"config:{self.config_path}:{stat.st_mtime_ns}:{stat.st_size}"
        from assistant.core.production import get_runtime

        cached = get_runtime().cache.get(cache_key)
        if isinstance(cached, dict):
            return cached

        try:
            with self.config_path.open("r", encoding=DEFAULT_ENCODING) as handle:
                loaded = yaml.safe_load(handle) or {}
        except OSError as exc:
            raise ConfigurationError(f"Cannot read configuration: {exc}") from exc
        except yaml.YAMLError as exc:
            raise ConfigurationError(f"Invalid YAML configuration: {exc}") from exc

        if not isinstance(loaded, dict):
            raise ConfigurationError("Configuration root must be a mapping.")
        get_runtime().cache.set(cache_key, loaded)
        return loaded

    def load_settings(self) -> Settings:
        """Load and validate typed settings."""
        data = self.load()
        normalized = _normalize_legacy_settings(data)
        return settings_from_mapping(normalized)

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a configuration value using dot-separated keys."""
        data = self.load()
        data = _add_legacy_aliases(data)
        current: Any = data
        for part in key.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current


def _normalize_legacy_settings(data: dict[str, Any]) -> dict[str, Any]:
    """Support earlier assistant.* YAML while accepting the typed schema."""
    if "assistant" not in data:
        return data

    assistant = data.get("assistant", {})
    if not isinstance(assistant, dict):
        return data

    normalized = dict(data)
    normalized.setdefault("application", {})
    normalized.setdefault("logging", {})

    if isinstance(normalized["application"], dict):
        normalized["application"].setdefault("name", assistant.get("name"))
    if isinstance(normalized["logging"], dict):
        normalized["logging"].setdefault("level", assistant.get("log_level"))
    return normalized


def _add_legacy_aliases(data: dict[str, Any]) -> dict[str, Any]:
    """Expose legacy assistant.* lookups for existing callers."""
    normalized = dict(data)
    application = normalized.get("application", {})
    logging_settings = normalized.get("logging", {})
    assistant = normalized.setdefault("assistant", {})

    if isinstance(application, dict) and isinstance(assistant, dict):
        assistant.setdefault("name", application.get("name"))
    if isinstance(logging_settings, dict) and isinstance(assistant, dict):
        assistant.setdefault("log_level", logging_settings.get("level"))
    return normalized
