"""Configuration for read-only Linux diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class DiagnosticsConfiguration:
    """Runtime limits for diagnostics collection."""

    max_processes: int = 10
    journal_lines: int = 100
    timeout: int = 5
    ignored_services: list[str] = field(default_factory=list)
    ignored_devices: list[str] = field(default_factory=list)
