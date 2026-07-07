"""Base tool abstractions for the assistant."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Common interface for all tools in the assistant."""

    name: str = "base_tool"
    description: str = "Base tool"
    permission_level: str = "SAFE"
    timeout: int = 10

    @abstractmethod
    def schema(self) -> dict[str, Any]:
        """Return a JSON-schema-like description for the tool."""

    @abstractmethod
    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the tool with validated arguments."""
