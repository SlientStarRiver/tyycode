"""Shell command execution tool."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

from tyycode.tools import register
from tyycode.tools.base import Tool

logger = logging.getLogger(__name__)

_DANGEROUS_PATTERNS = [
    r"\brm\s+(-[a-zA-Z]*f|--force)\b",
    r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f\b",
    r"\brm\s+-[a-zA-Z]*f[a-zA-Z]*r\b",
    r"\bsudo\b",
    r"\bmkfs\b",
    r"\bdd\b.*of=/dev/",
    r"[:]%(){ .:|:& };:",  # fork bomb
]


def _is_dangerous(command: str) -> bool:
    """Check if command matches dangerous patterns."""
    for pattern in _DANGEROUS_PATTERNS:
        if re.search(pattern, command):
            return True
    return False


class ShellTool(Tool):
    """Execute shell commands."""

    @property
    def name(self) -> str:
        return "shell"

    @property
    def description(self) -> str:
        return "Execute a shell command and return its output. Dangerous commands (rm -rf, sudo) require confirmation."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 30)",
                },
            },
            "required": ["command"],
        }

    async def execute(self, **kwargs: Any) -> str:
        command = kwargs["command"]
        timeout = kwargs.get("timeout", 30)

        if _is_dangerous(command):
            return f"DANGEROUS_COMMAND: This command requires user confirmation: {command}"

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                proc.kill()
                return f"Error: Command timed out after {timeout}s"

            output = stdout.decode("utf-8", errors="replace")
            error = stderr.decode("utf-8", errors="replace")

            parts = []
            if output:
                parts.append(output.rstrip())
            if error:
                parts.append(f"[stderr]\n{error.rstrip()}")
            if proc.returncode != 0:
                parts.append(f"[exit code: {proc.returncode}]")

            return "\n".join(parts) if parts else "(no output)"

        except Exception as e:
            return f"Error executing command: {e}"


register(ShellTool())
