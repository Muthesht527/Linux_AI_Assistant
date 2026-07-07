"""Dependency validation for startup and diagnostics."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass

from assistant.core.exceptions import DependencyError


@dataclass(frozen=True)
class DependencyCheck:
    """Result of checking required runtime packages."""

    missing: list[str]

    @property
    def ok(self) -> bool:
        """Return whether every required package is importable."""
        return not self.missing


def check_dependencies(packages: list[str]) -> DependencyCheck:
    """Check whether required import names are available."""
    missing = [package for package in packages if importlib.util.find_spec(package) is None]
    return DependencyCheck(missing=missing)


def require_dependencies(packages: list[str]) -> None:
    """Raise a friendly error when any required package is unavailable."""
    result = check_dependencies(packages)
    if result.ok:
        return
    missing = ", ".join(result.missing)
    raise DependencyError(
        "Missing required packages: "
        f"{missing}. Install dependencies with `python3 -m pip install -r requirements.txt`."
    )
