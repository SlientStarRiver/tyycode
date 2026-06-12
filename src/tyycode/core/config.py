"""Configuration management - loads TOML config from ~/.tyycode/config.toml."""

from __future__ import annotations

import sys
from pathlib import Path

from pydantic import BaseModel, Field

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib  # type: ignore[no-redef]


class ProviderConfig(BaseModel):
    """LLM provider configuration."""

    name: str
    base_url: str
    api_key: str
    model: str


class TyyCodeConfig(BaseModel):
    """Root configuration."""

    default_provider: str = "openai"
    max_tokens_per_session: int = 100000
    tool_timeout: int = 30
    providers: list[ProviderConfig] = Field(default_factory=list)

    def get_provider(self, name: str | None = None) -> ProviderConfig:
        """Get provider config by name, fallback to default."""
        target = name or self.default_provider
        for p in self.providers:
            if p.name == target:
                return p
        if self.providers:
            return self.providers[0]
        raise ValueError(f"No provider found: {target}")


_DEFAULT_CONFIG_DIR = Path.home() / ".tyycode"
_DEFAULT_CONFIG_FILE = _DEFAULT_CONFIG_DIR / "config.toml"


def _find_config_path() -> Path:
    """Resolve config file path from env or default."""
    import os

    env_path = os.environ.get("TYYCODE_CONFIG_PATH")
    if env_path:
        return Path(env_path)
    return _DEFAULT_CONFIG_FILE


def load_config(path: Path | None = None) -> TyyCodeConfig:
    """Load and validate config from TOML file.

    Returns default config if file doesn't exist.
    """
    config_path = path or _find_config_path()

    if not config_path.exists():
        return TyyCodeConfig()

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    return TyyCodeConfig.model_validate(data)
