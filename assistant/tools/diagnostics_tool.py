"""Tool Engine adapters for read-only Linux diagnostics."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from assistant.config.config_loader import ConfigLoader
from assistant.core.base_tool import BaseTool, PermissionLevel, ToolResult
from assistant.diagnostics import DiagnosticsConfiguration, DiagnosticsManager


def _manager() -> DiagnosticsManager:
    """Create a diagnostics manager from application settings."""
    settings = ConfigLoader().load_settings()
    return DiagnosticsManager(DiagnosticsConfiguration(**settings.diagnostics.model_dump()))


class DiagnosticsTool(BaseTool):
    """Collect a complete read-only diagnostics snapshot."""

    name = "diagnostics"
    description = "Collect a complete read-only Linux diagnostics snapshot."
    category = "diagnostics"
    permission_level = PermissionLevel.SAFE
    timeout = 15

    def execute(self, **kwargs: Any) -> ToolResult:
        del kwargs
        return self._execute_action("all")

    def _execute_action(self, action: str, **kwargs: Any) -> ToolResult:
        started_at = perf_counter()
        manager = _manager()
        try:
            method = getattr(manager, action)
            data = method(**kwargs)
            return self.result(
                success=bool(data.get("success", True)),
                message=f"{self.name} completed",
                data=data,
                started_at=started_at,
                error=data.get("error"),
            )
        except Exception as exc:
            return self.result(
                success=False,
                message=f"{self.name} failed",
                data={"error": str(exc)},
                started_at=started_at,
                error=str(exc),
            )


class SystemInfoTool(DiagnosticsTool):
    name = "system_info"
    description = "Collect read-only system identity information."

    def execute(self, **kwargs: Any) -> ToolResult:
        del kwargs
        return self._execute_action("system")


class CPUInfoTool(DiagnosticsTool):
    name = "cpu_info"
    description = "Collect read-only CPU diagnostics."

    def execute(self, **kwargs: Any) -> ToolResult:
        del kwargs
        return self._execute_action("cpu")


class MemoryInfoTool(DiagnosticsTool):
    name = "memory_info"
    description = "Collect read-only memory diagnostics."

    def execute(self, **kwargs: Any) -> ToolResult:
        del kwargs
        return self._execute_action("memory")


class DiskInfoTool(DiagnosticsTool):
    name = "disk_info"
    description = "Collect read-only disk diagnostics."

    def execute(self, **kwargs: Any) -> ToolResult:
        del kwargs
        return self._execute_action("disk")


class BatteryInfoTool(DiagnosticsTool):
    name = "battery_info"
    description = "Collect read-only battery diagnostics."

    def execute(self, **kwargs: Any) -> ToolResult:
        del kwargs
        return self._execute_action("battery")


class GPUInfoTool(DiagnosticsTool):
    name = "gpu_info"
    description = "Collect read-only GPU diagnostics."

    def execute(self, **kwargs: Any) -> ToolResult:
        del kwargs
        return self._execute_action("gpu")


class USBTool(DiagnosticsTool):
    name = "usb_info"
    description = "Collect read-only USB device diagnostics."

    def execute(self, **kwargs: Any) -> ToolResult:
        del kwargs
        return self._execute_action("usb")


class PCITool(DiagnosticsTool):
    name = "pci_info"
    description = "Collect read-only PCI device diagnostics."

    def execute(self, **kwargs: Any) -> ToolResult:
        del kwargs
        return self._execute_action("pci")


class ProcessTool(DiagnosticsTool):
    name = "process_info"
    description = "Collect read-only process diagnostics."

    def execute(self, **kwargs: Any) -> ToolResult:
        del kwargs
        return self._execute_action("processes")


class ServiceTool(DiagnosticsTool):
    name = "service_info"
    description = "Read active, failed, or named systemd service status."
    parameter_schema = {
        "type": "object",
        "properties": {"service": {"type": "string"}},
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        service = kwargs.get("service")
        if service:
            return self._execute_action("service_status", service=str(service))
        return self._execute_action("services")


class JournalTool(DiagnosticsTool):
    name = "journal_info"
    description = "Read recent systemd journal lines."
    parameter_schema = {
        "type": "object",
        "properties": {
            "errors_only": {"type": "boolean"},
            "search": {"type": "string"},
        },
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        return self._execute_action(
            "journal",
            errors_only=bool(kwargs.get("errors_only", False)),
            search=kwargs.get("search"),
        )


class KernelTool(DiagnosticsTool):
    name = "kernel_info"
    description = "Collect read-only kernel diagnostics."

    def execute(self, **kwargs: Any) -> ToolResult:
        del kwargs
        return self._execute_action("kernel")


class NetworkInfoTool(DiagnosticsTool):
    name = "network_info"
    description = "Collect read-only network interface information."

    def execute(self, **kwargs: Any) -> ToolResult:
        del kwargs
        return self._execute_action("network")


class HardwareInfoTool(DiagnosticsTool):
    name = "hardware_info"
    description = "Collect read-only USB, PCI, and GPU diagnostics."

    def execute(self, **kwargs: Any) -> ToolResult:
        del kwargs
        return self._execute_action("hardware")
