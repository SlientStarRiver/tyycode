"""Context management - conversation history, token counting, truncation via summary."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Rough estimate: 1 token ~ 4 chars for English, ~2 chars for CJK
_CHARS_PER_TOKEN = 3

_SYSTEM_PROMPT = """You are TyyCode, a terminal CLI agent. You help users with coding tasks.

You have access to tools for file operations, shell commands, and code search.
Always explain what you're about to do before calling a tool.
Be concise and direct."""


def _estimate_tokens(text: str) -> int:
    """Rough token count estimate."""
    return len(text) // _CHARS_PER_TOKEN


class ConversationContext:
    """Manages conversation history with token budget control."""

    def __init__(self, max_tokens: int = 80000) -> None:
        self._messages: list[dict[str, Any]] = []
        self._max_tokens = max_tokens
        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0

    @property
    def messages(self) -> list[dict[str, Any]]:
        return list(self._messages)

    @property
    def token_usage(self) -> dict[str, int]:
        return {
            "prompt": self._total_prompt_tokens,
            "completion": self._total_completion_tokens,
            "total": self._total_prompt_tokens + self._total_completion_tokens,
        }

    def add_user_message(self, content: str) -> None:
        self._messages.append({"role": "user", "content": content})

    def add_assistant_message(
        self,
        content: str | None = None,
        tool_calls: list[dict] | None = None,
    ) -> None:
        msg: dict[str, Any] = {"role": "assistant", "content": content or ""}
        if tool_calls:
            msg["tool_calls"] = tool_calls
            msg["content"] = content or None
        self._messages.append(msg)

    def add_tool_result(self, tool_call_id: str, content: str) -> None:
        self._messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content,
        })

    def record_usage(self, prompt_tokens: int, completion_tokens: int) -> None:
        self._total_prompt_tokens += prompt_tokens
        self._total_completion_tokens += completion_tokens

    def get_llm_messages(self) -> list[dict[str, Any]]:
        """Build message list for LLM call, with system prompt and truncation."""
        system = {"role": "system", "content": _SYSTEM_PROMPT}
        messages = self._messages

        # Check if we need to truncate
        total_text = json.dumps(messages)
        estimated = _estimate_tokens(total_text)

        if estimated > self._max_tokens:
            messages = self._truncate(messages, estimated)

        return [system] + messages

    def _truncate(
        self,
        messages: list[dict[str, Any]],
        current_tokens: int,
    ) -> list[dict[str, Any]]:
        """Keep system + recent messages, summarize middle."""
        if len(messages) <= 4:
            return messages

        # Keep last 6 messages, summarize the rest
        keep_count = 6
        recent = messages[-keep_count:]
        old = messages[:-keep_count]

        # Build a simple summary of old messages
        summary_parts = []
        for msg in old:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if content:
                preview = content[:100] + "..." if len(content) > 100 else content
                summary_parts.append(f"[{role}]: {preview}")

        summary = "[Previous conversation summary]\n" + "\n".join(summary_parts[-10:])

        return [
            {"role": "user", "content": summary},
            {"role": "assistant", "content": "Understood, continuing."},
            *recent,
        ]

    def save(self, session_dir: Path, session_id: str) -> Path:
        """Save session to JSON file."""
        session_dir.mkdir(parents=True, exist_ok=True)
        path = session_dir / f"{session_id}.json"
        data = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "messages": self._messages,
            "token_usage": self.token_usage,
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    @classmethod
    def load(cls, path: Path) -> ConversationContext:
        """Load session from JSON file."""
        data = json.loads(path.read_text(encoding="utf-8"))
        ctx = cls()
        ctx._messages = data.get("messages", [])
        usage = data.get("token_usage", {})
        ctx._total_prompt_tokens = usage.get("prompt", 0)
        ctx._total_completion_tokens = usage.get("completion", 0)
        return ctx
