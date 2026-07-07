"""Read-only Linux diagnostics collectors."""

from __future__ import annotations

import os
import platform
import socket
import sys
from pathlib import Path
from typing import Any

from assistant.diagnostics.command import DiagnosticsCommandRunner
from assistant.diagnostics.config import DiagnosticsConfiguration


def _read(path: Path) -> str | None:
    """Read a small system file, returning None on permission or existence issues."""
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None


def _number(value: str) -> int | float | None:
    """Parse a numeric string when possible."""
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return None


def _parse_kv_lines(text: str, separator: str = ":") -> dict[str, str]:
    """Parse key-value command output."""
    data: dict[str, str] = {}
    for line in text.splitlines():
        if separator not in line:
            continue
        key, value = line.split(separator, 1)
        data[key.strip()] = value.strip()
    return data


class SystemInfoCollector:
    """Collect basic operating system identity."""

    def collect(self) -> dict[str, Any]:
        """Return system information."""
        release = _parse_kv_lines(_read(Path("/etc/os-release")) or "", "=")
        return {
            "hostname": socket.gethostname(),
            "kernel": platform.release(),
            "distribution": release.get("PRETTY_NAME", platform.platform()).strip('"'),
            "desktop_environment": os.environ.get("XDG_CURRENT_DESKTOP"),
            "window_manager": os.environ.get("XDG_SESSION_DESKTOP"),
            "architecture": platform.machine(),
            "current_user": os.environ.get("USER"),
            "current_shell": os.environ.get("SHELL"),
            "python_version": sys.version.split()[0],
        }


class CPUCollector:
    """Collect CPU topology and usage."""

    def __init__(self, runner: DiagnosticsCommandRunner) -> None:
        self.runner = runner

    def collect(self) -> dict[str, Any]:
        """Return CPU information."""
        lscpu = self.runner.run(["lscpu"])
        parsed = _parse_kv_lines(lscpu.stdout)
        return {
            "model": parsed.get("Model name"),
            "logical_cores": os.cpu_count(),
            "physical_cores": _number(parsed.get("Core(s) per socket", "")),
            "frequency": parsed.get("CPU max MHz") or parsed.get("CPU MHz"),
            "usage": self._usage(),
            "load_average": os.getloadavg() if hasattr(os, "getloadavg") else None,
            "temperature": TemperatureCollector().collect().get("cpu"),
        }

    def _usage(self) -> dict[str, int] | None:
        first = self._cpu_times()
        if not first:
            return None
        second = self._cpu_times()
        if not second:
            return None
        idle = second["idle"] - first["idle"]
        total = second["total"] - first["total"]
        used = max(total - idle, 0)
        percent = round((used / total) * 100) if total else 0
        return {"percent": percent}

    def _cpu_times(self) -> dict[str, int] | None:
        line = (_read(Path("/proc/stat")) or "").splitlines()
        if not line:
            return None
        parts = line[0].split()[1:]
        values = [int(value) for value in parts if value.isdigit()]
        if len(values) < 4:
            return None
        idle = values[3] + (values[4] if len(values) > 4 else 0)
        return {"idle": idle, "total": sum(values)}


class MemoryCollector:
    """Collect RAM and swap usage."""

    def collect(self) -> dict[str, Any]:
        """Return memory information from /proc/meminfo."""
        values: dict[str, int] = {}
        for line in (_read(Path("/proc/meminfo")) or "").splitlines():
            key, _, rest = line.partition(":")
            amount = rest.strip().split(" ")[0]
            if amount.isdigit():
                values[key] = int(amount) * 1024
        return {
            "installed": values.get("MemTotal"),
            "used": values.get("MemTotal", 0) - values.get("MemAvailable", 0),
            "available": values.get("MemAvailable"),
            "cached": values.get("Cached"),
            "buffers": values.get("Buffers"),
            "swap": {
                "total": values.get("SwapTotal"),
                "free": values.get("SwapFree"),
                "used": values.get("SwapTotal", 0) - values.get("SwapFree", 0),
            },
            "huge_pages": {
                "total": values.get("HugePages_Total"),
                "free": values.get("HugePages_Free"),
            },
        }


class DiskCollector:
    """Collect mounted disks and storage traits."""

    def __init__(self, runner: DiagnosticsCommandRunner) -> None:
        self.runner = runner

    def collect(self) -> dict[str, Any]:
        """Return disk mount and block device data."""
        df = self.runner.run(["df", "-P", "-T"])
        lsblk = self.runner.run(["lsblk", "-J", "-o", "NAME,TYPE,FSTYPE,MOUNTPOINT,SIZE,ROTA,TRAN"])
        return {
            "mounts": self._parse_df(df.stdout),
            "block_devices": lsblk.stdout,
            "ssd_detected": '"rota":false' in lsblk.stdout.lower(),
            "nvme_detected": "nvme" in lsblk.stdout.lower(),
            "statistics_available": Path("/proc/diskstats").exists(),
        }

    def _parse_df(self, text: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for line in text.splitlines()[1:]:
            parts = line.split()
            if len(parts) < 7:
                continue
            rows.append(
                {
                    "filesystem": parts[0],
                    "type": parts[1],
                    "size": int(parts[2]) * 1024,
                    "used": int(parts[3]) * 1024,
                    "available": int(parts[4]) * 1024,
                    "usage_percent": parts[5],
                    "mountpoint": parts[6],
                }
            )
        return rows


class BatteryCollector:
    """Collect battery status from sysfs."""

    def collect(self) -> dict[str, Any]:
        """Return battery details when present."""
        batteries = []
        for path in Path("/sys/class/power_supply").glob("BAT*"):
            full = _number(_read(path / "energy_full") or _read(path / "charge_full") or "")
            design = _number(
                _read(path / "energy_full_design") or _read(path / "charge_full_design") or ""
            )
            batteries.append(
                {
                    "name": path.name,
                    "percentage": _number(_read(path / "capacity") or ""),
                    "charging": (_read(path / "status") or "").lower() == "charging",
                    "health": round((full / design) * 100, 1) if full and design else None,
                    "cycles": _number(_read(path / "cycle_count") or ""),
                    "remaining_time": None,
                }
            )
        return {"batteries": batteries, "available": bool(batteries)}


class GPUCollector:
    """Collect GPU adapter information."""

    def __init__(self, runner: DiagnosticsCommandRunner) -> None:
        self.runner = runner

    def collect(self) -> dict[str, Any]:
        """Return GPU information from lspci."""
        result = self.runner.run(["lspci"])
        devices = [
            line
            for line in result.stdout.splitlines()
            if any(term in line.lower() for term in ["vga", "3d controller", "display"])
        ]
        return {"devices": devices, "vendor": devices[0] if devices else None, "driver": None, "memory": None}


class HardwareCollector:
    """Collect USB and PCI hardware."""

    def __init__(self, runner: DiagnosticsCommandRunner, config: DiagnosticsConfiguration) -> None:
        self.runner = runner
        self.config = config

    def usb(self) -> dict[str, Any]:
        """Return connected USB devices."""
        result = self.runner.run(["lsusb"])
        devices = [line for line in result.stdout.splitlines() if self._allowed(line)]
        return {"devices": devices}

    def pci(self) -> dict[str, Any]:
        """Return PCI devices."""
        result = self.runner.run(["lspci"])
        devices = [line for line in result.stdout.splitlines() if self._allowed(line)]
        return {"devices": devices}

    def collect(self) -> dict[str, Any]:
        """Return combined hardware information."""
        return {"usb": self.usb(), "pci": self.pci(), "gpu": GPUCollector(self.runner).collect()}

    def _allowed(self, line: str) -> bool:
        return not any(ignored.lower() in line.lower() for ignored in self.config.ignored_devices)


class ProcessCollector:
    """Collect process information."""

    def __init__(self, runner: DiagnosticsCommandRunner, config: DiagnosticsConfiguration) -> None:
        self.runner = runner
        self.config = config

    def collect(self) -> dict[str, Any]:
        """Return top CPU/RAM and abnormal process states."""
        result = self.runner.run(["ps", "-eo", "pid,ppid,stat,pcpu,pmem,comm", "--sort=-pcpu"])
        rows = self._parse_ps(result.stdout)
        limit = self.config.max_processes
        return {
            "running_processes": len(rows),
            "top_cpu": rows[:limit],
            "top_ram": sorted(rows, key=lambda row: row["memory_percent"], reverse=True)[:limit],
            "zombie_processes": [row for row in rows if "Z" in row["state"]],
            "orphan_processes": [row for row in rows if row["ppid"] == 1][:limit],
        }

    def _parse_ps(self, text: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for line in text.splitlines()[1:]:
            parts = line.split(None, 5)
            if len(parts) != 6:
                continue
            rows.append(
                {
                    "pid": int(parts[0]),
                    "ppid": int(parts[1]),
                    "state": parts[2],
                    "cpu_percent": float(parts[3]),
                    "memory_percent": float(parts[4]),
                    "command": parts[5],
                }
            )
        return rows


class ServiceCollector:
    """Read systemd service state."""

    def __init__(self, runner: DiagnosticsCommandRunner, config: DiagnosticsConfiguration) -> None:
        self.runner = runner
        self.config = config

    def collect(self) -> dict[str, Any]:
        """Return active and failed service names."""
        active = self.runner.run(["systemctl", "list-units", "--type=service", "--state=active", "--no-pager", "--plain"])
        failed = self.runner.run(["systemctl", "list-units", "--type=service", "--state=failed", "--no-pager", "--plain"])
        return {"active": self._parse_units(active.stdout), "failed": self._parse_units(failed.stdout)}

    def status(self, service: str) -> dict[str, Any]:
        """Return read-only systemctl status output."""
        result = self.runner.run(["systemctl", "status", service, "--no-pager"])
        return {"service": service, "status": result.stdout, "error": result.stderr if not result.ok else None}

    def _parse_units(self, text: str) -> list[str]:
        services = []
        for line in text.splitlines():
            if not line.endswith(".service") and ".service " not in line:
                continue
            service = line.split()[0]
            if service not in self.config.ignored_services:
                services.append(service)
        return services


class JournalReader:
    """Read recent systemd journal lines."""

    def __init__(self, runner: DiagnosticsCommandRunner, config: DiagnosticsConfiguration) -> None:
        self.runner = runner
        self.config = config

    def read(self, errors_only: bool = False, search: str | None = None) -> dict[str, Any]:
        """Return recent journal lines with optional error priority and search."""
        command = ["journalctl", "-b", "--no-pager", "-n", str(self.config.journal_lines)]
        if errors_only:
            command.extend(["-p", "err"])
        result = self.runner.run(command)
        lines = result.stdout.splitlines()
        if search:
            lines = [line for line in lines if search.lower() in line.lower()]
        return {"lines": lines, "count": len(lines), "error": result.stderr if not result.ok else None}


class KernelCollector:
    """Collect kernel version, modules, and boot time."""

    def collect(self) -> dict[str, Any]:
        """Return kernel information."""
        modules = []
        for line in (_read(Path("/proc/modules")) or "").splitlines():
            parts = line.split()
            if parts:
                modules.append(parts[0])
        stat = _read(Path("/proc/stat")) or ""
        boot_time = next((line.split()[1] for line in stat.splitlines() if line.startswith("btime ")), None)
        return {"version": platform.release(), "modules": modules[:100], "boot_time": boot_time}


class TemperatureCollector:
    """Collect hardware temperatures from hwmon."""

    def collect(self) -> dict[str, Any]:
        """Return available temperatures in Celsius."""
        sensors: dict[str, float] = {}
        for path in Path("/sys/class/hwmon").glob("hwmon*/temp*_input"):
            value = _number(_read(path) or "")
            if value is None:
                continue
            label = _read(path.with_name(path.name.replace("_input", "_label"))) or path.parent.name
            sensors[label] = round(float(value) / 1000, 1)
        cpu = next(iter(sensors.values()), None)
        return {"sensors": sensors, "cpu": cpu}


class NetworkInfoCollector:
    """Collect read-only network identity and interface state."""

    def __init__(self, runner: DiagnosticsCommandRunner) -> None:
        self.runner = runner

    def collect(self) -> dict[str, Any]:
        """Return network information without changing configuration."""
        addresses = self.runner.run(["ip", "-o", "addr", "show"])
        routes = self.runner.run(["ip", "route", "show", "default"])
        dns = _read(Path("/etc/resolv.conf")) or ""
        return {
            "hostname": socket.gethostname(),
            "interfaces": self._parse_addr(addresses.stdout),
            "gateway": routes.stdout.strip(),
            "dns": [line.split()[-1] for line in dns.splitlines() if line.startswith("nameserver ")],
        }

    def _parse_addr(self, text: str) -> list[dict[str, Any]]:
        interfaces: dict[str, dict[str, Any]] = {}
        for line in text.splitlines():
            parts = line.split()
            if len(parts) < 4:
                continue
            name = parts[1]
            item = interfaces.setdefault(name, {"name": name, "ip_addresses": [], "mac_address": None})
            if parts[2] in {"inet", "inet6"}:
                item["ip_addresses"].append(parts[3])
        for name, item in interfaces.items():
            item["mac_address"] = _read(Path("/sys/class/net") / name / "address")
        return list(interfaces.values())
