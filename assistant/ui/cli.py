"""Minimal CLI entry point for the local assistant."""

from __future__ import annotations

from assistant.core.assistant_controller import AssistantController
from assistant.plugins.plugin_manager import PluginManager
from assistant.tools.echo_tool import EchoTool


def run_cli() -> None:
    """Start an interactive prompt for the assistant."""
    tools = [EchoTool()]
    tools.extend(PluginManager().discover())
    controller = AssistantController(tools)

    print("Linux AI Assistant ready. Type 'quit' to exit.")
    while True:
        user_input = input("> ").strip()
        if user_input.lower() in {"quit", "exit"}:
            break
        print(controller.handle(user_input)["response"])


if __name__ == "__main__":
    run_cli()
