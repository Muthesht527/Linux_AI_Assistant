"""Discover, validate, and manage plugin tools automatically."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from pkgutil import iter_modules

from assistant.core.base_tool import BaseTool


@dataclass(slots=True)
class PluginMetadata:
    """Metadata for one discovered plugin tool."""

    name: str
    description: str
    version: str
    author: str
    category: str
    enabled: bool
    module: str
    valid: bool
    error: str | None = None


class PluginManager:
    """Discover plugin modules and instantiate tool classes from them."""

    def __init__(
        self,
        package_name: str = "assistant.plugins",
        disabled_plugins: list[str] | None = None,
    ) -> None:
        self.package_name = package_name
        self.disabled_plugins = set(disabled_plugins or [])
        self.plugins: list[BaseTool] = []
        self.metadata: list[PluginMetadata] = []
        self.errors: list[str] = []

    def discover(self) -> list[BaseTool]:
        """Discover valid tool classes from installed plugin modules."""
        self.plugins = []
        self.metadata = []
        self.errors = []
        package = importlib.import_module(self.package_name)
        package_path = getattr(package, "__file__", None)
        if package_path is None:
            return self.plugins

        package_dir = Path(package_path).resolve().parent
        for module_info in iter_modules([str(package_dir)]):
            if module_info.name.startswith("_"):
                continue
            module_name = f"{self.package_name}.{module_info.name}"
            try:
                module = importlib.import_module(module_name)
            except Exception as exc:
                self.errors.append(f"{module_name}: {exc}")
                continue

            for attribute_name in dir(module):
                attribute = getattr(module, attribute_name)
                if not self._is_tool_class(attribute):
                    continue
                self._register_plugin(attribute, module_name)

        return self.plugins

    def list_metadata(self) -> list[PluginMetadata]:
        """Return discovered plugin metadata."""
        if not self.metadata:
            self.discover()
        return self.metadata

    def disable(self, name: str) -> None:
        """Disable a plugin tool by name for this manager."""
        self.disabled_plugins.add(name)
        for plugin in self.plugins:
            if plugin.name == name:
                plugin.enabled = False

    def enable(self, name: str) -> None:
        """Enable a plugin tool by name for this manager."""
        self.disabled_plugins.discard(name)
        for plugin in self.plugins:
            if plugin.name == name:
                plugin.enabled = True

    def reload(self) -> list[BaseTool]:
        """Reload plugin discovery."""
        importlib.invalidate_caches()
        return self.discover()

    def validate(self, tool: BaseTool) -> str | None:
        """Return a validation error, or None when valid."""
        required = ("name", "description", "version", "author", "permission_level")
        missing = [field for field in required if not getattr(tool, field, None)]
        if missing:
            return f"Missing metadata: {', '.join(missing)}"
        if not isinstance(tool.name, str) or not tool.name.strip():
            return "Plugin name must be a non-empty string"
        return None

    def _register_plugin(self, tool_class: type[BaseTool], module_name: str) -> None:
        try:
            tool = tool_class()
            error = self.validate(tool)
        except Exception as exc:
            self.errors.append(f"{module_name}.{tool_class.__name__}: {exc}")
            return

        tool.enabled = tool.enabled and tool.name not in self.disabled_plugins
        metadata = PluginMetadata(
            name=tool.name,
            description=tool.description,
            version=tool.version,
            author=tool.author,
            category=tool.category,
            enabled=tool.enabled,
            module=module_name,
            valid=error is None,
            error=error,
        )
        self.metadata.append(metadata)
        if error is None:
            self.plugins.append(tool)
        else:
            self.errors.append(f"{tool.name}: {error}")

    @staticmethod
    def _is_tool_class(attribute: object) -> bool:
        return (
            isinstance(attribute, type)
            and issubclass(attribute, BaseTool)
            and attribute is not BaseTool
        )
