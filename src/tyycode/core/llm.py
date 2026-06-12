"""LLM client - wraps openai SDK with streaming, retry, and multi-provider support."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

from openai import APIError, APITimeoutError, AsyncOpenAI, RateLimitError

from tyycode.core.config import ProviderConfig

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 1.0


class LLMClient:
    """Async LLM client with retry and fallback."""

    def __init__(self, provider: ProviderConfig) -> None:
        self._provider = provider
        self._client = AsyncOpenAI(
            api_key=provider.api_key,
            base_url=provider.base_url,
            timeout=60.0,
        )
        self._model = provider.model

    @property
    def provider_name(self) -> str:
        return self._provider.name

    async def chat_stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream chat completion, yielding token deltas and tool calls.

        Yields dicts with keys:
          - type: "text_delta" | "tool_call" | "error" | "usage"
          - content: str (for text_delta), dict (for tool_call), or error message
        """
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        for attempt in range(_MAX_RETRIES):
            try:
                stream = await self._client.chat.completions.create(**kwargs)

                async for chunk in stream:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if not delta:
                        continue

                    if delta.content:
                        yield {"type": "text_delta", "content": delta.content}

                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            yield {
                                "type": "tool_call",
                                "content": {
                                    "index": tc.index,
                                    "id": tc.id,
                                    "name": tc.function.name if tc.function else None,
                                    "arguments": tc.function.arguments if tc.function else "",
                                },
                            }

                    choice = chunk.choices[0] if chunk.choices else None
                    if choice and choice.finish_reason == "stop":
                        if chunk.usage:
                            yield {
                                "type": "usage",
                                "content": {
                                    "prompt_tokens": chunk.usage.prompt_tokens,
                                    "completion_tokens": chunk.usage.completion_tokens,
                                },
                            }

                return  # success, exit retry loop

            except RateLimitError as e:
                delay = _RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning("Rate limited, retrying in %.1fs: %s", delay, e)
                msg = f"Rate limited, retrying ({attempt + 1}/{_MAX_RETRIES})..."
                yield {"type": "error", "content": msg}
                await asyncio.sleep(delay)

            except APITimeoutError as e:
                delay = _RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning("Timeout, retrying in %.1fs: %s", delay, e)
                msg = f"Timeout, retrying ({attempt + 1}/{_MAX_RETRIES})..."
                yield {"type": "error", "content": msg}
                await asyncio.sleep(delay)

            except APIError as e:
                logger.error("API error: %s", e)
                yield {"type": "error", "content": f"API error: {e.message}"}
                return

            except Exception as e:
                logger.error("Unexpected error: %s", e)
                yield {"type": "error", "content": f"Error: {e}"}
                return

        yield {"type": "error", "content": f"Failed after {_MAX_RETRIES} retries"}
