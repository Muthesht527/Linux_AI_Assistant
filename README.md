# Linux AI Assistant

A local Linux desktop assistant built around Python, Ollama, and a modular tool system.
Phase 1 provides the production foundation only: configuration, logging, startup,
CLI, dependency checks, and project structure.

## Installation

Use Python 3.12 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
```

## Running

```bash
python3 main.py
python3 main.py --help
python3 main.py --version
python3 main.py config
python3 main.py doctor
python3 main.py info
```

Startup validates Python, loads YAML configuration, creates required
directories, initializes rotating file and console logging, and exits cleanly on
expected failures.

## Structure

- assistant/core: controllers and orchestration
- assistant/models: model and provider abstractions
- assistant/tools: independent tools inheriting from BaseTool
- assistant/plugins: plugin discovery and registration
- assistant/memory: local SQLite-backed memory
- assistant/config: YAML-based configuration
- assistant/ui: Rich-based CLI experience
- assistant/utils: environment, dependency, and logging helpers
- docs: project documentation
- tests: automated tests

## Configuration

Configuration is stored in `assistant/config/settings.yaml`. Copy
`assistant/config/settings.example.yaml` when creating a local variant. Paths are
resolved from the project root unless an absolute path is supplied.

## Testing

```bash
pytest
python3 -m compileall assistant main.py
```

## Future Phases

Later phases will add local model integration, tools, memory, file search,
terminal diagnostics, and plugin expansion according to `00_MASTER_SPEC.md`.
