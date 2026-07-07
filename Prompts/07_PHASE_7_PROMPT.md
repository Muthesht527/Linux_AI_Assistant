# ============================================================
# PHASE 7 — CODING & GIT ASSISTANT
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

If dependencies are required

Update

requirements.txt

requirements-dev.txt

pyproject.toml

Use the existing virtual environment for all testing.

------------------------------------------------------------

ROLE

You are a Senior Python Software Architect.

Continue extending the existing Linux AI Assistant.

Reuse all existing modules.

Everything must integrate into

Conversation Engine

Tool Engine

Filesystem Engine

Terminal Engine

Diagnostics Engine

Never duplicate existing functionality.

------------------------------------------------------------

GOAL

Transform the assistant into a programming assistant.

The assistant should understand

Projects

Repositories

Programming languages

Compiler errors

Runtime errors

Stack traces

Directory structures

Dependencies

Git repositories

The assistant must NEVER modify code automatically.

This phase is READ ONLY.

------------------------------------------------------------

DO NOT IMPLEMENT

Automatic code fixing

Automatic refactoring

Automatic commits

Automatic pushes

Automatic file editing

Desktop automation

Internet search

------------------------------------------------------------

IMPLEMENT

ProjectScanner

RepositoryAnalyzer

SourceCodeReader

LanguageDetector

DependencyReader

ErrorAnalyzer

StackTraceParser

RepositorySummary

DocumentationReader

GitRepositoryManager

GitStatusReader

GitHistoryReader

GitDiffReader

------------------------------------------------------------

SUPPORTED LANGUAGES

Python

Java

C

C++

JavaScript

TypeScript

HTML

CSS

JSON

YAML

Markdown

XML

Shell

SQL

------------------------------------------------------------

PROJECT DETECTION

Automatically detect

Git repositories

Python projects

Java projects

Node projects

CMake

Gradle

Maven

Flask

FastAPI

Django

React

Vue

Angular

Rust (basic)

Go (basic)

------------------------------------------------------------

DEPENDENCY FILES

Read

requirements.txt

pyproject.toml

package.json

pom.xml

build.gradle

Cargo.toml

go.mod

CMakeLists.txt

------------------------------------------------------------

SOURCE ANALYSIS

Support

Read source files

Locate functions

Locate classes

Locate methods

Locate imports

Locate TODO comments

Locate FIXME comments

Search symbols

Summarize source files

Summarize entire repositories

------------------------------------------------------------

ERROR ANALYSIS

Understand

Python Tracebacks

Java Exceptions

Compilation errors

Import errors

Module errors

Dependency errors

Syntax errors

Runtime errors

Explain them in plain English.

Never invent fixes.

------------------------------------------------------------

STACK TRACE PARSING

Extract

File

Line

Column

Function

Message

Root cause

Related files

------------------------------------------------------------

README SUPPORT

Read README

Summarize

Extract setup instructions

Extract project purpose

Extract dependencies

------------------------------------------------------------

GIT

Support

Status

Branches

Current branch

Recent commits

Commit history

Diff

Changed files

Untracked files

Ignored files

Repository root

Never modify Git history.

Never commit.

Never push.

Never pull.

------------------------------------------------------------

TOOLS

Implement

ProjectSummaryTool

RepositorySummaryTool

CodeSearchTool

FunctionSearchTool

ClassSearchTool

DependencyTool

StackTraceTool

GitStatusTool

GitHistoryTool

GitDiffTool

ReadmeTool

TodoTool

LanguageDetectorTool

Everything must integrate into the Tool Engine.

------------------------------------------------------------

CLI

Implement

/project

/project summary

/git status

/git history

/git diff

/readme

/todos

/search code

/search function

/search class

/explain error

------------------------------------------------------------

CONFIGURATION

Allow configuring

Ignored folders

Ignored languages

Maximum repository size

Maximum file size

Maximum files analyzed

Git history depth

------------------------------------------------------------

LOGGING

Log

Repository scanned

Files analyzed

Language detected

Git commands

Execution time

Errors

------------------------------------------------------------

TESTING

Create tests for

Repository detection

Language detection

Dependency readers

Git readers

README parsing

Stack trace parser

Project summary

Tool integration

Tests must pass.

------------------------------------------------------------

DOCUMENTATION

Update README.

Document

Supported languages

Git support

Repository analysis

Error analysis

Stack trace analysis

Configuration

------------------------------------------------------------

SELF CHECK

Before finishing verify

✓ Project detection works

✓ Git reading works

✓ README parsing works

✓ Dependency reading works

✓ Stack trace parsing works

✓ Tool integration complete

✓ CLI operational

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

git commit -m "Implement coding and Git assistant"

If Git cannot be executed automatically,

provide the exact commands.

------------------------------------------------------------

SUCCESS CRITERIA

✓ Repository analysis operational

✓ Programming language detection operational

✓ Git inspection operational

✓ Error explanation operational

✓ Tool Engine integration complete

✓ CLI operational

✓ Tests pass

✓ Project builds successfully

Do NOT continue to the next phase.