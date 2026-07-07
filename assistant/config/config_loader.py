"""Utilities for loading local YAML configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class ConfigLoader:
    """Load and retrieve configuration values from a YAML file."""

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or Path(__file__).resolve().parent / "settings.yaml"

    def load(self) -> dict[str, Any]:
        """Read the YAML configuration into memory."""
        if not self.config_path.exists():
            return {}

        with self.config_path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a configuration value using dot-separated keys."""
        data = self.load()
        current: Any = data
        for part in key.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current
