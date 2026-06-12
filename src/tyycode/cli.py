"""CLI entry point - typer commands."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer

from tyycode import __version__

app = typer.Typer(
    name="tyycode",
    help="TyyCode - Terminal CLI Agent",
    add_completion=False,
)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"TyyCode v{__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(
        False, "--version", "-v",
        callback=version_callback, is_eager=True,
    ),
    ctx: typer.Context = None,  # type: ignore[assignment]
) -> None:
    """TyyCode - Terminal CLI Agent."""
    if ctx and ctx.invoked_subcommand is None:
        _start_chat(None, None, None)


def _start_chat(
    provider: str | None,
    config: Path | None,
    resume: str | None,
) -> None:
    """Shared chat startup logic."""
    from tyycode.core.agent import Agent
    from tyycode.core.config import load_config
    from tyycode.core.context import ConversationContext
    from tyycode.core.llm import LLMClient
    from tyycode.ui.display import print_error
    from tyycode.ui.repl import run_repl

    try:
        cfg = load_config(config)
        provider_config = cfg.get_provider(provider)
        llm = LLMClient(provider_config)

        if resume:
            session_path = Path.home() / ".tyycode" / "sessions" / f"{resume}.json"
            if not session_path.exists():
                print_error(f"Session not found: {session_path}")
                raise typer.Exit(1)
            ctx = ConversationContext.load(session_path)
            agent = Agent(llm, max_tokens=cfg.max_tokens_per_session)
            agent._context = ctx
        else:
            agent = Agent(llm, max_tokens=cfg.max_tokens_per_session)

        run_repl(agent)

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except KeyboardInterrupt:
        pass


@app.command()
def chat(
    provider: str = typer.Option(None, "--provider", "-p", help="LLM provider name"),
    config: Path = typer.Option(None, "--config", "-c", help="Config file path"),
    resume: str = typer.Option(None, "--resume", "-r", help="Resume session by ID"),
) -> None:
    """Start interactive chat."""
    _start_chat(provider, config, resume)


@app.command()
def sessions() -> None:
    """List saved sessions."""
    from tyycode.ui.display import console

    session_dir = Path.home() / ".tyycode" / "sessions"
    if not session_dir.exists():
        console.print("[dim]No saved sessions.[/dim]")
        return

    files = sorted(session_dir.glob("*.json"), reverse=True)
    if not files:
        console.print("[dim]No saved sessions.[/dim]")
        return

    for f in files[:20]:
        name = f.stem
        size = f.stat().st_size
        console.print(f"  {name}  [dim]({size:,} bytes)[/dim]")


@app.command()
def run(
    prompt: str = typer.Argument(..., help="Single prompt to execute"),
    provider: str = typer.Option(None, "--provider", "-p", help="LLM provider name"),
    config: Path = typer.Option(None, "--config", "-c", help="Config file path"),
) -> None:
    """Run a single prompt (non-interactive)."""
    from tyycode.core.agent import Agent
    from tyycode.core.config import load_config
    from tyycode.core.llm import LLMClient
    from tyycode.ui.display import print_error, print_text

    async def _run() -> None:
        cfg = load_config(config)
        provider_config = cfg.get_provider(provider)
        llm = LLMClient(provider_config)
        agent = Agent(llm, max_tokens=cfg.max_tokens_per_session)

        buffer = ""
        async for event in agent.run(prompt):
            if event["type"] == "text":
                buffer += event["content"]
            elif event["type"] == "error":
                if buffer:
                    print_text(buffer)
                    buffer = ""
                print_error(event["content"])
            elif event["type"] == "done":
                if buffer:
                    print_text(buffer)

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        pass
