"""Runtime environment detection and validation helpers."""

from __future__ import annotations

import platform
import sys
from dataclasses import dataclass
from pathlib import Path

from assistant.core.constants import MINIMUM_PYTHON_VERSION
from assistant.core.exceptions import EnvironmentError


@dataclass(frozen=True)
class EnvironmentInfo:
    """Detected operating system and Python runtime details."""

    system: str
    distribution: str
    python_version: str
    executable: str


def detect_environment() -> EnvironmentInfo:
    """Detect basic local runtime information."""
    return EnvironmentInfo(
        system=platform.system(),
        distribution=_read_distribution(),
        python_version=platform.python_version(),
        executable=sys.executable,
    )


def validate_python_version(
    minimum: tuple[int, int] = MINIMUM_PYTHON_VERSION,
) -> None:
    """Validate that the active Python version is supported.

    Args:
        minimum: Minimum major and minor Python version.

    Raises:
        EnvironmentError: If the active interpreter is too old.
    """
    if sys.version_info < minimum:
        required = ".".join(str(part) for part in minimum)
        current = platform.python_version()
        raise EnvironmentError(
            f"Python {required}+ is required. Current version is {current}."
        )


def _read_distribution() -> str:
    """Read the Linux distribution name from os-release when available."""
    os_release = Path("/etc/os-release")
    if not os_release.exists():
        return platform.platform()

    values: dict[str, str] = {}
    for line in os_release.read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value.strip().strip('"')
    return values.get("PRETTY_NAME", platform.platform())
