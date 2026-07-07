"""Foundation tests for configuration, logging, startup, and CLI."""

from __future__ import annotations

import logging

from typer.testing import CliRunner

from assistant.config.config_loader import ConfigLoader
from assistant.config.settings import Settings
from assistant.core.bootstrap import build_startup_context
from assistant.ui.cli import app
from assistant.utils.logging_config import configure_logging


def test_typed_configuration_loads() -> None:
    """Verify YAML configuration is validated into typed settings."""
    settings = ConfigLoader().load_settings()

    assert settings.application.name == "Linux AI Assistant"
    assert settings.logging.level == "INFO"


def test_logger_writes_rotating_file(tmp_path) -> None:
    """Verify logging creates the configured log file."""
    configure_logging(log_dir=tmp_path, console=False)
    logging.getLogger(__name__).info("foundation logger test")

    assert (tmp_path / "assistant.log").exists()


def test_startup_context_initializes_directories() -> None:
    """Verify startup creates foundation directories."""
    context = build_startup_context()

    assert context.settings.application.name == "Linux AI Assistant"
    assert all(path.exists() for path in context.created_directories)


def test_cli_info_command_succeeds() -> None:
    """Verify the CLI exposes the info command."""
    result = CliRunner().invoke(app, ["info"])

    assert result.exit_code == 0
    assert "Linux AI Assistant" in result.output


def test_cli_phase_eight_commands_succeed() -> None:
    """Verify production release commands are available."""
    runner = CliRunner()

    for command in ("version", "plugins", "memory", "memory-info", "stats", "release"):
        result = runner.invoke(app, [command])
        assert result.exit_code == 0


def test_cli_memory_list_uses_assistant_memory() -> None:
    """Verify assistant memory is not shadowed by diagnostics memory."""
    result = CliRunner().invoke(app, ["memory", "list"])

    assert result.exit_code == 0
    assert "Session Memory" in result.output
    assert "Persistent Memory" in result.output


def test_cli_plugin_management_commands_succeed() -> None:
    """Verify plugin management commands are exposed."""
    runner = CliRunner()

    for args in (
        ["plugins", "validate"],
        ["plugins", "info", "example"],
        ["plugins", "disable", "example"],
        ["plugins", "enable", "example"],
    ):
        result = runner.invoke(app, args)
        assert result.exit_code == 0


def test_settings_default_version_is_release_version() -> None:
    """Verify typed defaults match release metadata."""
    assert Settings().application.version == "1.0.0"
    assert ConfigLoader().load_settings().application.version == "1.0.0"
