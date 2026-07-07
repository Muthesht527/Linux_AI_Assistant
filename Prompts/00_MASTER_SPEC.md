# Linux AI Assistant
# MASTER SOFTWARE SPECIFICATION
Version: 1.0

This document is the MASTER SPECIFICATION.

Every future implementation MUST follow this document.

This document is the highest authority of the project.

Never violate this specification.

If a future prompt conflicts with this document,
THIS DOCUMENT ALWAYS WINS.

------------------------------------------------------------

PROJECT NAME

Linux AI Assistant

------------------------------------------------------------

PROJECT GOAL

Create a completely LOCAL AI assistant for Linux.

The assistant runs entirely on the user's machine.

Primary model:

Ollama

Supported models

- Qwen 3
- Qwen 2.5
- Future Ollama models

No cloud inference.

No external APIs required.

Internet is optional.

------------------------------------------------------------

PRIMARY PURPOSE

This is NOT another chatbot.

This is a Linux desktop assistant.

The assistant should understand

• Linux
• File System
• Projects
• Programming
• Logs
• Hardware
• Running Processes
• Installed Software

The assistant is NOT responsible for desktop automation.

Desktop automation will be implemented in Version 2.

------------------------------------------------------------

VERSION 1 FEATURES

✔ Chat

✔ Tool Calling

✔ File Search

✔ File Reading

✔ Terminal Commands

✔ Linux Diagnostics

✔ Coding Assistant

✔ Project Understanding

✔ Git Assistant

✔ Package Manager

✔ Hardware Information

✔ Memory

✔ Logging

✔ Plugin System

------------------------------------------------------------

VERSION 2 FEATURES

DO NOT IMPLEMENT

Mouse

Keyboard

Voice

Screen OCR

Vision

Browser Control

Desktop Automation

Wake Word

------------------------------------------------------------

SUPPORTED OPERATING SYSTEMS

Ubuntu

Kubuntu

Linux Mint

Debian

Fedora (future)

Arch (future)

------------------------------------------------------------

PROGRAMMING LANGUAGE

Python

Python >= 3.12

Nothing else.

------------------------------------------------------------

PROJECT PHILOSOPHY

Simple.

Modular.

Maintainable.

Readable.

Professional.

Everything must be replaceable.

Everything must be documented.

------------------------------------------------------------

CODING STYLE

PEP8

Type Hints

Google Style Docstrings

No global variables.

No magic numbers.

No duplicated code.

No circular imports.

No giant files.

Maximum

500 lines per file.

If larger,

split it.

------------------------------------------------------------

DIRECTORY STRUCTURE

assistant/

core/

models/

tools/

plugins/

memory/

config/

cache/

logs/

ui/

utils/

tests/

docs/

Every folder must have a clear responsibility.

------------------------------------------------------------

ARCHITECTURE

User

↓

CLI

↓

Assistant Controller

↓

Conversation Manager

↓

LLM

↓

Tool Engine

↓

Tool

↓

Result

↓

LLM

↓

User

The LLM NEVER directly executes anything.

------------------------------------------------------------

THE MODEL

The LLM only reasons.

The LLM never

reads files

runs commands

searches directories

executes shell

Everything happens through tools.

------------------------------------------------------------

TOOL CALLING

The assistant decides

"I need a tool."

Python validates.

Python executes.

Python returns structured output.

The model explains.

Never allow the LLM to execute arbitrary code.

------------------------------------------------------------

TOOLS MUST BE INDEPENDENT

Each tool lives in

tools/

Each tool is its own class.

Each tool inherits BaseTool.

Each tool contains

description

permission level

timeout

schema

validation

execution

logging

------------------------------------------------------------

PERMISSIONS

Every tool belongs to one level.

SAFE

ASK

BLOCKED

Examples

Read File

SAFE

Delete File

ASK

rm -rf /

BLOCKED

Never bypass permissions.

------------------------------------------------------------

FILESYSTEM

Support

home

mnt

media

mounted drives

Automatically detect mounted drives.

Never hardcode paths.

Use pathlib.

------------------------------------------------------------

FILE SEARCH

Support

name

extension

regex

date

size

duplicates

content

Search must support multiple roots.

------------------------------------------------------------

DOCUMENT SUPPORT

txt

md

pdf

docx

csv

json

yaml

xml

html

css

java

python

cpp

c

js

------------------------------------------------------------

TERMINAL

Never use

shell=True

Never use

eval()

Never use

exec()

Use subprocess safely.

Whitelist commands.

------------------------------------------------------------

LINUX TOOLS

Support

systemctl

journalctl

dmesg

lsusb

lspci

lsblk

free

df

du

ps

top

git

apt

snap

flatpak

Everything wrapped as tools.

------------------------------------------------------------

MEMORY

Session Memory

Persistent Memory

Stored locally.

SQLite.

Never send memory outside.

------------------------------------------------------------

DATABASE

SQLite only.

No MySQL.

No PostgreSQL.

No MongoDB.

------------------------------------------------------------

CONFIGURATION

Use YAML.

Never hardcode values.

Everything configurable.

------------------------------------------------------------

LOGGING

Use logging module.

Every tool logs

execution time

errors

arguments

result

Logs stored inside

logs/

------------------------------------------------------------

ERROR HANDLING

Never crash.

Catch exceptions.

Return useful errors.

Never expose stack traces to users.

------------------------------------------------------------

SECURITY

Never execute dangerous commands automatically.

Never elevate privileges.

Never request sudo automatically.

Never modify files without permission.

Never delete without confirmation.

------------------------------------------------------------

PLUGIN SYSTEM

Every plugin registers itself.

Plugins can expose tools.

The assistant automatically discovers plugins.

Never hardcode plugin loading.

------------------------------------------------------------

DEPENDENCIES

Minimal dependencies.

Only add packages when necessary.

------------------------------------------------------------

UI

Use Rich.

Streaming responses.

Markdown rendering.

Progress bars.

Syntax highlighting.

Panels.

Tables.

------------------------------------------------------------

TESTING

Every major module must include tests.

Every phase must compile before continuing.

------------------------------------------------------------

DOCUMENTATION

Every class

Every function

Every module

must contain documentation.

------------------------------------------------------------

GIT

Every phase ends with

git add .

git commit

Commit messages

Phase 1

"Initialize project architecture"

Phase 2

"Add Ollama integration"

Phase 3

"Implement tool engine"

Phase 4

"Implement filesystem"

Phase 5

"Implement Linux tools"

Phase 6

"Implement coding assistant"

Phase 7

"Implement memory"

Phase 8

"Production release"

------------------------------------------------------------

IMPORTANT RULES

Never rewrite working code.

Never delete existing features.

Extend.

Do not replace.

Never create placeholders.

Never leave TODO comments.

Never generate pseudocode.

Everything must compile.

Everything must run.

Everything must be production quality.

------------------------------------------------------------

WHEN IMPLEMENTING FUTURE PHASES

Always

1.

Read this file.

2.

Understand the architecture.

3.

Inspect the existing codebase.

4.

Preserve architecture.

5.

Implement only the requested phase.

6.

Run tests.

7.

Fix errors.

8.

Update documentation.

9.

Perform git add .

10.

Perform git commit using the required message.

------------------------------------------------------------

END OF MASTER SPECIFICATION