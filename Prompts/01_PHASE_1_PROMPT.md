# ============================================================
# PHASE 1 — PROJECT FOUNDATION
# Linux AI Assistant
# ============================================================

IMPORTANT

Read and strictly follow 00_MASTER_SPEC.md before making any changes.

DO NOT rewrite the project.

DO NOT regenerate existing files.

DO NOT audit the whole repository.

DO NOT summarize the repository.

DO NOT inspect unrelated files.

ONLY inspect files required for this phase.

ONLY modify files if absolutely necessary.

If an existing implementation already satisfies the specification,
leave it unchanged.

Prefer editing existing code instead of replacing entire files.

Never remove working functionality.

Never change architecture.

Never rename files unless absolutely required.

Keep token usage minimal.

------------------------------------------------------------

YOUR ROLE

You are a Senior Python Software Architect.

You are NOT generating a demo project.

You are building a production-quality Linux application.

Think before making changes.

Follow professional software engineering practices.

------------------------------------------------------------

GOAL

Complete the Project Foundation.

After this phase the project should have a clean architecture,
startup system,
configuration,
logging,
CLI,
dependency management,
error handling,
and project structure.

NO AI FEATURES.

NO TOOLS.

NO OLLAMA.

NO FILE SEARCH.

NO TERMINAL COMMANDS.

Foundation only.

------------------------------------------------------------

FIRST

Inspect only the files necessary for this phase.

Determine what already exists.

Reuse existing code whenever possible.

Only create missing components.

------------------------------------------------------------

IMPLEMENT

Project structure

Configuration system

Logging system

Application bootstrap

Startup banner

CLI entrypoint

Environment detection

Python version validation

Dependency checker

Constants

Path manager

Utility helpers

Custom exceptions

Settings loader

README improvements

requirements.txt

requirements-dev.txt

pyproject.toml

.gitignore

License

Configuration templates

------------------------------------------------------------

CONFIGURATION

Use Pydantic.

Configuration stored in YAML.

Never hardcode paths.

Never hardcode usernames.

Everything configurable.

------------------------------------------------------------

LOGGER

Use Python logging.

Rotating log files.

Console logger.

File logger.

Configurable log level.

Rich formatting if appropriate.

------------------------------------------------------------

CLI

Use Typer.

Create a professional CLI.

Support

--help

--version

config

doctor

info

The CLI should be extendable.

------------------------------------------------------------

STARTUP

Running

python main.py

must

Validate environment

Load configuration

Initialize logger

Initialize directories

Print startup banner

Exit gracefully on failure

------------------------------------------------------------

DIRECTORIES

Automatically create if missing

logs/

cache/

memory/

config/

plugins/

tests/

------------------------------------------------------------

DEPENDENCY CHECKER

Verify required Python version.

Verify required packages.

Provide friendly errors.

Never crash.

------------------------------------------------------------

CODE STYLE

Python 3.12+

PEP8

Type hints everywhere

Google style docstrings

Pathlib

Dataclasses or Pydantic where appropriate

No globals

No duplicated code

No circular imports

Maximum approximately 500 lines per file.

Split large modules.

------------------------------------------------------------

ERROR HANDLING

Never expose stack traces to users.

Catch expected exceptions.

Log unexpected exceptions.

Return useful messages.

------------------------------------------------------------

DOCUMENTATION

Every public

module

class

function

must contain documentation.

README must explain

installation

virtual environment

project structure

running

future phases

------------------------------------------------------------

TESTING

Create test structure.

Create initial tests for

configuration

logger

startup

CLI

Tests must pass.

------------------------------------------------------------

BEFORE FINISHING

Run static checks where possible.

Ensure imports are correct.

Ensure no circular imports.

Ensure project compiles.

Ensure startup works.

------------------------------------------------------------

OUTPUT

Do NOT explain every file.

Only summarize:

Files created

Files modified

Reason for modification

Known issues (if any)

------------------------------------------------------------

GIT

When implementation is complete execute:

git add .

git commit -m "Initialize project architecture"

If commit cannot be performed automatically,
provide the exact commands.

------------------------------------------------------------

SUCCESS CRITERIA

The phase is complete only if:

✓ Project builds

✓ Startup succeeds

✓ Configuration loads

✓ Logger works

✓ CLI works

✓ No placeholder code

✓ No TODO comments

✓ Documentation exists

✓ Tests pass

✓ Git commit completed

If any item fails,
fix it before ending the task.