"""Tests for natural-language tool orchestration."""

from __future__ import annotations

from typing import Any

from assistant.config.settings import ConversationSettings
from assistant.core.base_tool import BaseTool, ToolResult
from assistant.core.conversation_manager import ConversationManager
from assistant.core.orchestrator import ConversationOrchestrator, ToolDecisionEngine
from assistant.core.production import get_runtime
from assistant.core.tool_engine import ToolEngine
from assistant.models.ollama_model import OllamaModelInfo


class CountingTool(BaseTool):
    """Test tool that records execution count."""

    name = "system_info"
    description = "Test system info"
    category = "diagnostics"
    permission_level = "SAFE"
    calls = 0

    def execute(self, **kwargs: Any) -> ToolResult:
        del kwargs
        type(self).calls += 1
        return self.result(
            success=True,
            message="System info loaded",
            data={"distribution": "Ubuntu 24.04", "desktop_environment": "KDE"},
        )


class FailingTool(BaseTool):
    """Test tool that returns a structured failure."""

    name = "memory_info"
    description = "Test memory info"
    category = "diagnostics"
    permission_level = "SAFE"

    def execute(self, **kwargs: Any) -> ToolResult:
        del kwargs
        return self.result(
            success=False,
            message="Memory failed",
            data={"error": "unavailable"},
            error="unavailable",
        )


class FakeSearchTool(BaseTool):
    """Test search tool."""

    name = "search_file"
    description = "Search files"
    category = "filesystem"
    permission_level = "SAFE"

    def execute(self, **kwargs: Any) -> ToolResult:
        return self.result(
            success=True,
            message="Search completed",
            data={"results": [{"path": kwargs.get("partial", "README.md")}], "total": 1},
        )


class FakeReadTool(BaseTool):
    """Test read tool."""

    name = "read_file"
    description = "Read files"
    category = "filesystem"
    permission_level = "SAFE"

    def execute(self, **kwargs: Any) -> ToolResult:
        return self.result(
            success=True,
            message="Read completed",
            data={"path": kwargs["path"], "content": "# Demo"},
        )


class FakeOllama:
    """Fake LLM client for orchestration tests."""

    def __init__(self) -> None:
        self.model = "qwen3"
        self.last_messages: list[dict[str, str]] = []

    def is_installed(self) -> bool:
        return True

    def is_running(self) -> bool:
        return True

    def list_models(self) -> list[OllamaModelInfo]:
        return [OllamaModelInfo(name="qwen3:latest")]

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float,
        top_p: float,
        context_size: int,
    ) -> dict[str, str]:
        del temperature, top_p, context_size
        self.last_messages = messages
        return {"response": f"answered with {messages[-1]['content'][:40]}"}


def _engine(*tools: BaseTool) -> ToolEngine:
    engine = ToolEngine()
    for tool in tools:
        engine.register(tool)
    return engine


def test_tool_decision_engine_selects_system_info() -> None:
    """Verify OS questions route to system info."""
    decision = ToolDecisionEngine().decide("What OS am I using?")

    assert decision.requires_tools
    assert decision.plans[0].tool_name == "system_info"


def test_tool_decision_engine_supports_chained_readme_plan() -> None:
    """Verify README find-and-summarize requests plan multiple tools."""
    decision = ToolDecisionEngine().decide("Find README.md and summarize it.")

    assert [plan.tool_name for plan in decision.plans] == ["search_file", "read_file"]


def test_tool_decision_engine_routes_common_local_requests() -> None:
    """Verify common Phase 9 examples route to existing tools."""
    engine = ToolDecisionEngine()

    cases = {
        "Read README.md": "read_file",
        "What branch am I on?": "git_status",
        "Show battery health.": "battery_info",
        "What USB devices are connected?": "usb_info",
        "Explain this traceback: ValueError": "stack_trace",
    }

    for prompt, tool_name in cases.items():
        decision = engine.decide(prompt)
        assert tool_name in [plan.tool_name for plan in decision.plans]


def test_orchestrator_reuses_cached_tool_results() -> None:
    """Verify repeated identical tool calls use cache."""
    get_runtime().cache.invalidate()
    CountingTool.calls = 0
    orchestrator = ConversationOrchestrator(_engine(CountingTool()))

    first = orchestrator.run("What operating system am I using?")
    second = orchestrator.run("What operating system am I using?")

    assert first is not None
    assert second is not None
    assert CountingTool.calls == 1
    assert second.used_cache


def test_orchestrator_handles_tool_failure() -> None:
    """Verify failed tools are returned for safe fallback explanation."""
    get_runtime().cache.invalidate()
    orchestrator = ConversationOrchestrator(_engine(FailingTool()))

    result = orchestrator.run("Why is RAM usage high?")

    assert result is not None
    assert result.tool_results[0].success is False
    assert "failed" in orchestrator.formatter.fallback("Why is RAM usage high?", result.tool_results)


def test_conversation_manager_uses_tools_before_final_answer() -> None:
    """Verify chat sends local tool results to the LLM for final wording."""
    get_runtime().cache.invalidate()
    client = FakeOllama()
    manager = ConversationManager(
        ConversationSettings(streaming_enabled=False),
        model=client,
        orchestrator=ConversationOrchestrator(_engine(CountingTool())),
    )

    result = manager.respond("What OS am I using?")

    assert result.error is None
    assert "Tool results" in client.last_messages[-1]["content"]
    assert "system_info" in client.last_messages[-1]["content"]
    assert manager.session.history.messages[-1].content == result.response


def test_orchestrator_multi_tool_execution() -> None:
    """Verify multiple planned tools execute successfully."""
    get_runtime().cache.invalidate()
    orchestrator = ConversationOrchestrator(_engine(FakeSearchTool(), FakeReadTool()))

    result = orchestrator.run("Find README.md and summarize it.")

    assert result is not None
    assert [item.tool_name for item in result.tool_results] == ["search_file", "read_file"]
    assert all(item.success for item in result.tool_results)
