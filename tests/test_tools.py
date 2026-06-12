"""Tests for tools."""

from pathlib import Path

import pytest

from tyycode.tools import get_all_tools, get_tool, get_tool_definitions
from tyycode.tools.file_ops import ListDirectoryTool, ReadFileTool, WriteFileTool
from tyycode.tools.shell import ShellTool, _is_dangerous


def test_registry_has_tools():
    tools = get_all_tools()
    names = {t.name for t in tools}
    assert "read_file" in names
    assert "write_file" in names
    assert "list_directory" in names
    assert "shell" in names
    assert "search" in names


def test_get_tool():
    tool = get_tool("read_file")
    assert tool is not None
    assert tool.name == "read_file"


def test_get_tool_definitions():
    defs = get_tool_definitions()
    assert len(defs) >= 5
    for d in defs:
        assert d["type"] == "function"
        assert "name" in d["function"]
        assert "parameters" in d["function"]


@pytest.mark.asyncio
async def test_read_file(tmp_path: Path):
    f = tmp_path / "test.txt"
    f.write_text("line1\nline2\nline3\n")

    tool = ReadFileTool()
    result = await tool.execute(path=str(f))
    assert "line1" in result
    assert "line2" in result


@pytest.mark.asyncio
async def test_read_file_not_found():
    tool = ReadFileTool()
    result = await tool.execute(path="/nonexistent/file.txt")
    assert "Error" in result


@pytest.mark.asyncio
async def test_write_file(tmp_path: Path):
    f = tmp_path / "out.txt"
    tool = WriteFileTool()
    result = await tool.execute(path=str(f), content="hello world")
    assert "Wrote" in result
    assert f.read_text() == "hello world"


@pytest.mark.asyncio
async def test_list_directory(tmp_path: Path):
    (tmp_path / "a.txt").touch()
    (tmp_path / "b").mkdir()
    tool = ListDirectoryTool()
    result = await tool.execute(path=str(tmp_path))
    assert "a.txt" in result
    assert "b" in result


@pytest.mark.asyncio
async def test_shell_basic():
    tool = ShellTool()
    result = await tool.execute(command="echo hello")
    assert "hello" in result


@pytest.mark.asyncio
async def test_shell_timeout():
    tool = ShellTool()
    result = await tool.execute(command="sleep 10", timeout=1)
    assert "timed out" in result


def test_dangerous_detection():
    assert _is_dangerous("rm -rf /")
    assert _is_dangerous("sudo rm file")
    assert not _is_dangerous("rm file.txt")
    assert not _is_dangerous("ls -la")
