# ============================================================
# PHASE 2 — OLLAMA & CONVERSATION ENGINE
# Linux AI Assistant
# ============================================================

IMPORTANT

Read and strictly follow 00_MASTER_SPEC.md before making any changes.

DO NOT audit the entire repository.

DO NOT regenerate working code.

DO NOT rewrite architecture.

DO NOT rename files unless absolutely necessary.

Inspect ONLY the files required for this phase.

Reuse existing code whenever possible.

Modify the minimum number of files required.

Keep token usage low.

------------------------------------------------------------

ROLE

You are a Senior Python Software Architect.

You are extending an existing production-quality project.

Think before making modifications.

Never replace working implementations.

------------------------------------------------------------

GOAL

Implement the AI conversation layer using Ollama.

At the end of this phase the assistant should be able to

• Detect installed Ollama models
• Select a model
• Chat with the selected model
• Stream responses
• Maintain conversation history
• Gracefully recover from errors
• Operate completely locally

DO NOT implement tool calling.

DO NOT implement filesystem access.

DO NOT implement terminal commands.

This phase is ONLY responsible for conversation.

------------------------------------------------------------

FIRST

Inspect the existing project.

Determine which modules already exist.

Reuse everything possible.

Only create missing components.

------------------------------------------------------------

IMPLEMENT

Conversation Manager

Ollama Client

Model Manager

Chat Session Manager

Streaming Response Handler

Prompt Builder

Message History

Conversation Context

Token Usage Tracking (local estimates if available)

Configuration Integration

------------------------------------------------------------

OLLAMA

Support local Ollama only.

Never use cloud APIs.

Never require API keys.

Detect whether Ollama is installed.

If missing,

display a friendly message explaining how to install it.

Detect whether the Ollama service is running.

If not,

guide the user to start it.

------------------------------------------------------------

MODEL DISCOVERY

Automatically detect installed models.

Support commands

/models

/model

/model list

/model current

/model switch <name>

Display installed models in a Rich table.

------------------------------------------------------------

CHAT

Support

single-line prompts

multi-line prompts

streaming output

conversation history

conversation reset

clear history

exit

------------------------------------------------------------

STREAMING

Responses must stream token-by-token when possible.

Do not wait for the entire response before displaying.

Use Rich live rendering where appropriate.

------------------------------------------------------------

CONTEXT

Maintain chat history.

Implement configurable history length.

Allow history to be disabled.

History should survive during the session.

Persistent memory is NOT implemented yet.

------------------------------------------------------------

SYSTEM PROMPT

Load the system prompt from configuration.

Never hardcode it.

Allow future modification without code changes.

------------------------------------------------------------

ERROR HANDLING

Handle

Ollama not installed

No models installed

Model missing

Model loading failure

Timeouts

Connection failures

Unexpected API responses

Never crash.

Always produce helpful errors.

------------------------------------------------------------

CONFIGURATION

Allow configuring

default model

temperature

top_p

context size

max history

streaming enabled

request timeout

All values must come from configuration.

------------------------------------------------------------

COMMANDS

Implement

/help

/model

/models

/history

/clear

/exit

/version

These commands must integrate with the CLI from Phase 1.

------------------------------------------------------------

CODE STYLE

Python 3.12+

PEP8

Type hints

Google docstrings

Pathlib where appropriate

No duplicated code

No circular imports

Maximum approximately 500 lines per file.

Split modules when needed.

------------------------------------------------------------

TESTING

Create tests for

Model discovery

Configuration loading

Conversation manager

Streaming handler

History management

Error handling

Ensure tests pass.

------------------------------------------------------------

DOCUMENTATION

Update

README.md

Document

Installing Ollama

Installing models

Selecting models

Starting the assistant

Changing the default model

Troubleshooting

------------------------------------------------------------

SELF CHECK

Before finishing verify

✓ Ollama detection works

✓ Model discovery works

✓ Streaming works

✓ Conversation works

✓ Commands work

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

Reason for each modification

Known issues (if any)

------------------------------------------------------------

GIT

When complete execute

git add .

git commit -m "Add Ollama integration"

If Git cannot be executed automatically,

provide the exact commands.

------------------------------------------------------------

SUCCESS CRITERIA

The phase is complete only if

✓ Local Ollama works

✓ Installed models detected

✓ Model switching works

✓ Streaming responses work

✓ Conversation history works

✓ CLI commands work

✓ Tests pass

✓ Project builds successfully

If any item fails,

fix it before ending the task.

Do not continue to Tool Calling or Phase 3.