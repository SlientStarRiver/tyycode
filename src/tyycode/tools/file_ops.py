"""File operation tools - read, write, list directory."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tyycode.tools import register
from tyycode.tools.base import Tool


class ReadFileTool(Tool):
    """Read file contents."""

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Read the contents of a file at the given path."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path to read",
                },
                "offset": {
                    "type": "integer",
                    "description": "Line number to start from (0-based)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max lines to read (default: all)",
                },
            },
            "required": ["path"],
        }

    async def execute(self, **kwargs: Any) -> str:
        path = Path(kwargs["path"]).resolve()
        offset = kwargs.get("offset", 0)
        limit = kwargs.get("limit")

        if not path.exists():
            return f"Error: File not found: {path}"
        if not path.is_file():
            return f"Error: Not a file: {path}"

        try:
            lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
            if offset:
                lines = lines[offset:]
            if limit:
                lines = lines[:limit]

            numbered = []
            for i, line in enumerate(lines, start=offset + 1):
                numbered.append(f"{i:4d}\t{line.rstrip()}")
            return "\n".join(numbered)
        except Exception as e:
            return f"Error reading file: {e}"


class WriteFileTool(Tool):
    """Write content to a file."""

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return "Write content to a file. Creates parent directories if needed."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path to write",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write",
                },
            },
            "required": ["path", "content"],
        }

    async def execute(self, **kwargs: Any) -> str:
        path = Path(kwargs["path"]).resolve()
        content = kwargs["content"]

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return f"Wrote {len(content)} bytes to {path}"
        except Exception as e:
            return f"Error writing file: {e}"


class ListDirectoryTool(Tool):
    """List directory contents."""

    @property
    def name(self) -> str:
        return "list_directory"

    @property
    def description(self) -> str:
        return "List files and directories at the given path."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to list",
                },
            },
            "required": ["path"],
        }

    async def execute(self, **kwargs: Any) -> str:
        path = Path(kwargs["path"]).resolve()

        if not path.exists():
            return f"Error: Path not found: {path}"
        if not path.is_dir():
            return f"Error: Not a directory: {path}"

        try:
            entries = []
            for item in sorted(path.iterdir()):
                prefix = "[dir] " if item.is_dir() else "[file]"
                entries.append(f"{prefix} {item.name}")
            return "\n".join(entries) if entries else "(empty directory)"
        except Exception as e:
            return f"Error listing directory: {e}"


# Auto-register
register(ReadFileTool())
register(WriteFileTool())
register(ListDirectoryTool())
