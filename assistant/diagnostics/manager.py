"""High-level Linux diagnostics manager and analyzer."""

from __future__ import annotations

import logging
from collections.abc import Callable
from time import perf_counter
from typing import Any

from assistant.diagnostics.collectors import (
    BatteryCollector,
    CPUCollector,
    DiskCollector,
    GPUCollector,
    HardwareCollector,
    JournalReader,
    KernelCollector,
    MemoryCollector,
    NetworkInfoCollector,
    ProcessCollector,
    ServiceCollector,
    SystemInfoCollector,
    TemperatureCollector,
)
from assistant.diagnostics.command import DiagnosticsCommandRunner
from assistant.diagnostics.config import DiagnosticsConfiguration


class DiagnosticsManager:
    """Coordinate read-only diagnostics collectors."""

    def __init__(self, config: DiagnosticsConfiguration | None = None) -> None:
        self.config = config or DiagnosticsConfiguration()
        self.runner = DiagnosticsCommandRunner(self.config)
        self.logger = logging.getLogger(__name__)

    def system(self) -> dict[str, Any]:
        return self._collect("system", SystemInfoCollector().collect)

    def cpu(self) -> dict[str, Any]:
        return self._collect("cpu", CPUCollector(self.runner).collect)

    def memory(self) -> dict[str, Any]:
        return self._collect("memory", MemoryCollector().collect)

    def disk(self) -> dict[str, Any]:
        return self._collect("disk", DiskCollector(self.runner).collect)

    def battery(self) -> dict[str, Any]:
        return self._collect("battery", BatteryCollector().collect)

    def gpu(self) -> dict[str, Any]:
        return self._collect("gpu", GPUCollector(self.runner).collect)

    def usb(self) -> dict[str, Any]:
        return self._collect("usb", lambda: HardwareCollector(self.runner, self.config).usb())

    def pci(self) -> dict[str, Any]:
        return self._collect("pci", lambda: HardwareCollector(self.runner, self.config).pci())

    def hardware(self) -> dict[str, Any]:
        return self._collect("hardware", lambda: HardwareCollector(self.runner, self.config).collect())

    def processes(self) -> dict[str, Any]:
        return self._collect("processes", lambda: ProcessCollector(self.runner, self.config).collect())

    def services(self) -> dict[str, Any]:
        return self._collect("services", lambda: ServiceCollector(self.runner, self.config).collect())

    def service_status(self, service: str) -> dict[str, Any]:
        return self._collect("service_status", lambda: ServiceCollector(self.runner, self.config).status(service))

    def journal(self, errors_only: bool = False, search: str | None = None) -> dict[str, Any]:
        return self._collect("journal", lambda: JournalReader(self.runner, self.config).read(errors_only, search))

    def kernel(self) -> dict[str, Any]:
        return self._collect("kernel", KernelCollector().collect)

    def temperatures(self) -> dict[str, Any]:
        return self._collect("temperatures", TemperatureCollector().collect)

    def network(self) -> dict[str, Any]:
        return self._collect("network", lambda: NetworkInfoCollector(self.runner).collect())

    def all(self) -> dict[str, Any]:
        """Return the common diagnostics set with a summary."""
        data = {
            "system": self.system(),
            "cpu": self.cpu(),
            "memory": self.memory(),
            "disk": self.disk(),
            "battery": self.battery(),
            "gpu": self.gpu(),
            "hardware": self.hardware(),
            "processes": self.processes(),
            "services": self.services(),
            "kernel": self.kernel(),
            "network": self.network(),
        }
        data["summary"] = self.summarize(data)
        return data

    def summarize(self, data: dict[str, Any]) -> list[str]:
        """Explain notable diagnostics findings without taking action."""
        findings: list[str] = []
        memory = data.get("memory", {}).get("data", data.get("memory", {}))
        installed = memory.get("installed") or 0
        used = memory.get("used") or 0
        if installed and used / installed >= 0.85:
            findings.append("High memory usage detected.")

        disk = data.get("disk", {}).get("data", data.get("disk", {}))
        for mount in disk.get("mounts", []):
            percent = str(mount.get("usage_percent", "0")).rstrip("%")
            if percent.isdigit() and int(percent) >= 90:
                findings.append(f"Disk nearly full: {mount.get('mountpoint')}.")

        battery = data.get("battery", {}).get("data", data.get("battery", {}))
        for item in battery.get("batteries", []):
            health = item.get("health")
            if health is not None and health < 70:
                findings.append(f"Battery health is poor: {health}%.")

        cpu = data.get("cpu", {}).get("data", data.get("cpu", {}))
        temperature = cpu.get("temperature")
        if temperature is not None and temperature >= 85:
            findings.append(f"CPU temperature is high: {temperature} C.")

        services = data.get("services", {}).get("data", data.get("services", {}))
        failed = services.get("failed", [])
        if len(failed) > 3:
            findings.append(f"Too many failed services: {len(failed)}.")
        elif failed:
            findings.append(f"Failed services detected: {', '.join(failed[:3])}.")

        return findings or ["No major issues detected from collected diagnostics."]

    def _collect(self, name: str, collector: Callable[[], dict[str, Any]]) -> dict[str, Any]:
        started_at = perf_counter()
        try:
            data = collector()
            elapsed = perf_counter() - started_at
            self.logger.info("diagnostics=%s elapsed=%.6f success=True", name, elapsed)
            return {"name": name, "success": True, "data": data, "elapsed": elapsed}
        except Exception as exc:
            elapsed = perf_counter() - started_at
            self.logger.warning("diagnostics=%s elapsed=%.6f error=%s", name, elapsed, exc)
            return {"name": name, "success": False, "data": {}, "elapsed": elapsed, "error": str(exc)}
