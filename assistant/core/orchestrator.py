"""Natural-language orchestration for Tool Engine backed chat."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from assistant.core.base_tool import ToolContext, ToolResult
from assistant.core.production import get_runtime
from assistant.core.tool_engine import ToolEngine


@dataclass(frozen=True, slots=True)
class ToolCallPlan:
    """One planned tool invocation."""

    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    reason: str = ""


@dataclass(frozen=True, slots=True)
class ToolDecision:
    """Decision produced for a user prompt."""

    requires_tools: bool
    plans: list[ToolCallPlan] = field(default_factory=list)
    reason: str = "reasoning only"


@dataclass(frozen=True, slots=True)
class OrchestrationResult:
    """Tool orchestration output for a user prompt."""

    decision: ToolDecision
    tool_results: list[ToolResult]
    final_prompt: str
    used_cache: bool = False


class ToolDecisionEngine:
    """Route natural-language requests to existing tools."""

    def decide(self, prompt: str) -> ToolDecision:
        """Return the tool plan for a user prompt."""
        text = prompt.lower().strip()
        plans: list[ToolCallPlan] = []

        if self._mentions(text, ("operating system", " os ", "distro", "distribution", "system am i")):
            plans.append(ToolCallPlan("system_info", reason="User asked for local OS/system information."))
        if self._mentions(text, ("ram", "memory usage", "memory high", "high memory")):
            plans.append(ToolCallPlan("memory_info", reason="User asked about local memory/RAM."))
        if self._mentions(text, ("cpu", "processor", "load average")):
            plans.append(ToolCallPlan("cpu_info", reason="User asked about local CPU."))
        if self._mentions(text, ("battery", "charge", "battery health")):
            plans.append(ToolCallPlan("battery_info", reason="User asked about battery health."))
        if self._mentions(text, ("gpu", "graphics")):
            plans.append(ToolCallPlan("gpu_info", reason="User asked about GPU information."))
        if self._mentions(text, ("disk", "storage", "space")):
            plans.append(ToolCallPlan("disk_info", reason="User asked about disks or storage."))
        if self._mentions(text, ("process", "running processes")):
            plans.append(ToolCallPlan("process_info", reason="User asked about processes."))
        if self._mentions(text, ("kernel",)):
            plans.append(ToolCallPlan("kernel_info", reason="User asked about the kernel."))
        if self._mentions(text, ("service", "systemd")):
            plans.append(ToolCallPlan("service_info", reason="User asked about services."))
        if self._mentions(text, ("usb",)):
            plans.append(ToolCallPlan("usb_info", reason="User asked about USB devices."))
        if self._mentions(text, ("network", "ip address", "dns", "gateway")):
            plans.append(ToolCallPlan("network_info", reason="User asked about networking."))

        path = self._extract_path(prompt)
        if self._mentions(text, ("read ", "open ", "show file", "cat ")) and path:
            plans.append(ToolCallPlan("read_file", {"path": path}, "User asked to read a local file."))
        elif self._mentions(text, ("find ", "locate ", "search ")) and path:
            plans.append(ToolCallPlan("search_file", {"partial": Path(path).name, "limit": 10}, "User asked to find a local file."))

        if self._mentions(text, ("readme",)) and self._mentions(text, ("summarize", "summary", "find")):
            plans.append(ToolCallPlan("search_file", {"partial": "README.md", "limit": 10}, "User asked to find README documentation."))
            plans.append(ToolCallPlan("read_file", {"path": "README.md"}, "User asked to read or summarize README documentation."))
        elif self._mentions(text, ("readme",)):
            plans.append(ToolCallPlan("readme_reader", {"path": "."}, "User asked about README documentation."))

        if self._mentions(text, ("project", "repository", "repo")) and self._mentions(text, ("summarize", "summary", "read")):
            plans.append(ToolCallPlan("project_summary", {"path": "."}, "User asked for project understanding."))
        if self._mentions(text, ("traceback", "stack trace", "error")):
            plans.append(ToolCallPlan("stack_trace", {"text": prompt}, "User asked to explain an error or traceback."))

        if self._mentions(text, ("branch", "git status", "changed files", "untracked")):
            plans.append(ToolCallPlan("git_status", {"path": "."}, "User asked about Git status or branch."))
        if self._mentions(text, ("git history", "commits", "recent commit")):
            plans.append(ToolCallPlan("git_history", {"path": "."}, "User asked about Git history."))
        if self._mentions(text, ("git diff", "diff")):
            plans.append(ToolCallPlan("git_diff", {"path": "."}, "User asked about Git diff."))

        plans = self._deduplicate(plans)
        if not plans:
            return ToolDecision(False)
        return ToolDecision(True, plans, "local information requires tools")

    def _extract_path(self, prompt: str) -> str | None:
        quoted = re.search(r"['\"]([^'\"]+)['\"]", prompt)
        if quoted:
            return quoted.group(1)
        match = re.search(r"([\w./-]+\.[A-Za-z0-9]+)", prompt)
        if match:
            return match.group(1)
        return None

    def _deduplicate(self, plans: list[ToolCallPlan]) -> list[ToolCallPlan]:
        seen: set[tuple[str, tuple[tuple[str, Any], ...]]] = set()
        unique: list[ToolCallPlan] = []
        for plan in plans:
            key = (plan.tool_name, tuple(sorted(plan.arguments.items())))
            if key in seen:
                continue
            seen.add(key)
            unique.append(plan)
        return unique

    def _mentions(self, text: str, terms: tuple[str, ...]) -> bool:
        padded = f" {text} "
        return any(term in padded for term in terms)


class ToolResponseFormatter:
    """Build final LLM prompts and fallback answers from tool results."""

    def final_prompt(self, user_input: str, results: list[ToolResult]) -> str:
        """Return a prompt asking the LLM to explain tool results."""
        payload = [result.to_dict() for result in results]
        return (
            "Use these local tool results to answer the user naturally. "
            "Do not invent local facts. If a tool failed, explain the failure and offer alternatives.\n\n"
            f"User request: {user_input}\n\nTool results:\n{payload}"
        )

    def fallback(self, user_input: str, results: list[ToolResult]) -> str:
        """Return a deterministic fallback when the LLM cannot answer."""
        failures = [result for result in results if not result.success]
        if failures:
            details = "; ".join(f"{item.tool_name}: {item.error or item.message}" for item in failures)
            return f"I tried to answer using local tools, but the tool call failed: {details}."
        summaries = "; ".join(f"{result.tool_name}: {result.data}" for result in results)
        return f"Local tool results for '{user_input}': {summaries}"


class ToolExecutionPipeline:
    """Execute planned tool calls with cache and session reuse."""

    def __init__(self, engine: ToolEngine) -> None:
        self.engine = engine
        self.logger = logging.getLogger(__name__)

    def execute(self, plans: list[ToolCallPlan]) -> tuple[list[ToolResult], bool]:
        """Execute tool plans and return results plus whether cache was used."""
        runtime = get_runtime()
        results: list[ToolResult] = []
        used_cache = False
        for plan in plans:
            cache_key = f"orchestrator:{plan.tool_name}:{sorted(plan.arguments.items())}"
            cached = runtime.cache.get(cache_key)
            if isinstance(cached, ToolResult):
                results.append(cached)
                used_cache = True
                continue
            result = self.engine.execute(plan.tool_name, plan.arguments, ToolContext())
            runtime.cache.set(cache_key, result)
            results.append(result)
            self.logger.info(
                "tool_orchestration tool=%s reason=%s success=%s elapsed=%.6f",
                plan.tool_name,
                plan.reason,
                result.success,
                result.execution_time,
            )
        return results, used_cache


class ConversationOrchestrator:
    """Coordinate tool decisions, execution, and final answer prompts."""

    def __init__(
        self,
        engine: ToolEngine,
        decision_engine: ToolDecisionEngine | None = None,
        formatter: ToolResponseFormatter | None = None,
    ) -> None:
        self.decision_engine = decision_engine or ToolDecisionEngine()
        self.pipeline = ToolExecutionPipeline(engine)
        self.formatter = formatter or ToolResponseFormatter()

    def run(self, user_input: str) -> OrchestrationResult | None:
        """Run orchestration for a prompt, returning None for reasoning-only prompts."""
        decision = self.decision_engine.decide(user_input)
        if not decision.requires_tools:
            return None
        results, used_cache = self.pipeline.execute(decision.plans)
        return OrchestrationResult(
            decision=decision,
            tool_results=results,
            final_prompt=self.formatter.final_prompt(user_input, results),
            used_cache=used_cache,
        )
