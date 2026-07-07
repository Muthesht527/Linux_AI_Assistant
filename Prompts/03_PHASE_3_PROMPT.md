# ============================================================
# PHASE 3 — TOOL ENGINE
# Linux AI Assistant
# ============================================================

IMPORTANT

Read and strictly follow 00_MASTER_SPEC.md before making any changes.

DO NOT audit the repository.

DO NOT regenerate working code.

DO NOT rewrite existing modules.

Inspect ONLY the files necessary for this phase.

Modify ONLY the minimum number of files required.

Never replace working implementations.

Never change architecture.

Keep token usage as low as possible.

------------------------------------------------------------

ROLE

You are a Senior Python Software Architect.

You are extending an existing production-quality application.

You are NOT writing a demo.

You are implementing the core Tool Engine that every future feature will use.

This phase is the FOUNDATION of the assistant.

Everything after this phase depends on it.

Think carefully before writing code.

------------------------------------------------------------

GOAL

Implement a professional Tool Engine.

The assistant must NEVER execute Python code,
terminal commands,
filesystem operations,
or Linux diagnostics directly.

Everything must happen through Tools.

The Tool Engine must become the ONLY way the assistant accesses functionality.

DO NOT implement actual filesystem searching.

DO NOT implement terminal execution.

DO NOT implement Linux tools.

DO NOT implement Git tools.

DO NOT implement Memory.

Only implement the framework.

------------------------------------------------------------

FIRST

Inspect the existing architecture.

Reuse existing modules.

Create only missing modules.

Never duplicate functionality.

------------------------------------------------------------

IMPLEMENT

Create a complete Tool Framework.

Implement

BaseTool

ToolRegistry

ToolDispatcher

PermissionManager

ToolResult

ToolContext

ToolValidator

ToolException

ToolLoader

ToolManager

ToolExecutor

------------------------------------------------------------

BASE TOOL

Every future tool must inherit BaseTool.

Every tool must expose

name

description

category

version

author

permission level

timeout

enabled

parameter schema

result schema

execute()

validate()

------------------------------------------------------------

TOOL RESULT

Every tool returns a ToolResult object.

ToolResult contains

success

message

data

execution_time

tool_name

error

warnings

metadata

No tool may return raw Python objects.

------------------------------------------------------------

TOOL REGISTRY

Implement automatic registration.

Support

register()

unregister()

reload()

find()

list()

categories()

enabled()

disabled()

Tool names must be unique.

------------------------------------------------------------

TOOL DISPATCHER

Dispatcher receives

Tool Name

Arguments

Context

Dispatcher

Validates

Checks permission

Executes

Returns ToolResult

Nothing bypasses Dispatcher.

------------------------------------------------------------

PERMISSION MANAGER

Support

SAFE

ASK

BLOCKED

Examples

Read File

SAFE

Delete File

ASK

Shutdown

BLOCKED

Dispatcher must consult PermissionManager before execution.

------------------------------------------------------------

VALIDATION

Every tool validates

Arguments

Types

Required fields

Ranges

Invalid values

Validation errors must never crash the assistant.

------------------------------------------------------------

PLUGIN SUPPORT

ToolLoader automatically discovers

plugins/

Every plugin may register tools.

No hardcoded imports.

Use dynamic discovery.

------------------------------------------------------------

TOOL CATEGORIES

Filesystem

Terminal

Git

Hardware

Network

Memory

Coding

Package Manager

Diagnostics

Utility

Categories must be extensible.

------------------------------------------------------------

CONTEXT

Create ToolContext.

Context contains

Current directory

Configuration

Logger

Conversation state

Current model

Session ID

Timestamp

Future tools receive ToolContext.

------------------------------------------------------------

ERROR HANDLING

Create

ToolException

ValidationException

PermissionException

ExecutionException

RegistrationException

Handle gracefully.

Never expose stack traces.

------------------------------------------------------------

LOGGING

Every execution logs

Tool name

Arguments

Permission level

Execution time

Success

Failure

Exception

------------------------------------------------------------

DUMMY TOOLS

Create only TWO demonstration tools.

PingTool

Returns

Assistant is alive.

VersionTool

Returns

Assistant version.

No other real tools.

------------------------------------------------------------

CLI

Implement

/tools

/tool list

/tool info

/tool categories

/tool reload

These should display information only.

------------------------------------------------------------

TESTING

Create tests for

Registry

Dispatcher

Permission Manager

Validation

Exceptions

Registration

Plugin Loader

Dummy Tools

Tests must pass.

------------------------------------------------------------

DOCUMENTATION

Document

Tool architecture

Plugin architecture

How to create a tool

How permissions work

How validation works

Provide examples.

------------------------------------------------------------

DO NOT IMPLEMENT

Filesystem

Terminal

Git

Memory

Linux Diagnostics

Clipboard

Networking

Hardware

Anything outside the framework.

------------------------------------------------------------

SELF CHECK

Before finishing verify

✓ Registry works

✓ Dispatcher works

✓ Validation works

✓ Permissions work

✓ Plugins load

✓ Dummy tools execute

✓ Tests pass

✓ Documentation updated

✓ No placeholder code

✓ No TODO comments

------------------------------------------------------------

OUTPUT

Do NOT explain every file.

Return only

Files created

Files modified

Reason for modification

Known issues (if any)

------------------------------------------------------------

GIT

When implementation is complete execute

git add .

git commit -m "Implement Tool Engine"

If Git cannot be executed automatically,

provide the exact commands.

------------------------------------------------------------

SUCCESS CRITERIA

The phase is complete only if

✓ Tool Engine fully operational

✓ Registry operational

✓ Dispatcher operational

✓ Plugin loading operational

✓ Validation operational

✓ Permissions operational

✓ CLI commands operational

✓ Tests pass

✓ Project builds successfully

If any item fails,

fix it before ending the task.

Do NOT continue to Phase 4.