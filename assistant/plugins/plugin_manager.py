"""Discover, validate, and manage plugin tools automatically."""

from __future__ import annotations

import importlib
import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from pkgutil import iter_modules
from typing import Any

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
    dependencies: list[str] | None = None
    missing_dependencies: list[str] | None = None
    error: str | None = None


class PluginManager:
    """Discover plugin modules and instantiate tool classes from them."""

    def __init__(
        self,
        package_name: str = "assistant.plugins",
        disabled_plugins: list[str] | None = None,
        state_path: Path | None = None,
    ) -> None:
        self.package_name = package_name
        self.state_path = state_path or Path("assistant/cache/plugin_state.json")
        self.disabled_plugins = set(disabled_plugins or []) | set(self._load_state().get("disabled_plugins", []))
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
        self._save_state()
        for plugin in self.plugins:
            if plugin.name == name:
                plugin.enabled = False
        for metadata in self.metadata:
            if metadata.name == name:
                metadata.enabled = False

    def enable(self, name: str) -> None:
        """Enable a plugin tool by name for this manager."""
        self.disabled_plugins.discard(name)
        self._save_state()
        for plugin in self.plugins:
            if plugin.name == name:
                plugin.enabled = True
        for metadata in self.metadata:
            if metadata.name == name:
                metadata.enabled = True

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
        missing_dependencies = self.missing_dependencies(tool)
        if missing_dependencies:
            return f"Missing dependencies: {', '.join(missing_dependencies)}"
        return None

    def missing_dependencies(self, tool: BaseTool) -> list[str]:
        """Return missing optional plugin dependencies."""
        dependencies = getattr(tool, "dependencies", [])
        if not isinstance(dependencies, list):
            return ["invalid dependency metadata"]
        return [
            dependency
            for dependency in dependencies
            if isinstance(dependency, str) and importlib.util.find_spec(dependency) is None
        ]

    def _register_plugin(self, tool_class: type[BaseTool], module_name: str) -> None:
        try:
            tool = tool_class()
            error = self.validate(tool)
        except Exception as exc:
            self.errors.append(f"{module_name}.{tool_class.__name__}: {exc}")
            return

        dependencies = getattr(tool, "dependencies", [])
        if not isinstance(dependencies, list):
            dependencies = []
        missing_dependencies = self.missing_dependencies(tool)
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
            dependencies=dependencies,
            missing_dependencies=missing_dependencies,
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

    def _load_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return {}
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def _save_state(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"disabled_plugins": sorted(self.disabled_plugins)}
        self.state_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
