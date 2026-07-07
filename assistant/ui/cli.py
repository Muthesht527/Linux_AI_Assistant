"""Typer CLI entry point for Linux AI Assistant."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from assistant.config.config_loader import ConfigLoader
from assistant.core.bootstrap import build_startup_context, startup_banner
from assistant.core.conversation_manager import ConversationManager
from assistant.core.constants import APP_VERSION
from assistant.core.exceptions import AssistantError
from assistant.core.orchestrator import ConversationOrchestrator
from assistant.core.production import (
    ReleaseManager,
    VersionManager,
    configure_runtime_memory,
    get_runtime,
)
from assistant.core.tool_engine import ToolEngine
from assistant.diagnostics import DiagnosticsConfiguration, DiagnosticsManager
from assistant.filesystem import FilesystemConfiguration, FilesystemManager
from assistant.memory import MemoryManager
from assistant.plugins import PluginManager
from assistant.project import ErrorAnalyzer, GitRepositoryManager, ProjectConfiguration, RepositoryAnalyzer
from assistant.utils.dependencies import check_dependencies
from assistant.utils.environment import detect_environment

app = typer.Typer(
    add_completion=False,
    help="Foundation CLI for the local Linux AI Assistant.",
    no_args_is_help=False,
)
console = Console()
_memory_configured = False


def _build_conversation_manager() -> ConversationManager:
    """Create a configured local conversation manager."""
    settings = ConfigLoader().load_settings()
    tool_engine = ToolEngine()
    tool_engine.load_package("assistant.tools")
    for plugin in _build_plugin_manager().discover():
        if tool_engine.registry.find(plugin.name) is None:
            tool_engine.register(plugin)
    manager = ConversationManager(
        settings.conversation,
        orchestrator=ConversationOrchestrator(tool_engine),
    )
    memory = _build_memory_manager()
    memory.session.current_model = manager.models.current_model
    memory.record_model(manager.models.current_model)
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
    if editor:
        memory.preferences.set("favourite_editor", editor)
    return manager


def _build_filesystem_manager() -> FilesystemManager:
    """Create a configured filesystem manager."""
    settings = ConfigLoader().load_settings()
    configuration = FilesystemConfiguration(**settings.filesystem.model_dump())
    _build_memory_manager().session.current_working_directory = str(Path.cwd())
    return FilesystemManager(configuration)


def _build_diagnostics_manager() -> DiagnosticsManager:
    settings = ConfigLoader().load_settings()
    configuration = DiagnosticsConfiguration(**settings.diagnostics.model_dump())
    return DiagnosticsManager(configuration)


def _build_repository_analyzer() -> RepositoryAnalyzer:
    """Create a configured repository analyzer."""
    settings = ConfigLoader().load_settings()
    configuration = ProjectConfiguration(**settings.project.model_dump())
    _build_memory_manager().session.current_project = str(Path.cwd())
    return RepositoryAnalyzer(configuration)


def _build_git_manager() -> GitRepositoryManager:
    """Create a configured read-only Git manager."""
    settings = ConfigLoader().load_settings()
    configuration = ProjectConfiguration(**settings.project.model_dump())
    _build_memory_manager().session.current_repository = str(Path.cwd())
    return GitRepositoryManager(configuration)


def _build_memory_manager() -> MemoryManager:
    """Create a configured memory manager."""
    global _memory_configured
    settings = ConfigLoader().load_settings()
    if not _memory_configured:
        configure_runtime_memory(
            MemoryManager(
                db_path=settings.memory.database_path,
                max_recent_items=settings.memory.max_recent_items,
                sensitive_keys=settings.memory.sensitive_keys,
            )
        )
        _memory_configured = True
    memory = get_runtime().memory
    memory.session.current_working_directory = str(Path.cwd())
    memory.session.current_configuration = settings.model_dump(mode="json")
    return memory


def _build_plugin_manager() -> PluginManager:
    """Create a configured plugin manager."""
    settings = ConfigLoader().load_settings()
    return PluginManager(disabled_plugins=settings.plugins.disabled_plugins)


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
        runtime = get_runtime()
        runtime.statistics.record_command(ctx.invoked_subcommand)
        runtime.memory.record_command(ctx.invoked_subcommand)
        _build_memory_manager()
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
    _build_memory_manager().record_folder(str(path.expanduser().resolve()))
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
    get_runtime().statistics.record_filesystem_search(query)
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
    _build_memory_manager().session.remember_file(str(path.expanduser().resolve()))
    manager = _build_filesystem_manager()
    try:
        data = manager.read(path, preview_rows)
    except (OSError, ValueError) as exc:
        console.print(f"[red]Read failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    _print_read_result(data)


@app.command()
def project(
    command: str = typer.Argument("summary", help="Project command: summary."),
    path: Path = typer.Argument(Path("."), help="Project path."),
) -> None:
    """Inspect a local project without changing files."""
    if command not in {"summary", "/project", "/project summary"}:
        console.print("[red]Unknown project command. Use summary.[/red]")
        raise typer.Exit(code=1)
    _build_memory_manager().record_repository(str(path.expanduser().resolve()))
    _print_project_summary(_build_repository_analyzer().analyze(path))


@app.command(name="git")
def git_command(
    command: str = typer.Argument("status", help="Git command: status, history, or diff."),
    path: Path = typer.Argument(Path("."), help="Repository path."),
) -> None:
    """Inspect Git repositories without modifying history or remotes."""
    _build_memory_manager().record_repository(str(path.expanduser().resolve()))
    manager = _build_git_manager()
    if command in {"status", "/git status"}:
        _print_git_status(manager.status(path))
        return
    if command in {"history", "/git history"}:
        _print_git_history(manager.history(path))
        return
    if command in {"diff", "/git diff"}:
        _print_git_diff(manager.diff(path))
        return
    console.print("[red]Unknown git command. Use status, history, or diff.[/red]")
    raise typer.Exit(code=1)


@app.command()
def readme(path: Path = typer.Argument(Path("."), help="Project path.")) -> None:
    """Read and summarize README documentation."""
    _print_readme(_build_repository_analyzer().docs.read(path))


@app.command()
def todos(path: Path = typer.Argument(Path("."), help="Project path.")) -> None:
    """List TODO and FIXME comments."""
    _print_rows(_build_repository_analyzer().search_symbols(path, "", "todo"), "TODOs")


@app.command(name="explain-error")
def explain_error(text: list[str] = typer.Argument(..., help="Error or stack trace text.")) -> None:
    """Explain a compiler error, runtime error, or stack trace."""
    _print_error_analysis(ErrorAnalyzer().analyze(" ".join(text)))


@app.command(name="memory")
def memory_command(
    command: str = typer.Argument("list", help="Memory command: list, clear, export, import."),
    path: Path | None = typer.Argument(None, help="Path for export or import."),
) -> None:
    """Inspect or manage local assistant memory."""
    manager = _build_memory_manager()
    if command in {"list", "/memory", "/memory list"}:
        _print_memory(manager.list_memory())
        return
    if command in {"clear", "/memory clear"}:
        manager.clear(include_persistent=True)
        console.print("[green]Memory cleared.[/green]")
        return
    if command in {"export", "/memory export"}:
        if path is None:
            console.print("[red]Provide an export path.[/red]")
            raise typer.Exit(code=1)
        path.write_text(json.dumps(manager.export(), indent=2), encoding="utf-8")
        console.print(f"[green]Memory exported to {path}.[/green]")
        return
    if command in {"import", "/memory import"}:
        if path is None:
            console.print("[red]Provide an import path.[/red]")
            raise typer.Exit(code=1)
        manager.import_data(json.loads(path.read_text(encoding="utf-8")))
        console.print(f"[green]Memory imported from {path}.[/green]")
        return
    console.print("[red]Unknown memory command. Use list, clear, export, or import.[/red]")
    raise typer.Exit(code=1)


@app.command(name="preferences")
def preferences_command(
    command: str = typer.Argument("list", help="Preference command: list, set, get, reset."),
    key: str | None = typer.Argument(None, help="Preference key."),
    value: str | None = typer.Argument(None, help="Preference value for set."),
) -> None:
    """Inspect or manage local user preferences."""
    preferences = _build_memory_manager().preferences
    if command in {"list", "/preferences"}:
        _print_mapping("Preferences", preferences.list())
        return
    if command == "get":
        if key is None:
            console.print("[red]Provide a preference key.[/red]")
            raise typer.Exit(code=1)
        console.print(preferences.get(key, ""))
        return
    if command == "set":
        if key is None or value is None:
            console.print("[red]Provide a preference key and value.[/red]")
            raise typer.Exit(code=1)
        preferences.set(key, value)
        console.print(f"[green]Preference saved: {key}[/green]")
        return
    if command in {"reset", "/preferences reset"}:
        preferences.reset()
        console.print("[green]Preferences reset.[/green]")
        return
    console.print("[red]Unknown preferences command. Use list, get, set, or reset.[/red]")
    raise typer.Exit(code=1)


@app.command(name="plugins")
def plugins_command(
    command: str = typer.Argument(
        "list",
        help="Plugin command: list, reload, enable, disable, validate, or info.",
    ),
    name: str | None = typer.Argument(None, help="Plugin name for enable, disable, or info."),
) -> None:
    """Inspect auto-discovered plugins."""
    manager = _build_plugin_manager()
    runtime = get_runtime()
    if command in {"list", "/plugins", "/plugins list"}:
        runtime.statistics.record_plugin("list")
        _print_plugins(manager.list_metadata())
        return
    if command in {"reload", "/plugins reload"}:
        manager.reload()
        runtime.statistics.record_plugin("reload")
        console.print("[green]Plugins reloaded.[/green]")
        _print_plugins(manager.list_metadata())
        return
    if command == "enable":
        if not name:
            console.print("[red]Provide a plugin name to enable.[/red]")
            raise typer.Exit(code=1)
        manager.discover()
        manager.enable(name)
        runtime.statistics.record_plugin("enable")
        console.print(f"[green]Plugin enabled: {name}[/green]")
        return
    if command == "disable":
        if not name:
            console.print("[red]Provide a plugin name to disable.[/red]")
            raise typer.Exit(code=1)
        manager.discover()
        manager.disable(name)
        runtime.statistics.record_plugin("disable")
        console.print(f"[green]Plugin disabled: {name}[/green]")
        return
    if command == "validate":
        manager.reload()
        runtime.statistics.record_plugin("validate")
        _print_plugins(manager.list_metadata())
        if manager.errors:
            console.print(f"[yellow]Plugin issues: {_compact_value(manager.errors)}[/yellow]")
        return
    if command == "info":
        if not name:
            console.print("[red]Provide a plugin name for info.[/red]")
            raise typer.Exit(code=1)
        manager.discover()
        for plugin in manager.list_metadata():
            if plugin.name == name:
                runtime.statistics.record_plugin("info")
                _print_mapping("Plugin Info", asdict(plugin))
                return
        console.print(f"[red]Plugin not found: {name}[/red]")
        raise typer.Exit(code=1)
    console.print("[red]Unknown plugin command. Use list, reload, enable, disable, validate, or info.[/red]")
    raise typer.Exit(code=1)


@app.command(name="stats")
def stats_command() -> None:
    """Show process-local application statistics."""
    _print_mapping("Application Statistics", get_runtime().statistics.snapshot())


@app.command(name="about")
def about_command() -> None:
    """Show release information."""
    settings = ConfigLoader().load_settings()
    console.print(f"{settings.application.name} {settings.application.version}")
    console.print("Local Linux assistant with chat, tools, filesystem, diagnostics, coding, Git, memory, and plugins.")


@app.command(name="version")
def version_command() -> None:
    """Show application version."""
    info = VersionManager().info()
    console.print(f"{info['name']} {info['version']}")


@app.command(name="license")
def license_command() -> None:
    """Show project license text."""
    path = Path("LICENSE")
    if not path.exists():
        console.print("[yellow]LICENSE file not found.[/yellow]")
        raise typer.Exit(code=1)
    console.print(path.read_text(encoding="utf-8"))


@app.command(name="release")
def release_command() -> None:
    """Check release packaging readiness."""
    _print_mapping("Release Readiness", ReleaseManager(Path.cwd()).check())


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


def _make_diagnostics_command(action: str):
    def command() -> None:
        _print_diagnostics(getattr(_build_diagnostics_manager(), action)())

    command.__name__ = action
    command.__doc__ = f"Show read-only {action} diagnostics."
    return command


for _diagnostics_command_name, _diagnostics_action in {
    "system": "system",
    "cpu": "cpu",
    "memory-info": "memory",
    "disk": "disk",
    "processes": "processes",
    "services": "services",
    "kernel": "kernel",
    "network": "network",
    "hardware": "hardware",
}.items():
    app.command(name=_diagnostics_command_name)(_make_diagnostics_command(_diagnostics_action))


def _handle_chat_command(manager: ConversationManager, user_input: str) -> bool:
    """Handle slash commands inside the chat loop."""
    if user_input in {"/exit", "exit", "quit"}:
        raise typer.Exit()
    runtime = get_runtime()
    runtime.statistics.record_command(user_input.split(" ", 1)[0])
    runtime.memory.record_command(user_input.split(" ", 1)[0])
    if user_input in {"/reset", "/clear", "clear history"}:
        manager.reset()
        console.print("[green]Conversation history cleared.[/green]")
        return True
    if user_input in {"/help", "help"}:
        console.print("Commands: /models, /files, /search, /read, /project, /git status, /memory, /preferences, /plugins, /stats, /about, /version, /license, /exit")
        return True
    if user_input in {"/memory", "/memory list"}:
        _print_memory(_build_memory_manager().list_memory())
        return True
    if user_input == "/memory clear":
        _build_memory_manager().clear(include_persistent=True)
        console.print("[green]Memory cleared.[/green]")
        return True
    if user_input.startswith("/memory export "):
        path = Path(user_input.removeprefix("/memory export ").strip())
        path.write_text(json.dumps(_build_memory_manager().export(), indent=2), encoding="utf-8")
        console.print(f"[green]Memory exported to {path}.[/green]")
        return True
    if user_input.startswith("/memory import "):
        path = Path(user_input.removeprefix("/memory import ").strip())
        _build_memory_manager().import_data(json.loads(path.read_text(encoding="utf-8")))
        console.print(f"[green]Memory imported from {path}.[/green]")
        return True
    if user_input in {"/preferences", "/preferences list"}:
        _print_mapping("Preferences", _build_memory_manager().preferences.list())
        return True
    if user_input == "/preferences reset":
        _build_memory_manager().preferences.reset()
        console.print("[green]Preferences reset.[/green]")
        return True
    if user_input in {"/plugins", "/plugins list"}:
        _print_plugins(_build_plugin_manager().list_metadata())
        return True
    if user_input == "/plugins reload":
        plugin_manager = _build_plugin_manager()
        plugin_manager.reload()
        _print_plugins(plugin_manager.list_metadata())
        return True
    if user_input.startswith("/plugins enable "):
        plugin_name = user_input.removeprefix("/plugins enable ").strip()
        plugin_manager = _build_plugin_manager()
        plugin_manager.discover()
        plugin_manager.enable(plugin_name)
        runtime.statistics.record_plugin("enable")
        console.print(f"[green]Plugin enabled: {plugin_name}[/green]")
        return True
    if user_input.startswith("/plugins disable "):
        plugin_name = user_input.removeprefix("/plugins disable ").strip()
        plugin_manager = _build_plugin_manager()
        plugin_manager.discover()
        plugin_manager.disable(plugin_name)
        runtime.statistics.record_plugin("disable")
        console.print(f"[green]Plugin disabled: {plugin_name}[/green]")
        return True
    if user_input == "/plugins validate":
        plugin_manager = _build_plugin_manager()
        plugin_manager.reload()
        _print_plugins(plugin_manager.list_metadata())
        return True
    if user_input.startswith("/plugins info "):
        plugin_name = user_input.removeprefix("/plugins info ").strip()
        plugin_manager = _build_plugin_manager()
        plugin_manager.discover()
        for plugin in plugin_manager.list_metadata():
            if plugin.name == plugin_name:
                _print_mapping("Plugin Info", asdict(plugin))
                return True
        console.print(f"[red]Plugin not found: {plugin_name}[/red]")
        return True
    if user_input == "/stats":
        _print_mapping("Application Statistics", get_runtime().statistics.snapshot())
        return True
    if user_input == "/about":
        about_command()
        return True
    if user_input == "/version":
        version_command()
        return True
    if user_input == "/license":
        license_command()
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
    if user_input.startswith("/search code "):
        query = user_input.removeprefix("/search code ").strip()
        _print_rows(_build_repository_analyzer().search_symbols(Path("."), query, "code"), "Code Search")
        return True
    if user_input.startswith("/search function "):
        query = user_input.removeprefix("/search function ").strip()
        _print_rows(_build_repository_analyzer().search_symbols(Path("."), query, "function"), "Function Search")
        return True
    if user_input.startswith("/search class "):
        query = user_input.removeprefix("/search class ").strip()
        _print_rows(_build_repository_analyzer().search_symbols(Path("."), query, "class"), "Class Search")
        return True
    if user_input.startswith("/search "):
        query = user_input.removeprefix("/search ").strip()
        _print_search_results(_build_filesystem_manager().search(partial=query, limit=50))
        return True
    if user_input.startswith("/read "):
        path = user_input.removeprefix("/read ").strip()
        _print_read_result(_build_filesystem_manager().read(path))
        return True
    if user_input in {"/project", "/project summary"}:
        _print_project_summary(_build_repository_analyzer().analyze(Path(".")))
        return True
    if user_input == "/git status":
        _print_git_status(_build_git_manager().status(Path(".")))
        return True
    if user_input == "/git history":
        _print_git_history(_build_git_manager().history(Path(".")))
        return True
    if user_input == "/git diff":
        _print_git_diff(_build_git_manager().diff(Path(".")))
        return True
    if user_input == "/readme":
        _print_readme(_build_repository_analyzer().docs.read(Path(".")))
        return True
    if user_input == "/todos":
        _print_rows(_build_repository_analyzer().search_symbols(Path("."), "", "todo"), "TODOs")
        return True
    if user_input.startswith("/explain error "):
        text = user_input.removeprefix("/explain error ").strip()
        _print_error_analysis(ErrorAnalyzer().analyze(text))
        return True
    if user_input == "/index status":
        _print_index_status(_build_filesystem_manager().index_status())
        return True
    if user_input == "/index rebuild":
        data = _build_filesystem_manager().rebuild_index()
        console.print(f"[green]Indexed {data['indexed']} files.[/green]")
        return True
    diagnostics_commands = {
        "/system": "system",
        "/cpu": "cpu",
        "/memory-info": "memory",
        "/disk": "disk",
        "/processes": "processes",
        "/services": "services",
        "/kernel": "kernel",
        "/network": "network",
        "/hardware": "hardware",
    }
    if user_input in diagnostics_commands:
        diagnostics = _build_diagnostics_manager()
        _print_diagnostics(getattr(diagnostics, diagnostics_commands[user_input])())
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


def _print_diagnostics(result: dict[str, object]) -> None:
    """Render diagnostics output."""
    title = str(result.get("name", "diagnostics")).replace("_", " ").title()
    if not result.get("success", False):
        console.print(f"[red]{title} failed:[/red] {result.get('error')}")
        return
    data = result.get("data", {})
    if isinstance(data, dict):
        table = Table(title=title)
        table.add_column("Field")
        table.add_column("Value")
        for key, value in data.items():
            table.add_row(str(key), _compact_value(value))
        console.print(table)
        return
    console.print(data)


def _print_project_summary(data: dict[str, object]) -> None:
    """Render a repository summary."""
    console.print(f"Project: {data.get('root')}")
    console.print(f"Git: {data.get('is_git_repository')}")
    console.print(f"Types: {_compact_value(data.get('project_types', []))}")
    console.print(f"Languages: {_compact_value(data.get('languages', {}))}")
    console.print(f"Files analyzed: {data.get('files_analyzed', 0)}")


def _print_git_status(data: dict[str, object]) -> None:
    """Render Git status."""
    console.print(f"Repository: {data.get('repository_root')}")
    console.print(f"Branch: {data.get('current_branch')}")
    console.print(f"Clean: {data.get('clean')}")
    console.print(f"Changed: {_compact_value(data.get('changed_files', []))}")
    console.print(f"Untracked: {_compact_value(data.get('untracked_files', []))}")


def _print_git_history(data: dict[str, object]) -> None:
    """Render recent Git history."""
    table = Table(title="Git History")
    table.add_column("Hash")
    table.add_column("Date")
    table.add_column("Subject")
    for commit in data.get("commits", []):
        if isinstance(commit, dict):
            table.add_row(str(commit.get("hash", "")), str(commit.get("date", "")), str(commit.get("subject", "")))
    console.print(table)


def _print_git_diff(data: dict[str, object]) -> None:
    """Render Git diff summary."""
    console.print(f"Repository: {data.get('repository_root')}")
    console.print(data.get("diff_stat") or "No unstaged diff.")


def _print_readme(data: dict[str, object]) -> None:
    """Render README summary."""
    if not data.get("found"):
        console.print("[yellow]No README found.[/yellow]")
        return
    console.print(f"README: {data.get('path')}")
    console.print(data.get("summary", ""))


def _print_rows(rows: list[dict[str, object]], title: str) -> None:
    """Render generic source search rows."""
    table = Table(title=title)
    table.add_column("Path")
    table.add_column("Line")
    table.add_column("Text")
    for row in rows:
        table.add_row(str(row.get("path", "")), str(row.get("line", "")), str(row.get("text", row.get("name", ""))))
    console.print(table)


def _print_error_analysis(data: dict[str, object]) -> None:
    """Render parsed stack trace details."""
    console.print(f"Message: {data.get('message', '')}")
    console.print(f"Explanation: {data.get('explanation', '')}")
    console.print(f"Root cause: {data.get('root_cause', '')}")


def _print_memory(data: dict[str, object]) -> None:
    """Render memory state."""
    session = data.get("session", {})
    persistent = data.get("persistent", [])
    if isinstance(session, dict):
        _print_mapping("Session Memory", session)
    table = Table(title="Persistent Memory")
    table.add_column("Namespace")
    table.add_column("Key")
    table.add_column("Value")
    table.add_column("Updated")
    if isinstance(persistent, list):
        for row in persistent:
            if isinstance(row, dict):
                table.add_row(
                    str(row.get("namespace", "")),
                    str(row.get("key", "")),
                    _compact_value(row.get("value")),
                    str(row.get("updated_at", "")),
                )
    console.print(table)


def _print_plugins(plugins: list[object]) -> None:
    """Render plugin metadata."""
    table = Table(title="Plugins")
    table.add_column("Name")
    table.add_column("Version")
    table.add_column("Enabled")
    table.add_column("Valid")
    table.add_column("Missing Dependencies")
    table.add_column("Module")
    for plugin in plugins:
        table.add_row(
            str(getattr(plugin, "name", "")),
            str(getattr(plugin, "version", "")),
            str(getattr(plugin, "enabled", "")),
            str(getattr(plugin, "valid", "")),
            _compact_value(getattr(plugin, "missing_dependencies", [])),
            str(getattr(plugin, "module", "")),
        )
    console.print(table)


def _print_mapping(title: str, data: dict[str, object]) -> None:
    """Render a mapping as a two-column table."""
    table = Table(title=title)
    table.add_column("Field")
    table.add_column("Value")
    for key, value in data.items():
        table.add_row(str(key), _compact_value(value))
    console.print(table)


def _compact_value(value: object) -> str:
    """Format nested diagnostics values for compact CLI display."""
    if isinstance(value, list):
        if not value:
            return "[]"
        preview = ", ".join(str(item) for item in value[:5])
        suffix = "" if len(value) <= 5 else f" ... ({len(value)} total)"
        return preview + suffix
    if isinstance(value, dict):
        if not value:
            return "{}"
        return ", ".join(f"{key}={_compact_value(item)}" for key, item in value.items())
    return "-" if value is None else str(value)


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
