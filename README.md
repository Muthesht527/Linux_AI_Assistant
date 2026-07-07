# Linux AI Assistant

A local Linux desktop assistant built around Ollama, Python, and a modular tool system.

## Structure

- assistant/core: controllers and orchestration
- assistant/models: model and provider abstractions
- assistant/tools: independent tools inheriting from BaseTool
- assistant/plugins: plugin discovery and registration
- assistant/memory: local SQLite-backed memory
- assistant/config: YAML-based configuration
- assistant/ui: Rich-based CLI experience
- tests: automated tests
