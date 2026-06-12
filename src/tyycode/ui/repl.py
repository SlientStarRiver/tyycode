"""REPL interaction - prompt_toolkit based input loop."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.history import FileHistory

from tyycode.core.agent import Agent
from tyycode.ui import display

_HISTORY_FILE = Path.home() / ".tyycode" / "history"


def _create_session() -> PromptSession:
    """Create prompt session with history."""
    _HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    return PromptSession(
        history=FileHistory(str(_HISTORY_FILE)),
        auto_suggest=AutoSuggestFromHistory(),
    )


def _process_events(agent: Agent, user_input: str) -> None:
    """Run agent and process events synchronously."""
    buffer = ""

    async def _consume() -> None:
        nonlocal buffer
        async for event in agent.run(user_input):
            etype = event["type"]
            content = event["content"]

            if etype == "text":
                buffer += content
            elif etype == "tool_start":
                if buffer:
                    display.print_text(buffer)
                    buffer = ""
                display.print_tool_start(content["name"], content["arguments"])
            elif etype == "tool_end":
                display.print_tool_end(content["name"], content["result"])
            elif etype == "error":
                if buffer:
                    display.print_text(buffer)
                    buffer = ""
                display.print_error(content)
            elif etype == "done":
                if buffer:
                    display.print_text(buffer)
                    buffer = ""

    asyncio.run(_consume())


def run_repl(agent: Agent) -> None:
    """Run the interactive REPL loop."""
    display.print_logo("0.1.0", agent._llm.provider_name)

    # Check if stdin is interactive (TTY)
    is_tty = sys.stdin.isatty()
    session = _create_session() if is_tty else None

    while True:
        try:
            if is_tty:
                user_input = session.prompt(ANSI(display.print_user_prompt()))  # type: ignore[union-attr]
            else:
                # Piped input: read line by line
                line = sys.stdin.readline()
                if not line:  # EOF
                    break
                user_input = line
        except (EOFError, KeyboardInterrupt):
            display.print_success("\nBye!")
            break

        user_input = user_input.strip()
        if not user_input:
            continue

        # Handle commands
        if user_input.startswith("/"):
            if user_input in ("/quit", "/exit"):
                display.print_success("Bye!")
                break
            elif user_input == "/help":
                _print_help()
                continue
            elif user_input == "/clear":
                print("\033[2J\033[H", end="")  # ANSI clear screen
                continue
            elif user_input == "/usage":
                display.print_token_usage(agent.token_usage)
                continue
            elif user_input == "/save":
                session_dir = Path.home() / ".tyycode" / "sessions"
                from datetime import datetime
                sid = datetime.now().strftime("%Y%m%d_%H%M%S")
                path = agent._context.save(session_dir, sid)
                display.print_success(f"Session saved: {path}")
                continue
            else:
                display.print_warning(f"Unknown command: {user_input}")
                continue

        # Process with agent
        _process_events(agent, user_input)

        # Show token usage
        display.print_token_usage(agent.token_usage)


def _print_help() -> None:
    """Print help message."""
    display.console.print("""
[bold cyan]TyyCode Commands[/]

  /help      Show this help
  /quit      Exit TyyCode
  /clear     Clear screen
  /usage     Show token usage
  /save      Save current session

Type your message to chat with the LLM.
Tools are called automatically when needed.
""")
