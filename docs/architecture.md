# Architecture

Linux AI Assistant is organized as a local-first Python package. The CLI accepts
user input, the assistant controller coordinates tool usage, and each tool
returns structured data for the assistant to explain.

## Package Responsibilities

- `assistant/core`: controller, conversation, and tool execution interfaces.
- `assistant/models`: local Ollama model integration points.
- `assistant/tools`: built-in independent tools that inherit from `BaseTool`.
- `assistant/plugins`: automatic plugin discovery for plugin-provided tools.
- `assistant/memory`: local SQLite-backed memory.
- `assistant/config`: YAML configuration loading.
- `assistant/cache`: local cache storage.
- `assistant/logs`: local log output.
- `assistant/ui`: Rich-based command line interface.
- `assistant/utils`: shared infrastructure helpers.
- `tests`: regression tests for implemented modules.
