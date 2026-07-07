"""Compiler error and stack trace parsing."""

from __future__ import annotations

import re
from typing import Any


class StackTraceParser:
    """Parse common stack traces into structured frames."""

    PYTHON_FRAME = re.compile(r'File "([^"]+)", line (\d+), in ([^\n]+)')
    JAVA_FRAME = re.compile(r"\s*at\s+(.+)\(([^:]+):(\d+)\)")
    GCC_FRAME = re.compile(r"([^:\n]+):(\d+):(?:(\d+):)?\s*(error|warning):\s*(.+)")

    def parse(self, text: str) -> dict[str, Any]:
        """Extract frames, message, and likely root cause."""
        frames = []
        for match in self.PYTHON_FRAME.finditer(text):
            frames.append({"file": match.group(1), "line": int(match.group(2)), "function": match.group(3)})
        for match in self.JAVA_FRAME.finditer(text):
            frames.append({"function": match.group(1), "file": match.group(2), "line": int(match.group(3))})
        for match in self.GCC_FRAME.finditer(text):
            frames.append(
                {
                    "file": match.group(1),
                    "line": int(match.group(2)),
                    "column": int(match.group(3) or 0),
                    "severity": match.group(4),
                    "message": match.group(5),
                }
            )
        message = self._message(text)
        return {
            "frames": frames,
            "message": message,
            "root_cause": message,
            "related_files": sorted({str(frame.get("file")) for frame in frames if frame.get("file")}),
        }

    def _message(self, text: str) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return ""
        for line in reversed(lines):
            if re.search(r"(Error|Exception|Traceback|error:|warning:)", line):
                return line
        return lines[-1]


class ErrorAnalyzer:
    """Explain common errors without inventing code changes."""

    def __init__(self) -> None:
        self.parser = StackTraceParser()

    def analyze(self, text: str) -> dict[str, Any]:
        """Return structured parsing plus a plain-English explanation."""
        parsed = self.parser.parse(text)
        message = parsed["message"]
        explanation = "The error output points to the reported message."
        if "ModuleNotFoundError" in message or "ImportError" in message:
            explanation = "Python could not import a required module."
        elif "SyntaxError" in message or "error:" in message:
            explanation = "The compiler or interpreter found invalid syntax or invalid source code."
        elif "Exception" in message:
            explanation = "The program raised a runtime exception."
        parsed["explanation"] = explanation
        return parsed
