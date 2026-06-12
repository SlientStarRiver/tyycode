"""Display rendering - rich-based terminal output."""

from __future__ import annotations

import io
import sys

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner

# Force UTF-8 on Windows to avoid GBK encoding errors
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

console = Console(file=io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace"))

# ANSI color codes
_PURPLE = "\033[35m"
_CYAN = "\033[36m"
_GREEN = "\033[32m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_GRAY = "\033[90m"
_RESET = "\033[0m"

_LOGO = f"""{_PURPLE}
  ████████╗██╗   ██╗██╗   ██╗ ██████╗ ██████╗ ██████╗ ███████╗
  ╚══██╔══╝╚██╗ ██╔╝╚██╗ ██╔╝██╔════╝██╔═══██╗██╔══██╗██╔════╝
     ██║    ╚████╔╝  ╚████╔╝ ██║     ██║   ██║██║  ██║█████╗
     ██║     ╚██╔╝    ╚██╔╝  ██║     ██║   ██║██║  ██║██╔══╝
     ██║      ██║      ██║   ╚██████╗╚██████╔╝██████╔╝███████╗
     ╚═╝      ╚═╝      ╚═╝    ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝{_RESET}"""


def print_logo(version: str, provider_name: str) -> None:
    """Print startup logo with version info."""
    console.print(_LOGO)
    console.print(f"  {_GRAY}v{version} · provider: {provider_name}{_RESET}")
    console.print()


def print_user_prompt() -> str:
    """Return styled prompt string."""
    return f"{_CYAN}❯{_RESET} "


def print_text(text: str) -> None:
    """Print assistant text with markdown rendering."""
    console.print(Markdown(text))


def print_error(text: str) -> None:
    """Print error message."""
    console.print(f"{_RED}✗ {text}{_RESET}")


def print_warning(text: str) -> None:
    """Print warning message."""
    console.print(f"{_YELLOW}⚠ {text}{_RESET}")


def print_success(text: str) -> None:
    """Print success message."""
    console.print(f"{_GREEN}✓ {text}{_RESET}")


def print_tool_start(name: str, arguments: str) -> None:
    """Print tool execution start."""
    console.print(f"\n{_GRAY}[tool]{_RESET} {_CYAN}{name}{_RESET}")
    if arguments and arguments != "{}":
        # Show truncated args
        args_preview = arguments[:120] + "..." if len(arguments) > 120 else arguments
        console.print(f"  {_GRAY}{args_preview}{_RESET}")


def print_tool_end(name: str, result: str) -> None:
    """Print tool execution result."""
    if result.startswith("Error"):
        console.print(f"  {_RED}{result}{_RESET}")
    else:
        # Show first 10 lines of result
        lines = result.splitlines()
        preview = "\n".join(lines[:10])
        if len(lines) > 10:
            preview += f"\n  {_GRAY}... ({len(lines) - 10} more lines){_RESET}"
        console.print(Panel(preview, border_style="dim"))


def print_token_usage(usage: dict[str, int]) -> None:
    """Print token usage summary."""
    total = usage.get("total", 0)
    if total > 0:
        console.print(f"{_GRAY}tokens: {total:,}{_RESET}")


def create_spinner(text: str) -> Spinner:
    """Create a spinner for loading state."""
    return Spinner("dots", text=text)
