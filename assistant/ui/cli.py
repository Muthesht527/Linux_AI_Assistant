"""Typer CLI entry point for Linux AI Assistant."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from assistant.config.config_loader import ConfigLoader
from assistant.core.bootstrap import build_startup_context, startup_banner
from assistant.core.conversation_manager import ConversationManager
from assistant.core.constants import APP_VERSION
from assistant.core.exceptions import AssistantError
from assistant.filesystem import FilesystemConfiguration, FilesystemManager
from assistant.utils.dependencies import check_dependencies
from assistant.utils.environment import detect_environment

app = typer.Typer(
    add_completion=False,
    help="Foundation CLI for the local Linux AI Assistant.",
    no_args_is_help=False,
)
console = Console()


def _build_conversation_manager() -> ConversationManager:
    """Create a configured local conversation manager."""
    settings = ConfigLoader().load_settings()
    return ConversationManager(settings.conversation)


def _build_filesystem_manager() -> FilesystemManager:
    """Create a configured filesystem manager."""
    settings = ConfigLoader().load_settings()
    configuration = FilesystemConfiguration(**settings.filesystem.model_dump())
    return FilesystemManager(configuration)


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


@app.command()
def models(
    command: str = typer.Argument(
        "list",
        help="Model command: list, current, or switch.",
    ),
    model_name: str | None = typer.Argument(
        None,
        help="Model name for 'switch'.",
    ),
) -> None:
    """Inspect or select local Ollama models."""
    manager = _build_conversation_manager()
    status = manager.status()
    if not status["ok"]:
        console.print(f"[yellow]{status['message']}[/yellow]")
        raise typer.Exit(code=1)

    if command in {"list", "/models", "/model", "/model list"}:
        _print_models(manager)
        return
    if command in {"current", "/model current"}:
        console.print(f"Current model: [green]{manager.models.current_model}[/green]")
        return
    if command in {"switch", "/model switch"}:
        if not model_name:
            console.print("[red]Provide a model name to switch to.[/red]")
            raise typer.Exit(code=1)
        try:
            selected = manager.switch_model(model_name)
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1) from exc
        console.print(f"Current model: [green]{selected}[/green]")
        return

    console.print("[red]Unknown model command. Use list, current, or switch.[/red]")
    raise typer.Exit(code=1)


@app.command()
def chat(prompt: list[str] | None = typer.Argument(None)) -> None:
    """Chat with a local Ollama model."""
    manager = _build_conversation_manager()
    status = manager.status()
    if not status["ok"]:
        console.print(f"[yellow]{status['message']}[/yellow]")
        raise typer.Exit(code=1)

    if prompt:
        user_input = " ".join(prompt).strip()
        _print_response(manager, user_input)
        return

    console.print("[bold]Local chat ready.[/bold] Type /exit to leave.")
    while True:
        try:
            user_input = _read_chat_input()
        except (EOFError, KeyboardInterrupt):
            console.print("\nGoodbye.")
            return

        if not user_input:
            continue
        if _handle_chat_command(manager, user_input):
            continue
        _print_response(manager, user_input)


@app.command()
def files(
    path: Path = typer.Argument(Path("."), help="Directory path to list."),
    limit: int = typer.Option(50, "--limit", "-n", help="Maximum entries to show."),
) -> None:
    """List local files in a directory."""
    manager = _build_filesystem_manager()
    try:
        data = manager.list_directory(path, limit)
    except OSError as exc:
        console.print(f"[red]File listing failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    _print_directory_listing(data)


@app.command()
def search(
    query: str = typer.Argument(..., help="Partial filename or content query."),
    extension: str | None = typer.Option(None, "--ext", help="File extension."),
    content: bool = typer.Option(False, "--content", help="Search inside text files."),
    regex: bool = typer.Option(False, "--regex", help="Treat query as regex."),
    limit: int = typer.Option(50, "--limit", "-n", help="Maximum results."),
) -> None:
    """Search indexed files."""
    manager = _build_filesystem_manager()
    if content:
        data = manager.search_content(query, regex=regex, limit=limit)
    else:
        data = manager.search(partial=query, extension=extension, regex=query if regex else None, limit=limit)
    _print_search_results(data)


@app.command()
def read(
    path: Path = typer.Argument(..., help="File path to read."),
    preview_rows: int = typer.Option(20, "--preview-rows", help="CSV preview rows."),
) -> None:
    """Read a supported local file."""
    manager = _build_filesystem_manager()
    try:
        data = manager.read(path, preview_rows)
    except (OSError, ValueError) as exc:
        console.print(f"[red]Read failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    _print_read_result(data)


@app.command()
def index(
    command: str = typer.Argument("status", help="Index command: status or rebuild."),
    yes: bool = typer.Option(False, "--yes", help="Confirm index rebuild."),
) -> None:
    """Inspect or rebuild the filesystem index."""
    manager = _build_filesystem_manager()
    if command in {"status", "/index status"}:
        _print_index_status(manager.index_status())
        return
    if command in {"rebuild", "/index rebuild"}:
        if not yes and not typer.confirm("Rebuild the filesystem index?"):
            raise typer.Exit(code=1)
        data = manager.rebuild_index()
        console.print(f"[green]Indexed {data['indexed']} files.[/green]")
        if data.get("errors"):
            console.print(f"[yellow]Errors: {len(data['errors'])}[/yellow]")
        return
    console.print("[red]Unknown index command. Use status or rebuild.[/red]")
    raise typer.Exit(code=1)


def _handle_chat_command(manager: ConversationManager, user_input: str) -> bool:
    """Handle slash commands inside the chat loop."""
    if user_input in {"/exit", "exit", "quit"}:
        raise typer.Exit()
    if user_input in {"/reset", "/clear", "clear history"}:
        manager.reset()
        console.print("[green]Conversation history cleared.[/green]")
        return True
    if user_input in {"/models", "/model", "/model list"}:
        _print_models(manager)
        return True
    if user_input == "/model current":
        console.print(f"Current model: [green]{manager.models.current_model}[/green]")
        return True
    if user_input.startswith("/model switch "):
        model_name = user_input.removeprefix("/model switch ").strip()
        try:
            selected = manager.switch_model(model_name)
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
            return True
        console.print(f"Current model: [green]{selected}[/green]")
        return True
    if user_input.startswith("/files"):
        path = user_input.removeprefix("/files").strip() or "."
        _print_directory_listing(_build_filesystem_manager().list_directory(path, 50))
        return True
    if user_input.startswith("/search "):
        query = user_input.removeprefix("/search ").strip()
        _print_search_results(_build_filesystem_manager().search(partial=query, limit=50))
        return True
    if user_input.startswith("/read "):
        path = user_input.removeprefix("/read ").strip()
        _print_read_result(_build_filesystem_manager().read(path))
        return True
    if user_input == "/index status":
        _print_index_status(_build_filesystem_manager().index_status())
        return True
    if user_input == "/index rebuild":
        data = _build_filesystem_manager().rebuild_index()
        console.print(f"[green]Indexed {data['indexed']} files.[/green]")
        return True
    return False


def _read_chat_input() -> str:
    """Read a single-line or continuation-based multi-line prompt."""
    lines: list[str] = []
    prompt = "[cyan]you>[/cyan] "
    while True:
        line = console.input(prompt)
        if line.endswith("\\"):
            lines.append(line[:-1])
            prompt = "[cyan]...[/cyan] "
            continue
        lines.append(line)
        return "\n".join(lines).strip()


def _print_models(manager: ConversationManager) -> None:
    """Render installed Ollama models."""
    try:
        models = manager.list_models()
    except (OSError, ValueError) as exc:
        console.print(f"[red]Cannot list Ollama models:[/red] {exc}")
        return

    table = Table(title="Installed Ollama Models")
    table.add_column("Name")
    table.add_column("Size")
    table.add_column("Modified")
    for model in models:
        size = _format_size(model.size)
        table.add_row(model.name, size, model.modified_at or "-")
    console.print(table)


def _print_response(manager: ConversationManager, user_input: str) -> None:
    """Print one model response."""
    if manager.settings.streaming_enabled:
        console.print("[green]assistant>[/green] ", end="")
        for chunk in manager.stream_response(user_input):
            console.print(chunk, end="")
        console.print()
        return

    result = manager.respond(user_input)
    if result.error:
        console.print(f"[red]{result.error}[/red]")
        return
    console.print(f"[green]assistant>[/green] {result.response}")


def _print_directory_listing(data: dict[str, object]) -> None:
    """Render a directory listing."""
    table = Table(title=f"Files: {data.get('path')}")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Size")
    table.add_column("Modified")
    for entry in data.get("entries", []):
        if not isinstance(entry, dict):
            continue
        table.add_row(
            Path(str(entry.get("path", ""))).name,
            "dir" if entry.get("is_dir") else "file",
            _format_size(int(entry.get("size", 0))),
            str(entry.get("modified", "-")),
        )
    console.print(table)


def _print_search_results(data: dict[str, object]) -> None:
    """Render file search results."""
    table = Table(title=f"Search Results ({data.get('total', 0)})")
    table.add_column("Path")
    table.add_column("Size")
    for row in data.get("results", []):
        if not isinstance(row, dict):
            continue
        table.add_row(str(row.get("path", "")), _format_size(int(row.get("size", 0))))
    console.print(table)


def _print_read_result(data: dict[str, object]) -> None:
    """Render a read result compactly."""
    if "content" in data and isinstance(data["content"], str):
        console.print(data["content"])
        return
    console.print(data)


def _print_index_status(data: dict[str, object]) -> None:
    """Render index status."""
    console.print(f"Index: {data.get('path')}")
    console.print(f"Files: {data.get('files', 0)}")
    console.print(f"Available: {data.get('available')}")
    roots = data.get("roots", [])
    if roots:
        console.print("Roots:")
        for root in roots:
            console.print(f"  {root}")


def _format_size(size: int | None) -> str:
    """Format a byte count for display."""
    if size is None:
        return "-"
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def run_cli(args: list[str] | None = None) -> None:
    """Run the Typer application."""
    app(args=args, prog_name="linux-ai-assistant")


if __name__ == "__main__":
    run_cli()
