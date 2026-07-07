# Linux AI Assistant

A local Linux desktop assistant built around Python, Ollama, and a modular tool system.
The project currently includes the foundation, local chat integration, Tool Engine,
and filesystem engine for indexing, search, reading, metadata, and directory listing.

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
python3 main.py files .
python3 main.py search notes --ext md
python3 main.py search "class Example" --content
python3 main.py read README.md
python3 main.py index status
python3 main.py index rebuild
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

The `filesystem` section controls indexed paths, ignored folders, ignored
extensions, maximum readable file size, metadata cache size, SQLite index
location, disabled locations, and standard root discovery. When `indexed_paths`
is empty, the assistant detects standard Linux roots and mounted partitions from
the local system.

## Filesystem Engine

Filesystem capabilities are exposed through Tool Engine tools:

- `search_file`: searches indexed files by partial name, filename, extension,
  directory, regex, size, date, case sensitivity, fuzzy match, or text content.
- `read_file`: reads supported files and returns structured content.
- `file_metadata`: returns path, size, extension, owner, permissions, modified
  time, created time, MIME type, and type flags.
- `directory_list`: lists a directory with metadata.
- `index_status`: reports SQLite index status and detected roots.
- `rebuild_index`: rebuilds the SQLite index and requires `ASK` permission.

The index is stored in SQLite and updated incrementally. Search uses the SQLite
index first. Metadata is cached with a bounded local cache that can be cleared by
the filesystem manager.

Supported readable formats include `txt`, `md`, `pdf`, `docx`, `csv`, `json`,
`yaml`, `xml`, `py`, `java`, `cpp`, `c`, `html`, `css`, and `js`. PDF support
uses PyMuPDF, DOCX support uses python-docx, and YAML support uses PyYAML.

## Testing

```bash
pytest
python3 -m compileall assistant main.py
```

## Future Phases

Later phases will add terminal diagnostics, Git assistance, package management,
hardware information, memory expansion, and plugin expansion according to
`00_MASTER_SPEC.md`.
