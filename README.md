# Linux AI Assistant

A local Linux desktop assistant built around Python, Ollama, SQLite, Rich, and a
modular tool system. Version 1.0 includes local chat, Tool Engine, filesystem
search and reading, safe terminal commands, read-only Linux diagnostics, a
read-only coding and Git assistant, local memory, plugin discovery, statistics,
and release checks.

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
python3 main.py system
python3 main.py cpu
python3 main.py memory
python3 main.py disk
python3 main.py processes
python3 main.py services
python3 main.py kernel
python3 main.py network
python3 main.py hardware
python3 main.py project summary .
python3 main.py git status .
python3 main.py git history .
python3 main.py git diff .
python3 main.py readme .
python3 main.py todos .
python3 main.py explain-error "ModuleNotFoundError: No module named 'rich'"
python3 main.py memory list
python3 main.py memory export memory.json
python3 main.py preferences list
python3 main.py plugins list
python3 main.py stats
python3 main.py about
python3 main.py version
python3 main.py license
python3 main.py release
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

The `diagnostics` section controls read-only collection limits:
`max_processes`, `journal_lines`, command `timeout`, `ignored_services`, and
`ignored_devices`.

The `project` section controls repository analysis: ignored folders, ignored
languages, maximum repository size, maximum source file size, maximum files
analyzed, and Git history depth.

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

## Linux Diagnostics Engine

Diagnostics are read-only. The assistant may inspect `/proc`, `/sys`, system
identity files, and non-mutating commands such as `df`, `lsblk`, `lscpu`,
`lsusb`, `lspci`, `ps`, `systemctl` status/list operations, `journalctl`,
`uname`, and `ip`. It never restarts services, edits logs, changes network
configuration, installs packages, kills processes, mounts disks, or modifies the
operating system.

Tool Engine diagnostics tools:

- `diagnostics`: complete read-only snapshot with summary findings.
- `system_info`: hostname, kernel, distribution, desktop, architecture, user,
  shell, and Python version.
- `cpu_info`: CPU model, core counts, frequency, usage, load, and temperature
  when available.
- `memory_info`: installed, used, available, cached, buffers, swap, and huge
  pages.
- `disk_info`: mounted filesystems, usage, block device output, SSD/NVMe hints,
  and disk statistics availability.
- `battery_info`: percentage, charging state, health, cycles, and remaining time
  when available.
- `gpu_info`, `usb_info`, `pci_info`, and `hardware_info`: read-only hardware
  inventory.
- `process_info`: running process count, top CPU/RAM, zombies, and orphans.
- `service_info`: active and failed services, plus read-only status for a named
  service.
- `journal_info`: recent boot journal lines, optional error filtering, and
  search.
- `kernel_info`: kernel version, loaded modules, and boot time.
- `network_info`: hostname, interfaces, IP addresses, MAC addresses, gateway,
  and DNS.

The chat loop also supports `/system`, `/cpu`, `/memory-info`, `/disk`,
`/processes`, `/services`, `/kernel`, `/network`, and `/hardware`.

## Coding And Git Assistant

Project analysis is read-only. The assistant can inspect source files,
dependency manifests, README files, stack traces, and Git metadata, but it does
not edit code, refactor files, commit, push, pull, or rewrite Git history.

Supported languages include Python, Java, C, C++, JavaScript, TypeScript, HTML,
CSS, JSON, YAML, Markdown, XML, Shell, and SQL, with basic Rust and Go project
detection. Project detection recognizes Git repositories, Python, Java, Node,
CMake, Gradle, Maven, Flask/FastAPI hints, Django, React, Vue, Angular, Rust,
and Go.

Dependency readers inspect `requirements.txt`, `pyproject.toml`,
`package.json`, `pom.xml`, `build.gradle`, `Cargo.toml`, `go.mod`, and
`CMakeLists.txt`. README support extracts project purpose, setup notes, and
dependency sections when present.

Tool Engine project tools:

- `project_summary` and `repository_summary`: summarize local projects.
- `code_search`, `function_search`, and `class_search`: search source content
  and symbols.
- `dependency_reader`: read dependency manifests.
- `stack_trace`: parse compiler errors, runtime errors, and stack traces.
- `git_status`, `git_history`, and `git_diff`: read Git state without changing
  repositories.
- `readme_reader`, `todo_search`, and `language_detector`: inspect docs,
  TODO/FIXME comments, and detected source languages.

The chat loop supports `/project`, `/project summary`, `/git status`,
`/git history`, `/git diff`, `/readme`, `/todos`, `/search code`,
`/search function`, `/search class`, and `/explain error`.

## Memory, Plugins, And Release Tools

Memory is local-only. Session memory tracks the current working directory,
project, repository, model, recent files, recent tools, and recent conversation
turns for the current process. Persistent memory uses SQLite and stores
preferences, frequent folders, recent projects, preferred models, and other
non-sensitive user preferences. Keys that look sensitive, such as passwords,
tokens, secrets, credentials, and keys, are not stored automatically.

The chat loop supports `/memory`, `/memory list`, `/memory clear`,
`/memory export`, `/memory import`, `/preferences`, `/preferences reset`,
`/plugins`, `/plugins list`, `/plugins reload`, `/plugins enable`,
`/plugins disable`, `/plugins validate`, `/plugins info`, `/stats`, `/about`,
`/version`, and `/license`. The diagnostics memory shortcut is `/memory-info`.

Plugin discovery loads `BaseTool` subclasses from `assistant/plugins`, validates
metadata, tracks enabled state, exposes version and author details, and supports
reload. Enabled and disabled plugin state is persisted locally in the cache
directory. Release readiness checks verify packaging files such as README,
LICENSE, requirements, and `pyproject.toml`.

Runtime cache is process-local and covers configuration loads, filesystem
queries, file reads, repository summaries, diagnostics snapshots, Ollama model
lists, and tool lookups. Stale entries expire automatically and index rebuilds
invalidate cached filesystem data. Statistics track command usage, tool
execution, response timing, cache usage, memory usage, plugin activity,
repository scans, filesystem searches, and errors.

## Documentation

- `INSTALL.md`: installation and verification.
- `USER_GUIDE.md`: user-facing commands and chat shortcuts.
- `DEVELOPER_GUIDE.md`: architecture, package responsibilities, and tests.
- `PLUGIN_DEVELOPMENT.md`: plugin tool requirements.
- `CONTRIBUTING.md`: contribution rules.
- `CHANGELOG.md`: release history.

## Testing

```bash
pytest
python3 -m compileall assistant main.py
```

## Release

Version 1.0 is the production-ready local release. Version 2 features such as
voice, OCR, vision, browser control, and desktop automation are intentionally not
implemented.
