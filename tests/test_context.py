"""Tests for context module."""

from pathlib import Path

from tyycode.core.context import ConversationContext


def test_add_messages():
    ctx = ConversationContext()
    ctx.add_user_message("hello")
    ctx.add_assistant_message("hi there")

    msgs = ctx.messages
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"


def test_add_tool_result():
    ctx = ConversationContext()
    ctx.add_tool_result("call_123", "result text")

    msgs = ctx.messages
    assert len(msgs) == 1
    assert msgs[0]["role"] == "tool"
    assert msgs[0]["tool_call_id"] == "call_123"


def test_record_usage():
    ctx = ConversationContext()
    ctx.record_usage(100, 50)
    ctx.record_usage(200, 80)

    usage = ctx.token_usage
    assert usage["prompt"] == 300
    assert usage["completion"] == 130
    assert usage["total"] == 430


def test_get_llm_messages_has_system():
    ctx = ConversationContext()
    ctx.add_user_message("test")

    msgs = ctx.get_llm_messages()
    assert msgs[0]["role"] == "system"


def test_save_and_load(tmp_path: Path):
    ctx = ConversationContext()
    ctx.add_user_message("hello")
    ctx.add_assistant_message("world")
    ctx.record_usage(100, 50)

    path = ctx.save(tmp_path, "test_session")
    assert path.exists()

    loaded = ConversationContext.load(path)
    assert len(loaded.messages) == 2
    assert loaded.token_usage["total"] == 150


def test_truncation():
    ctx = ConversationContext(max_tokens=100)  # very low limit

    # Add many messages to trigger truncation
    for i in range(20):
        ctx.add_user_message(f"message {i}" * 10)
        ctx.add_assistant_message(f"response {i}" * 10)

    msgs = ctx.get_llm_messages()
    # Should have system + summary + recent messages
    assert msgs[0]["role"] == "system"
    assert len(msgs) < 42  # less than 1 system + 40 messages
