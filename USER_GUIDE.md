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
python3 main.py stats
python3 main.py release
```

## Chat Slash Commands

The chat loop supports `/models`, `/files`, `/search`, `/read`, `/project`,
`/git status`, `/git history`, `/git diff`, `/readme`, `/todos`, `/memory`,
`/preferences`, `/plugins`, `/stats`, `/about`, `/version`, `/license`, and
`/exit`.

Diagnostics shortcuts include `/system`, `/cpu`, `/memory-info`, `/disk`,
`/processes`, `/services`, `/kernel`, `/network`, and `/hardware`.

## Safety

Filesystem, diagnostics, coding, and Git operations are read-only unless a tool
explicitly requires confirmation. The assistant never performs desktop
automation, browser control, cloud inference, remote execution, or automatic code
modification in Version 1.
