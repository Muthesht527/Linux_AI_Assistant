"""Custom exceptions used by the application foundation."""

from __future__ import annotations


class AssistantError(Exception):
    """Base exception for expected application failures."""


class ConfigurationError(AssistantError):
    """Raised when configuration cannot be loaded or validated."""


class DependencyError(AssistantError):
    """Raised when a required runtime dependency is missing."""


class EnvironmentError(AssistantError):
    """Raised when the local runtime environment is unsupported."""


class StartupError(AssistantError):
    """Raised when startup cannot complete cleanly."""
