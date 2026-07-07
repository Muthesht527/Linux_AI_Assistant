"""Base tool abstractions for the assistant."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from time import perf_counter
from typing import Any


class PermissionLevel(StrEnum):
    """Supported tool permission levels."""

    SAFE = "SAFE"
    ASK = "ASK"
    BLOCKED = "BLOCKED"


class ToolException(Exception):
    """Raised when tool validation, permission, or execution fails."""


@dataclass(slots=True)
class ToolContext:
    """Runtime context supplied to tool dispatch."""

    user: str | None = None
    session_id: str | None = None
    working_directory: str | None = None
    approved_permissions: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ToolResult(Mapping[str, Any]):
    """Structured result returned by every tool."""

    success: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    tool_name: str = ""
    error: str | None = None
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        """Support legacy dictionary-style access to result data."""
        if key in self.data:
            return self.data[key]
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        """Iterate over public result keys and payload keys."""
        keys = [
            "success",
            "message",
            "data",
            "execution_time",
            "tool_name",
            "error",
            "warnings",
            "metadata",
        ]
        yield from keys
        for key in self.data:
            if key not in keys:
                yield key

    def __len__(self) -> int:
        """Return the number of exposed mapping keys."""
        return len(list(iter(self)))

    def to_dict(self) -> dict[str, Any]:
        """Serialize the result for logging, display, or tests."""
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "execution_time": self.execution_time,
            "tool_name": self.tool_name,
            "error": self.error,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }


class ToolValidator:
    """Validate tool argument payloads against a small schema subset."""

    TYPE_MAP = {
        "array": list,
        "boolean": bool,
        "integer": int,
        "number": (int, float),
        "object": dict,
        "string": str,
    }

    def validate(self, schema: dict[str, Any], arguments: dict[str, Any]) -> None:
        """Validate required fields and primitive JSON-schema-like types."""
        required = schema.get("required", [])
        missing = [name for name in required if name not in arguments]
        if missing:
            raise ToolException(f"Missing required argument(s): {', '.join(missing)}")

        properties = schema.get("properties", {})
        for name, value in arguments.items():
            expected = properties.get(name, {}).get("type")
            if expected is None:
                continue
            python_type = self.TYPE_MAP.get(expected)
            if python_type is None:
                continue
            if expected == "integer" and isinstance(value, bool):
                raise ToolException(f"Argument '{name}' must be integer")
            if not isinstance(value, python_type):
                raise ToolException(f"Argument '{name}' must be {expected}")


class BaseTool(ABC):
    """Common interface for all tools in the assistant."""

    name: str = "base_tool"
    description: str = "Base tool"
    category: str = "general"
    version: str = "1.0.0"
    author: str = "Linux AI Assistant"
    permission_level: PermissionLevel | str = PermissionLevel.SAFE
    timeout: int = 10
    enabled: bool = True
    parameter_schema: dict[str, Any] = {"type": "object", "properties": {}}
    result_schema: dict[str, Any] = {"type": "object", "properties": {}}

    def schema(self) -> dict[str, Any]:
        """Return a JSON-schema-like description for the tool."""
        return self.parameter_schema

    def validate(self, **kwargs: Any) -> None:
        """Validate arguments before execution."""
        ToolValidator().validate(self.schema(), kwargs)

    def result(
        self,
        *,
        success: bool,
        message: str,
        data: dict[str, Any] | None = None,
        started_at: float | None = None,
        error: str | None = None,
        warnings: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ToolResult:
        """Build a structured tool result."""
        execution_time = 0.0 if started_at is None else perf_counter() - started_at
        return ToolResult(
            success=success,
            message=message,
            data=data or {},
            execution_time=execution_time,
            tool_name=self.name,
            error=error,
            warnings=warnings or [],
            metadata=metadata or {},
        )

    @abstractmethod
    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with validated arguments."""
