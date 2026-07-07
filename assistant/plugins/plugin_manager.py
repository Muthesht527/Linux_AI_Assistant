"""Discover and register plugin tools automatically."""

from __future__ import annotations

import importlib
from pathlib import Path
from pkgutil import iter_modules
from assistant.core.base_tool import BaseTool


class PluginManager:
    """Discover plugin modules and instantiate tool classes from them."""

    def __init__(self, package_name: str = "assistant.plugins") -> None:
        self.package_name = package_name
        self.plugins: list[BaseTool] = []

    def discover(self) -> list[BaseTool]:
        """Discover tool classes from installed plugin modules."""
        self.plugins = []
        package = importlib.import_module(self.package_name)
        package_path = getattr(package, "__file__", None)
        if package_path is None:
            return self.plugins

        package_dir = Path(package_path).resolve().parent
        for module_info in iter_modules([str(package_dir)]):
            if module_info.name.startswith("_"):
                continue

            module = importlib.import_module(f"{self.package_name}.{module_info.name}")
            for attribute_name in dir(module):
                attribute = getattr(module, attribute_name)
                if (
                    isinstance(attribute, type)
                    and issubclass(attribute, BaseTool)
                    and attribute is not BaseTool
                ):
                    self.plugins.append(attribute())

        return self.plugins
