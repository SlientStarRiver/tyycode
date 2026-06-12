"""Agent main loop - orchestrates LLM calls and tool execution."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any

from tyycode.core.context import ConversationContext
from tyycode.core.llm import LLMClient
from tyycode.tools import get_tool, get_tool_definitions

logger = logging.getLogger(__name__)


class Agent:
    """Main agent loop."""

    def __init__(self, llm: LLMClient, max_tokens: int = 100000) -> None:
        self._llm = llm
        self._context = ConversationContext(max_tokens=max_tokens)

    @property
    def token_usage(self) -> dict[str, int]:
        return self._context.token_usage

    async def run(self, user_input: str) -> AsyncIterator[dict[str, Any]]:
        """Process user input, yield events for UI rendering.

        Yields dicts with keys:
          - type: "text" | "tool_start" | "tool_end" | "error" | "done"
          - content: str or dict
        """
        self._context.add_user_message(user_input)

        tools = get_tool_definitions()
        messages = self._context.get_llm_messages()

        # Collect streaming response
        full_text = ""
        tool_calls: list[dict[str, Any]] = []
        current_tool_calls: dict[int, dict] = {}

        tool_defs = tools if tools else None
        async for event in self._llm.chat_stream(messages, tools=tool_defs):
            if event["type"] == "text_delta":
                full_text += event["content"]
                yield {"type": "text", "content": event["content"]}

            elif event["type"] == "tool_call":
                tc = event["content"]
                idx = tc["index"]
                if idx not in current_tool_calls:
                    current_tool_calls[idx] = {
                        "id": tc["id"] or "",
                        "name": tc["name"] or "",
                        "arguments": "",
                    }
                else:
                    if tc["id"]:
                        current_tool_calls[idx]["id"] = tc["id"]
                    if tc["name"]:
                        current_tool_calls[idx]["name"] = tc["name"]

                current_tool_calls[idx]["arguments"] += tc["arguments"] or ""

            elif event["type"] == "usage":
                usage = event["content"]
                self._context.record_usage(
                    usage["prompt_tokens"],
                    usage["completion_tokens"],
                )

            elif event["type"] == "error":
                yield {"type": "error", "content": event["content"]}

        # Process tool calls if any
        if current_tool_calls:
            tool_calls = list(current_tool_calls.values())
            # Save assistant message with tool calls
            self._context.add_assistant_message(
                content=full_text or None,
                tool_calls=[
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {"name": tc["name"], "arguments": tc["arguments"]}
                    }
                    for tc in tool_calls
                ],
            )

            # Execute each tool
            for tc in tool_calls:
                name = tc["name"]
                args_str = tc["arguments"]
                call_id = tc["id"]

                yield {
                    "type": "tool_start",
                    "content": {"name": name, "arguments": args_str},
                }

                tool = get_tool(name)
                if not tool:
                    result = f"Error: Unknown tool '{name}'"
                else:
                    try:
                        import json
                        args = json.loads(args_str) if args_str else {}
                        result = await tool.execute(**args)
                    except Exception as e:
                        result = f"Error executing {name}: {e}"

                yield {"type": "tool_end", "content": {"name": name, "result": result}}
                self._context.add_tool_result(call_id, str(result))

            # After tool execution, call LLM again with results
            async for event in self.run(""):
                yield event
        else:
            # No tool calls, save text response
            self._context.add_assistant_message(content=full_text)

        yield {"type": "done", "content": ""}
