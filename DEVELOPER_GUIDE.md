# Developer Guide

## Architecture

```text
User
  -> CLI
  -> Assistant Controller
  -> Conversation Manager
  -> Local Ollama Model
  -> Tool Engine
  -> Independent Tools
  -> Structured Results
```

Major packages:

- `assistant/core`: orchestration, tool engine, startup, release helpers
- `assistant/models`: local model integration
- `assistant/tools`: Tool Engine adapters
- `assistant/filesystem`: search, indexing, metadata, readers
- `assistant/terminal`: safe command execution
- `assistant/diagnostics`: read-only Linux diagnostics
- `assistant/project`: coding and Git analysis
- `assistant/memory`: session and persistent SQLite memory
- `assistant/plugins`: plugin discovery and validation
- `assistant/ui`: Rich/Typer CLI

Production runtime services live in `assistant/core/production.py`. They provide
shared process-local cache, statistics, release checks, and the configured
memory manager. Managers update these services during normal filesystem,
diagnostics, repository, model, plugin, and tool operations.

## Testing

```bash
source .venv/bin/activate
python3 -m pytest
python3 -m compileall assistant main.py
```

## Guidelines

Use pathlib, type hints, Google-style docstrings, SQLite for local storage, YAML
for configuration, and independent `BaseTool` subclasses for tools. Never use
`shell=True`, `eval`, or `exec` for command execution.
