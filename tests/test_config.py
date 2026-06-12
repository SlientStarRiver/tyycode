"""Tests for config module."""

from pathlib import Path

from tyycode.core.config import ProviderConfig, TyyCodeConfig, load_config


def test_default_config():
    cfg = TyyCodeConfig()
    assert cfg.default_provider == "openai"
    assert cfg.max_tokens_per_session == 100000
    assert cfg.tool_timeout == 30
    assert cfg.providers == []


def test_provider_config():
    p = ProviderConfig(
        name="test", base_url="http://localhost",
        api_key="key", model="model",
    )
    assert p.name == "test"


def test_get_provider_by_name():
    cfg = TyyCodeConfig(
        providers=[
            ProviderConfig(name="a", base_url="http://a", api_key="ka", model="ma"),
            ProviderConfig(name="b", base_url="http://b", api_key="kb", model="mb"),
        ]
    )
    assert cfg.get_provider("b").name == "b"


def test_get_provider_default():
    cfg = TyyCodeConfig(
        default_provider="b",
        providers=[
            ProviderConfig(name="a", base_url="http://a", api_key="ka", model="ma"),
            ProviderConfig(name="b", base_url="http://b", api_key="kb", model="mb"),
        ],
    )
    assert cfg.get_provider().name == "b"


def test_get_provider_missing():
    cfg = TyyCodeConfig()
    try:
        cfg.get_provider("none")
        raise AssertionError("Should have raised")
    except ValueError:
        pass


def test_load_config_missing_file(tmp_path: Path):
    cfg = load_config(tmp_path / "nonexistent.toml")
    assert cfg.default_provider == "openai"


def test_load_config_from_file(tmp_path: Path):
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
default_provider = "ollama"
max_tokens_per_session = 50000
tool_timeout = 60

[[providers]]
name = "ollama"
base_url = "http://localhost:11434/v1"
api_key = "ollama"
model = "qwen2.5"
""")
    cfg = load_config(config_file)
    assert cfg.default_provider == "ollama"
    assert cfg.max_tokens_per_session == 50000
    assert cfg.tool_timeout == 60
    assert len(cfg.providers) == 1
    assert cfg.providers[0].name == "ollama"
