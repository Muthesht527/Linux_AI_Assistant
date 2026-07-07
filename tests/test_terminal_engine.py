"""Tests for the secure terminal engine."""

from __future__ import annotations

import pytest

from assistant.core.tool_engine import ToolEngine
from assistant.terminal import TerminalConfiguration, TerminalManager
from assistant.tools.terminal_tool import TerminalTool


def test_terminal_manager_executes_allowed_command(tmp_path) -> None:
    """Verify allowed commands execute with captured output."""
    manager = TerminalManager(TerminalConfiguration(default_working_directory=tmp_path))

    result = manager.run("pwd")

    assert result.success is True
    assert result.return_code == 0
    assert result.stdout.strip() == str(tmp_path)


def test_terminal_manager_blocks_dangerous_command(tmp_path) -> None:
    """Verify blocked commands never reach subprocess execution."""
    manager = TerminalManager(TerminalConfiguration(default_working_directory=tmp_path))

    with pytest.raises(ValueError, match="blocked"):
        manager.run("rm -rf .")


def test_terminal_manager_rejects_shell_operators(tmp_path) -> None:
    """Verify shell operators are rejected even with allowed commands."""
    manager = TerminalManager(TerminalConfiguration(default_working_directory=tmp_path))

    with pytest.raises(ValueError, match="Shell operator"):
        manager.run("echo hello ; whoami")


def test_terminal_tool_returns_structured_error_for_blocked_command() -> None:
    """Verify the Tool Engine adapter returns friendly rejection errors."""
    tool = TerminalTool()

    result = tool.execute(command="sudo whoami")

    assert result.success is False
    assert "blocked" in str(result.error)


def test_tool_engine_dispatches_terminal_tool() -> None:
    """Verify terminal execution works through the Tool Engine."""
    engine = ToolEngine([TerminalTool()])

    result = engine.execute("terminal", {"command": "echo hello"})

    assert result.success is True
    assert result.data["stdout"].strip() == "hello"
