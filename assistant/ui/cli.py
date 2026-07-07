"""Typer CLI entry point for Linux AI Assistant."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from assistant.config.config_loader import ConfigLoader
from assistant.core.bootstrap import build_startup_context, startup_banner
from assistant.core.constants import APP_VERSION
from assistant.core.exceptions import AssistantError
from assistant.utils.dependencies import check_dependencies
from assistant.utils.environment import detect_environment

app = typer.Typer(
    add_completion=False,
    help="Foundation CLI for the local Linux AI Assistant.",
    no_args_is_help=False,
)
console = Console()


def _version_callback(value: bool) -> None:
    """Print version information and exit."""
    if value:
        console.print(f"Linux AI Assistant {APP_VERSION}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show the application version.",
    ),
) -> None:
    """Run startup checks when no subcommand is provided."""
    del version
    if ctx.invoked_subcommand is not None:
        return
    try:
        context = build_startup_context()
    except AssistantError as exc:
        console.print(f"[red]Startup failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        console.print("[red]Startup failed:[/red] Unexpected error. See logs for details.")
        raise typer.Exit(code=1) from exc
    console.print(startup_banner(context))


@app.command()
def config(
    path: Path | None = typer.Option(
        None,
        "--path",
        "-p",
        help="Optional configuration file to inspect.",
    ),
) -> None:
    """Show the active configuration."""
    try:
        loader = ConfigLoader(path)
        settings = loader.load_settings()
    except AssistantError as exc:
        console.print(f"[red]Configuration error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(f"Config file: {loader.config_path}")
    console.print(f"Application: {settings.application.name}")
    console.print(f"Version: {settings.application.version}")
    console.print(f"Log level: {settings.logging.level}")


@app.command()
def doctor() -> None:
    """Validate the local environment and dependencies."""
    try:
        settings = ConfigLoader().load_settings()
        context = build_startup_context()
    except AssistantError as exc:
        console.print(f"[red]Doctor failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    dependency_result = check_dependencies(settings.dependencies.packages)
    console.print("[green]Environment OK[/green]")
    console.print(f"Python: {context.environment.python_version}")
    console.print(f"System: {context.environment.distribution}")
    console.print(f"Dependencies: {'OK' if dependency_result.ok else 'Missing'}")


@app.command()
def info() -> None:
    """Show application and environment information."""
    environment = detect_environment()
    settings = ConfigLoader().load_settings()
    console.print(f"Application: {settings.application.name}")
    console.print(f"Version: {settings.application.version}")
    console.print(f"Python: {environment.python_version}")
    console.print(f"Executable: {environment.executable}")
    console.print(f"System: {environment.distribution}")


def run_cli(args: list[str] | None = None) -> None:
    """Run the Typer application."""
    app(args=args, prog_name="linux-ai-assistant")


if __name__ == "__main__":
    run_cli()
