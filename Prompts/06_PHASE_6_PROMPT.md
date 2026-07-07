# ============================================================
# PHASE 6 — LINUX DIAGNOSTICS ENGINE
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

Use the existing virtual environment for testing.

------------------------------------------------------------

ROLE

You are a Senior Python Software Architect.

Continue extending the project.

Everything must integrate into the Tool Engine.

Never bypass existing abstractions.

------------------------------------------------------------

GOAL

Implement a Linux Diagnostics Engine.

The assistant should understand the current Linux system.

It should inspect the machine and explain the results.

It should NEVER modify the operating system.

This phase is READ-ONLY.

------------------------------------------------------------

DO NOT IMPLEMENT

Git

Coding Assistant

Memory

Filesystem

Desktop Automation

Networking tools that modify configuration

Package installation

Anything destructive

------------------------------------------------------------

IMPLEMENT

DiagnosticsManager

SystemInfoCollector

HardwareCollector

ProcessCollector

DiskCollector

MemoryCollector

CPUCollector

GPUCollector

BatteryCollector

ServiceCollector

JournalReader

KernelCollector

TemperatureCollector

NetworkInfoCollector

------------------------------------------------------------

SYSTEM INFORMATION

Collect

Hostname

Kernel

Distribution

Desktop Environment

Window Manager

Architecture

Current User

Current Shell

Python Version

------------------------------------------------------------

CPU

Collect

Model

Logical Cores

Physical Cores

Frequency

Usage

Load Average

Temperature (if available)

------------------------------------------------------------

RAM

Collect

Installed

Used

Available

Cached

Buffers

Swap

Huge Pages if available

------------------------------------------------------------

DISK

Collect

Mounted drives

Filesystem

Usage

Read/Write statistics if available

SSD detection

NVMe detection

------------------------------------------------------------

BATTERY

Collect

Percentage

Charging

Health

Cycles if available

Remaining Time

------------------------------------------------------------

GPU

Collect

Vendor

Driver

Memory (if available)

Renderer

------------------------------------------------------------

USB

Collect

Connected devices

Vendor

Product

------------------------------------------------------------

PCI

Collect

PCI devices

------------------------------------------------------------

PROCESSES

Collect

Running processes

Top CPU

Top RAM

Zombie processes

Orphan processes if detectable

------------------------------------------------------------

SERVICES

Support reading

systemctl status

List active services

List failed services

Never restart services.

Never stop services.

------------------------------------------------------------

JOURNAL

Support reading

journalctl

Recent boot logs

Recent errors

Filtering

Search

Never modify logs.

------------------------------------------------------------

KERNEL

Collect

Version

Modules

Boot Time

------------------------------------------------------------

NETWORK INFORMATION

Collect only

Hostname

Interfaces

IP addresses

MAC addresses

Gateway

DNS

Do NOT modify network configuration.

------------------------------------------------------------

TOOLS

Implement

SystemInfoTool

CPUInfoTool

MemoryInfoTool

DiskInfoTool

BatteryInfoTool

GPUInfoTool

USBTool

PCITool

ProcessTool

ServiceTool

JournalTool

KernelTool

NetworkInfoTool

Everything must integrate into Tool Engine.

------------------------------------------------------------

CLI

Implement

/system

/cpu

/memory

/disk

/processes

/services

/kernel

/network

/hardware

------------------------------------------------------------

ANALYSIS

The assistant should summarize collected information.

Example

High memory usage

Disk nearly full

Battery health poor

CPU temperature high

Too many failed services

The assistant explains findings but NEVER changes the system.

------------------------------------------------------------

CONFIGURATION

Allow configuring

Maximum processes returned

Journal size

Timeouts

Ignored services

Ignored devices

------------------------------------------------------------

LOGGING

Log

Execution

Collection time

Failures

Permission issues

Timeouts

------------------------------------------------------------

TESTING

Create tests for

Collectors

Parsers

Timeouts

Errors

System summaries

Tool integration

Tests must pass.

------------------------------------------------------------

DOCUMENTATION

Update README.

Document

Supported diagnostics

Safety model

Collected information

CLI commands

Configuration

------------------------------------------------------------

SELF CHECK

Before finishing verify

✓ System information works

✓ CPU works

✓ RAM works

✓ Disk works

✓ Battery works

✓ GPU works

✓ USB works

✓ Services work

✓ Journal reading works

✓ Tool Engine integration complete

✓ Tests pass

✓ Documentation updated

✓ No placeholder code

✓ No TODO comments

------------------------------------------------------------

OUTPUT

Return only

Files created

Files modified

Reason for each modification

Known issues

------------------------------------------------------------

GIT

When implementation is complete execute

git add .

git commit -m "Implement Linux diagnostics engine"

If Git cannot be executed automatically,

provide the exact commands.

------------------------------------------------------------

SUCCESS CRITERIA

✓ Diagnostics Engine operational

✓ Read-only safety preserved

✓ Tool Engine integration complete

✓ CLI operational

✓ Tests pass

✓ Project builds successfully

Do NOT continue to the next phase.