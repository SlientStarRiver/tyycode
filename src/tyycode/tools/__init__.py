"""Tool registry - auto-discovers and registers all tools."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tyycode.tools.base import Tool

_registry: dict[str, Tool] = {}


def register(tool: Tool) -> None:
    """Register a tool instance."""
    _registry[tool.name] = tool


def get_tool(name: str) -> Tool | None:
    """Get a registered tool by name."""
    return _registry.get(name)


def get_all_tools() -> list[Tool]:
    """Get all registered tools."""
    return list(_registry.values())


def get_tool_definitions() -> list[dict]:
    """Get OpenAI function calling definitions for all tools."""
    return [tool.definition for tool in _registry.values()]


def _auto_register() -> None:
    """Import tool modules to trigger registration."""
    from tyycode.tools import file_ops, search, shell  # noqa: F401

_auto_register()
