"""Tool base class - all tools inherit from this."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    """Abstract base class for all tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool name for function calling."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description for LLM."""
        ...

    @property
    @abstractmethod
    def parameters_schema(self) -> dict[str, Any]:
        """JSON Schema for tool parameters."""
        ...

    @property
    def definition(self) -> dict[str, Any]:
        """OpenAI function calling definition."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema,
            },
        }

    @abstractmethod
    async def execute(self, **kwargs: Any) -> str:
        """Execute the tool with given arguments. Returns result as string."""
        ...
