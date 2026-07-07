# User Guide

Linux AI Assistant provides local chat, filesystem search, read-only terminal
commands, diagnostics, project analysis, Git inspection, memory, and plugins.

## Common Commands

```bash
python3 main.py chat
python3 main.py models list
python3 main.py files .
python3 main.py search notes --ext md
python3 main.py read README.md
python3 main.py system
python3 main.py project summary .
python3 main.py git status .
python3 main.py memory list
python3 main.py preferences list
python3 main.py plugins list
python3 main.py plugins validate
python3 main.py stats
python3 main.py release
```

## Chat Slash Commands

The chat loop supports `/models`, `/files`, `/search`, `/read`, `/project`,
`/git status`, `/git history`, `/git diff`, `/readme`, `/todos`, `/memory`,
`/preferences`, `/plugins`, `/plugins enable`, `/plugins disable`,
`/plugins validate`, `/plugins info`, `/stats`, `/about`, `/version`,
`/license`, and `/exit`.

Diagnostics shortcuts include `/system`, `/cpu`, `/memory-info`, `/disk`,
`/processes`, `/services`, `/kernel`, `/network`, and `/hardware`.

## Memory, Cache, And Statistics

Session memory updates automatically as commands open folders, read files,
inspect repositories, switch models, execute tools, and chat. Persistent memory
learns non-sensitive preferences and frequent usage such as preferred model,
editor, folders, repositories, languages, commands, and recent projects.

Runtime cache is local to the current process and accelerates configuration,
filesystem, diagnostics, repository, model, and tool lookups. `stats` shows
uptime, command and tool counts, response timing, cache counters, memory usage,
plugin activity, repository scans, filesystem searches, and errors.

## Safety

Filesystem, diagnostics, coding, and Git operations are read-only unless a tool
explicitly requires confirmation. The assistant never performs desktop
automation, browser control, cloud inference, remote execution, or automatic code
modification in Version 1.
