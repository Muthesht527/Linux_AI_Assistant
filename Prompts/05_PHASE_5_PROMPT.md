# ============================================================
# PHASE 5 — TERMINAL ENGINE
# Linux AI Assistant
# ============================================================

IMPORTANT

Read and strictly follow 00_MASTER_SPEC.md.

Read the existing project before making changes.

DO NOT audit the repository.

DO NOT regenerate working code.

DO NOT rewrite architecture.

Inspect ONLY the files required for this phase.

Modify ONLY the minimum number of files.

Never replace working implementations.

Never remove existing functionality.

Keep token usage as low as possible.

------------------------------------------------------------

PYTHON ENVIRONMENT

Always use the project's existing virtual environment (.venv).

Never create another virtual environment.

Never install packages globally.

If dependencies are required:

• Update requirements.txt
• Update requirements-dev.txt if appropriate
• Update pyproject.toml if appropriate

Use the existing virtual environment for all testing.

------------------------------------------------------------

ROLE

You are a Senior Python Software Architect.

Continue the existing project.

Do not redesign previous phases.

Reuse existing abstractions.

Everything must integrate with the Tool Engine.

------------------------------------------------------------

GOAL

Implement a secure Terminal Engine.

The assistant should be capable of executing SAFE Linux commands through the Tool Engine.

DO NOT implement Linux diagnostics yet.

DO NOT implement filesystem.

DO NOT implement memory.

DO NOT implement Git.

This phase only builds a secure terminal execution layer.

------------------------------------------------------------

FIRST

Inspect

Tool Engine

Configuration

Logger

Utilities

Reuse everything possible.

------------------------------------------------------------

IMPLEMENT

TerminalManager

CommandExecutor

CommandValidator

CommandParser

CommandHistory

TerminalConfiguration

TerminalContext

TerminalResult

------------------------------------------------------------

EXECUTION

Use subprocess safely.

NEVER use

shell=True

eval()

exec()

os.system()

------------------------------------------------------------

ALLOWED COMMANDS

Support only SAFE commands.

Examples

pwd

ls

lsblk

whoami

hostname

uname

date

free

df

du

tree

find

grep

cat

head

tail

wc

echo

which

whereis

file

stat

id

uptime

env

printenv

------------------------------------------------------------

BLOCKED COMMANDS

Never allow

sudo

su

rm

dd

mkfs

fdisk

shutdown

reboot

poweroff

halt

killall

chmod

chown

systemctl

journalctl

apt

snap

flatpak

mount

umount

curl

wget

ssh

scp

Anything capable of modifying the system.

------------------------------------------------------------

COMMAND VALIDATION

Validate

Executable

Arguments

Length

Illegal characters

Command whitelist

Timeout

Working directory

Reject invalid commands before execution.

------------------------------------------------------------

TIMEOUT

Every command must support configurable timeout.

Terminate safely if exceeded.

------------------------------------------------------------

OUTPUT

Capture

stdout

stderr

exit code

execution time

Return ToolResult.

------------------------------------------------------------

WORKING DIRECTORY

Support

pwd

cd (session only)

relative paths

absolute paths

Current working directory should persist only during the assistant session.

------------------------------------------------------------

TOOLS

Implement

RunCommandTool

WorkingDirectoryTool

CommandHistoryTool

CommandHelpTool

Every tool must integrate into the Tool Engine.

------------------------------------------------------------

CLI

Implement

/run

/history

/pwd

/cd

/help terminal

------------------------------------------------------------

SECURITY

Never execute commands without validation.

Never bypass PermissionManager.

Never expose shell injection vulnerabilities.

Escape user input appropriately.

------------------------------------------------------------

LOGGING

Log

command

arguments

execution time

exit code

errors

permission level

------------------------------------------------------------

CONFIGURATION

Allow configuring

timeout

history length

working directory

allowed commands

blocked commands

maximum output size

------------------------------------------------------------

TESTING

Create tests for

validation

execution

timeouts

history

working directory

blocked commands

allowed commands

error handling

Tests must pass.

------------------------------------------------------------

DOCUMENTATION

Update README.

Document

terminal usage

security model

supported commands

blocked commands

timeouts

configuration

------------------------------------------------------------

SELF CHECK

Before finishing verify

✓ Terminal Engine works

✓ Validation works

✓ Timeouts work

✓ History works

✓ Working directory works

✓ Tool integration complete

✓ Tests pass

✓ Documentation updated

✓ No placeholder code

✓ No TODO comments

------------------------------------------------------------

OUTPUT

Return only

Files created

Files modified

Reason for modifications

Known issues

------------------------------------------------------------

GIT

When implementation is complete execute

git add .

git commit -m "Implement terminal engine"

If Git cannot be executed automatically,

provide the exact commands.

------------------------------------------------------------

SUCCESS CRITERIA

✓ Safe command execution

✓ Tool Engine integration

✓ Validation operational

✓ Timeouts operational

✓ Tests pass

✓ Project builds successfully

Do NOT continue to the next phase.