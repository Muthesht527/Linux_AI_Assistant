"""Tool registry, permission, dispatch, and execution framework."""

from __future__ import annotations

import importlib
import importlib.resources
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pkgutil import iter_modules
from time import perf_counter
from typing import Any

from assistant.core.production import get_runtime
from assistant.core.base_tool import (
    BaseTool,
    PermissionLevel,
    ToolContext,
    ToolException,
    ToolResult,
    ToolValidator,
)


class ToolRegistry:
    """Store and query registered tools by unique name."""

    def __init__(self, tools: list[BaseTool] | None = None) -> None:
        self._tools: dict[str, BaseTool] = {}
        for tool in tools or []:
            self.register(tool)

    def register(self, tool: BaseTool) -> None:
        """Register a tool with a unique name."""
        if not isinstance(tool, BaseTool):
            raise ToolException("Registered object must inherit BaseTool")
        if tool.name in self._tools:
            raise ToolException(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool
        get_runtime().cache.invalidate(f"tool:{tool.name}")

    def unregister(self, name: str) -> None:
        """Remove a tool from the registry."""
        if name not in self._tools:
            raise ToolException(f"Tool not registered: {name}")
        del self._tools[name]
        get_runtime().cache.invalidate(f"tool:{name}")

    def reload(self, tools: list[BaseTool]) -> None:
        """Replace all registered tools."""
        self._tools = {}
        get_runtime().cache.invalidate()
        for tool in tools:
            self.register(tool)

    def find(self, name: str) -> BaseTool | None:
        """Return a tool by name."""
        runtime = get_runtime()
        cache_key = f"tool:{name}"
        cached = runtime.cache.get(cache_key)
        if isinstance(cached, BaseTool):
            return cached
        tool = self._tools.get(name)
        if tool is not None:
            runtime.cache.set(cache_key, tool)
        return tool

    def list(self) -> list[BaseTool]:
        """Return all registered tools."""
        return list(self._tools.values())

    def categories(self) -> list[str]:
        """Return registered tool categories."""
        return sorted({tool.category for tool in self._tools.values()})

    def enabled(self) -> list[BaseTool]:
        """Return enabled tools."""
        return [tool for tool in self._tools.values() if tool.enabled]

    def disabled(self) -> list[BaseTool]:
        """Return disabled tools."""
        return [tool for tool in self._tools.values() if not tool.enabled]


class PermissionManager:
    """Authorize tool execution based on the declared permission level."""

    def check(self, tool: BaseTool, context: ToolContext | None = None) -> None:
        """Raise when a tool is blocked or needs unapproved confirmation."""
        try:
            permission = PermissionLevel(str(tool.permission_level).upper())
        except ValueError as exc:
            raise ToolException(
                f"Invalid permission level for tool: {tool.name}"
            ) from exc
        context = context or ToolContext()
        if permission is PermissionLevel.SAFE:
            return
        if permission is PermissionLevel.BLOCKED:
            raise ToolException(f"Tool is blocked: {tool.name}")
        if tool.name not in context.approved_permissions:
            raise ToolException(f"Tool requires permission: {tool.name}")


class ToolExecutor:
    """Execute tools and normalize every outcome to ToolResult."""

    def execute(
        self,
        tool: BaseTool,
        arguments: dict[str, Any],
        context: ToolContext | None = None,
    ) -> ToolResult:
        """Run a tool with timeout handling."""
        if not tool.enabled:
            get_runtime().statistics.record_error(f"tool_disabled:{tool.name}")
            return ToolResult(
                success=False,
                message=f"Tool is disabled: {tool.name}",
                tool_name=tool.name,
                error="Tool disabled",
            )

        started_at = perf_counter()
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(tool.execute, **arguments)
                result = future.result(timeout=tool.timeout)
        except TimeoutError:
            get_runtime().statistics.record_error(f"tool_timeout:{tool.name}")
            return ToolResult(
                success=False,
                message=f"Tool timed out after {tool.timeout} seconds",
                execution_time=perf_counter() - started_at,
                tool_name=tool.name,
                error="Tool timeout",
            )
        except Exception as exc:
            get_runtime().statistics.record_error(f"tool_failed:{tool.name}")
            return ToolResult(
                success=False,
                message=f"Tool failed: {tool.name}",
                execution_time=perf_counter() - started_at,
                tool_name=tool.name,
                error=str(exc),
            )

        if isinstance(result, ToolResult):
            runtime = get_runtime()
            runtime.statistics.record_tool(tool.name)
            runtime.statistics.performance.record(result.execution_time)
            runtime.memory.session.remember_tool(tool.name)
            return result
        if isinstance(result, dict):
            get_runtime().statistics.record_tool(tool.name)
            return ToolResult(
                success="error" not in result,
                message="Tool executed",
                data=result,
                execution_time=perf_counter() - started_at,
                tool_name=tool.name,
                error=result.get("error"),
            )
        get_runtime().statistics.record_tool(tool.name)
        return ToolResult(
            success=True,
            message="Tool executed",
            data={"result": result},
            execution_time=perf_counter() - started_at,
            tool_name=tool.name,
        )


class ToolDispatcher:
    """Validate, authorize, and execute tools through one path."""

    def __init__(
        self,
        registry: ToolRegistry,
        permission_manager: PermissionManager | None = None,
        validator: ToolValidator | None = None,
        executor: ToolExecutor | None = None,
    ) -> None:
        self.registry = registry
        self.permission_manager = permission_manager or PermissionManager()
        self.validator = validator or ToolValidator()
        self.executor = executor or ToolExecutor()

    def dispatch(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        context: ToolContext | None = None,
    ) -> ToolResult:
        """Execute a registered tool and always return ToolResult."""
        arguments = arguments or {}
        tool = self.registry.find(tool_name)
        if tool is None:
            return ToolResult(
                success=False,
                message=f"Tool not found: {tool_name}",
                tool_name=tool_name,
                error="Tool not found",
            )

        try:
            self.validator.validate(tool.schema(), arguments)
            self.permission_manager.check(tool, context)
        except ToolException as exc:
            return ToolResult(
                success=False,
                message=str(exc),
                tool_name=tool.name,
                error=str(exc),
            )

        return self.executor.execute(tool, arguments, context)


class ToolLoader:
    """Load tool classes from a package."""

    def load(self, package_name: str = "assistant.tools") -> list[BaseTool]:
        """Discover BaseTool subclasses from modules in a package."""
        package = importlib.import_module(package_name)
        package_file = getattr(package, "__file__", None)
        if package_file is None:
            return []

        tools: list[BaseTool] = []
        package_dir = importlib.resources.files(package_name)
        for module_info in iter_modules([str(package_dir)]):
            if module_info.name.startswith("_"):
                continue
            module = importlib.import_module(f"{package_name}.{module_info.name}")
            for attribute_name in dir(module):
                attribute = getattr(module, attribute_name)
                if (
                    isinstance(attribute, type)
                    and issubclass(attribute, BaseTool)
                    and attribute is not BaseTool
                ):
                    tools.append(attribute())
        return tools


class ToolManager:
    """High-level facade for loading, registering, and dispatching tools."""

    def __init__(self, tools: list[BaseTool] | None = None) -> None:
        self.registry = ToolRegistry(tools)
        self.dispatcher = ToolDispatcher(self.registry)
        self.loader = ToolLoader()

    def load_package(self, package_name: str = "assistant.tools") -> list[BaseTool]:
        """Load tools from a package and register them."""
        tools = self.loader.load(package_name)
        for tool in tools:
            if self.registry.find(tool.name) is None:
                self.registry.register(tool)
        return tools

    def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        context: ToolContext | None = None,
    ) -> ToolResult:
        """Dispatch a tool by name."""
        return self.dispatcher.dispatch(tool_name, arguments, context)


class ToolEngine(ToolManager):
    """Backward-compatible engine facade used by earlier phases."""

    def register(self, tool: BaseTool) -> None:
        """Register a tool with the engine."""
        self.registry.register(tool)

    def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        context: ToolContext | None = None,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute a tool by name through the dispatcher."""
        payload = arguments or {}
        payload.update(kwargs)
        return self.dispatcher.dispatch(tool_name, payload, context)


__all__ = [
    "BaseTool",
    "PermissionLevel",
    "PermissionManager",
    "ToolContext",
    "ToolDispatcher",
    "ToolEngine",
    "ToolException",
    "ToolExecutor",
    "ToolLoader",
    "ToolManager",
    "ToolRegistry",
    "ToolResult",
    "ToolValidator",
]
