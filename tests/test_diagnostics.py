from assistant.core.tool_engine import ToolEngine
from assistant.diagnostics.collectors import DiskCollector, ProcessCollector
from assistant.diagnostics.command import CommandResult, DiagnosticsCommandRunner
from assistant.diagnostics.config import DiagnosticsConfiguration
from assistant.diagnostics.manager import DiagnosticsManager
from assistant.tools.diagnostics_tool import SystemInfoTool


class FakeRunner:
    def __init__(self, outputs: dict[str, str]) -> None:
        self.outputs = outputs

    def run(self, command: list[str], timeout: int | None = None) -> CommandResult:
        del timeout
        key = " ".join(command)
        return CommandResult(command, self.outputs.get(key, ""), "", 0, 0.0)


def test_disk_collector_parses_df_output() -> None:
    runner = FakeRunner(
        {
            "df -P -T": (
                "Filesystem Type 1024-blocks Used Available Capacity Mounted on\n"
                "/dev/sda1 ext4 100 95 5 95% /\n"
            ),
            "lsblk -J -o NAME,TYPE,FSTYPE,MOUNTPOINT,SIZE,ROTA,TRAN": '{"rota":false,"tran":"nvme"}',
        }
    )

    data = DiskCollector(runner).collect()

    assert data["mounts"][0]["mountpoint"] == "/"
    assert data["mounts"][0]["usage_percent"] == "95%"
    assert data["ssd_detected"] is True
    assert data["nvme_detected"] is True


def test_process_collector_reports_zombies_and_orphans() -> None:
    runner = FakeRunner(
        {
            "ps -eo pid,ppid,stat,pcpu,pmem,comm --sort=-pcpu": (
                "PID PPID STAT %CPU %MEM COMMAND\n"
                "10 1 Z 20.0 1.0 dead\n"
                "11 10 S 1.0 30.0 worker\n"
            )
        }
    )

    data = ProcessCollector(runner, DiagnosticsConfiguration(max_processes=5)).collect()

    assert data["running_processes"] == 2
    assert data["zombie_processes"][0]["command"] == "dead"
    assert data["orphan_processes"][0]["pid"] == 10
    assert data["top_ram"][0]["command"] == "worker"


def test_diagnostics_summary_flags_common_issues() -> None:
    manager = DiagnosticsManager()

    findings = manager.summarize(
        {
            "memory": {"installed": 100, "used": 90},
            "disk": {"mounts": [{"mountpoint": "/", "usage_percent": "91%"}]},
            "battery": {"batteries": [{"health": 60}]},
            "cpu": {"temperature": 90},
            "services": {"failed": ["a.service", "b.service"]},
        }
    )

    assert "High memory usage detected." in findings
    assert "Disk nearly full: /." in findings
    assert "Battery health is poor: 60%." in findings
    assert "CPU temperature is high: 90 C." in findings
    assert "Failed services detected: a.service, b.service." in findings


def test_command_runner_rejects_unapproved_commands() -> None:
    runner = DiagnosticsCommandRunner(DiagnosticsConfiguration())

    result = runner.run(["rm", "-rf", "/tmp/example"])

    assert result.ok is False
    assert result.returncode == 126
    assert "not allowed" in result.stderr


def test_system_info_tool_integrates_with_tool_engine() -> None:
    engine = ToolEngine([SystemInfoTool()])

    result = engine.execute("system_info")

    assert result.success is True
    assert result.data["data"]["hostname"]
