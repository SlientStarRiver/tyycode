"""Code search tool - grep/ripgrep integration."""

from __future__ import annotations

import asyncio
import shutil
from typing import Any

from tyycode.tools import register
from tyycode.tools.base import Tool


class SearchTool(Tool):
    """Search code using grep or ripgrep."""

    @property
    def name(self) -> str:
        return "search"

    @property
    def description(self) -> str:
        return "Search for a pattern in files using grep/ripgrep. Returns matching lines with file paths and line numbers."

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Search pattern (regex supported)",
                },
                "path": {
                    "type": "string",
                    "description": "Directory or file to search in (default: current directory)",
                },
                "glob": {
                    "type": "string",
                    "description": "File glob pattern to filter (e.g. '*.py')",
                },
            },
            "required": ["pattern"],
        }

    async def execute(self, **kwargs: Any) -> str:
        pattern = kwargs["pattern"]
        path = kwargs.get("path", ".")
        glob_pattern = kwargs.get("glob")

        # Prefer ripgrep if available
        if shutil.which("rg"):
            return await self._search_with_rg(pattern, path, glob_pattern)
        return await self._search_with_grep(pattern, path, glob_pattern)

    async def _search_with_rg(self, pattern: str, path: str, glob: str | None) -> str:
        cmd = ["rg", "--line-number", "--no-heading", "--color=never"]
        if glob:
            cmd.extend(["--glob", glob])
        cmd.extend([pattern, path])

        return await self._run(cmd, timeout=30)

    async def _search_with_grep(self, pattern: str, path: str, glob: str | None) -> str:
        cmd = ["grep", "-rn", "--color=never"]
        if glob:
            cmd.extend(["--include", glob])
        cmd.extend([pattern, path])

        return await self._run(cmd, timeout=30)

    async def _run(self, cmd: list[str], timeout: int) -> str:
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                proc.kill()
                return "Error: Search timed out"

            output = stdout.decode("utf-8", errors="replace").rstrip()
            error = stderr.decode("utf-8", errors="replace").rstrip()

            if proc.returncode == 1:  # grep returns 1 when no matches
                return "No matches found."
            if proc.returncode != 0:
                return f"Search error: {error}" if error else "Search failed."

            # Limit output to 200 lines
            lines = output.splitlines()
            if len(lines) > 200:
                return "\n".join(lines[:200]) + f"\n... ({len(lines) - 200} more matches)"
            return output

        except FileNotFoundError:
            return "Error: Neither 'rg' (ripgrep) nor 'grep' found. Install ripgrep for better search."
        except Exception as e:
            return f"Error: {e}"


register(SearchTool())
