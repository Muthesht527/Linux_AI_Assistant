# Installation

Linux AI Assistant is a local Python application for Linux desktops.

## Requirements

- Python 3.12 or newer
- Ollama for local model inference
- A Linux distribution such as Ubuntu, Kubuntu, Linux Mint, or Debian

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
```

## Verify

```bash
python3 main.py doctor
python3 main.py info
python3 -m pytest
python3 -m compileall assistant main.py
```

## Ollama

Install Ollama from the official local package for your distribution, start it,
and pull a supported model:

```bash
ollama serve
ollama pull qwen3
```

The assistant does not require cloud inference or external APIs.
