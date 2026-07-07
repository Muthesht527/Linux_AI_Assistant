# ============================================================
# PHASE 4 — FILESYSTEM ENGINE
# Linux AI Assistant
# ============================================================

IMPORTANT

Read and strictly follow 00_MASTER_SPEC.md.

Read the existing project before making changes.

DO NOT audit the repository.

DO NOT regenerate working code.

DO NOT rewrite architecture.

Inspect ONLY files required for this phase.

Modify ONLY the minimum number of files.

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

Extend the existing project.

Do not redesign previous phases.

Reuse all existing abstractions.

The filesystem implementation MUST integrate with the Tool Engine.

------------------------------------------------------------

GOAL

Implement the complete Filesystem subsystem.

This phase allows the assistant to

Locate files

Read files

Index files

Search files

Search inside files

Return metadata

Support multiple mounted partitions

Everything must integrate into the Tool Engine.

DO NOT implement Terminal tools.

DO NOT implement Linux diagnostics.

DO NOT implement Git.

DO NOT implement Memory.

------------------------------------------------------------

FIRST

Inspect

Tool Engine

Configuration

Logger

Utilities

Reuse everything.

------------------------------------------------------------

IMPLEMENT

FilesystemManager

FilesystemIndexer

FilesystemSearcher

FilesystemReader

FilesystemMetadata

FilesystemCache

FilesystemConfiguration

FilesystemValidators

------------------------------------------------------------

SUPPORTED ROOTS

Automatically detect

/

home

mnt

media

mounted external drives

Do NOT hardcode paths.

Use pathlib everywhere.

------------------------------------------------------------

AUTOMATIC DRIVE DETECTION

Detect mounted partitions automatically.

Examples

Internal SSD

USB Drives

External HDD

Mounted network locations

Allow configuration to disable locations.

------------------------------------------------------------

INDEXING

Implement SQLite indexing.

Store

Absolute path

Filename

Extension

Size

Modification time

Creation time (if available)

Directory

File hash (optional)

Last indexed

Index updates must be incremental.

Do NOT rebuild the entire index every run.

------------------------------------------------------------

SEARCH

Search by

Filename

Extension

Directory

Regex

Modified date

Size

Partial name

Case sensitive

Case insensitive

Fuzzy search

------------------------------------------------------------

SEARCH INSIDE FILES

Support

txt

md

py

java

cpp

c

json

yaml

xml

html

css

js

csv

Search text inside files.

Support regex.

------------------------------------------------------------

FILE READERS

Implement readers for

txt

md

pdf

docx

csv

json

yaml

xml

python

java

cpp

c

html

css

javascript

Unknown formats should return friendly errors.

------------------------------------------------------------

PDF

Use PyMuPDF.

Extract text.

Return page count.

Return metadata.

------------------------------------------------------------

DOCX

Use python-docx.

Extract paragraphs.

Extract tables if practical.

------------------------------------------------------------

CSV

Read safely.

Return

headers

rows

column count

preview

------------------------------------------------------------

METADATA

Every file must expose

Path

Size

Extension

Owner

Permissions

Modified

Created

Mime type (if available)

------------------------------------------------------------

CACHE

Implement caching.

Frequently accessed metadata should be cached.

Allow cache clearing.

------------------------------------------------------------

TOOLS

Create tools

SearchFileTool

ReadFileTool

FileMetadataTool

DirectoryListTool

IndexStatusTool

RebuildIndexTool

Every tool must use the Tool Engine.

------------------------------------------------------------

CLI

Implement

/files

/search

/read

/index

/index status

/index rebuild

------------------------------------------------------------

PERMISSIONS

SAFE

Search

Read

Metadata

ASK

Rebuild index

BLOCKED

Delete

Move

Rename

Copy

Those operations are future features.

------------------------------------------------------------

PERFORMANCE

Large directories should not block the assistant.

Indexing should display progress.

Searching should prefer SQLite over recursive scanning.

Only fall back to recursive scanning if needed.

------------------------------------------------------------

ERROR HANDLING

Handle

Permission denied

Broken symlinks

Unreadable files

Unsupported formats

Missing files

Index corruption

Never crash.

------------------------------------------------------------

CONFIGURATION

Allow configuring

Indexed paths

Ignored folders

Ignored extensions

Maximum file size

Cache size

Index location

------------------------------------------------------------

IGNORED DIRECTORIES

Ignore by default

.git

.venv

__pycache__

node_modules

.cache

Trash

------------------------------------------------------------

TESTING

Create tests for

Search

Index

Readers

Metadata

Caching

Partition detection

Large directories

Errors

Tests must pass.

------------------------------------------------------------

DOCUMENTATION

Update README.

Document

Indexing

Searching

Supported formats

Configuration

Performance

------------------------------------------------------------

SELF CHECK

Before finishing verify

✓ Multiple partitions detected

✓ Mounted drives detected

✓ SQLite index operational

✓ Searching operational

✓ Reading operational

✓ Metadata operational

✓ Cache operational

✓ CLI operational

✓ Tests pass

✓ Documentation updated

✓ No TODO comments

✓ No placeholder code

------------------------------------------------------------

OUTPUT

Return only

Files created

Files modified

Reason for each modification

Known issues

------------------------------------------------------------

GIT

When complete execute

git add .

git commit -m "Implement filesystem engine"

If Git cannot be executed automatically,

provide the exact commands.

------------------------------------------------------------

SUCCESS CRITERIA

The phase is complete only if

✓ File searching works

✓ Reading works

✓ Mounted partitions supported

✓ SQLite indexing works

✓ CLI commands work

✓ Tool Engine integration complete

✓ Tests pass

✓ Project builds successfully

Do NOT continue to the next phase.