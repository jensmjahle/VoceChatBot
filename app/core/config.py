import os
import re
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel


# Matches ${VAR} and ${VAR:-default}
_ENV_VAR_PATTERN = re.compile(r"\$\{([^}:]+)(?::-(.*?))?\}")


def _substitute_env_vars(value: Any) -> Any:
    if isinstance(value, str):
        def replace(match: re.Match) -> str:
            var_name = match.group(1)
            default = match.group(2)
            env_value = os.environ.get(var_name)
            if env_value is None:
                if default is not None:
                    return default
                raise RuntimeError(f"Required environment variable '{var_name}' is not set")
            return env_value
        return _ENV_VAR_PATTERN.sub(replace, value)
    if isinstance(value, dict):
        return {k: _substitute_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_substitute_env_vars(item) for item in value]
    return value


class VoceChatServerConfig(BaseModel):
    server_url: str


class AIChatConfig(BaseModel):
    model: str = "llama3.2"
    system_prompt: str = "You are a helpful assistant."
    temperature: float = 0.7
    max_tokens: int = 2048
    history_length: int = 20


class JellyfinProxyConfig(BaseModel):
    target_channel_id: int


class JellyseerrProxyConfig(BaseModel):
    jellyseerr_url: str
    jellyseerr_api_key: str
    target_channel_id: int
    allowed_users: list[int] = []


class BotConfig(BaseModel):
    name: str
    api_key: str
    webhook_path: str
    type: Literal["ai_chat", "jellyfin_proxy", "jellyseerr_proxy"]
    config: dict[str, Any] = {}


class OllamaConfig(BaseModel):
    base_url: str = "http://localhost:11434"


class JellyfinConfig(BaseModel):
    url: str
    api_key: str


class AppConfig(BaseModel):
    vocechat: VoceChatServerConfig
    bots: list[BotConfig]
    ollama: OllamaConfig = OllamaConfig()
    jellyfin: JellyfinConfig | None = None


_config: AppConfig | None = None


def load_config(path: str | None = None) -> AppConfig:
    global _config
    config_path = path or os.environ.get("CONFIG_PATH", "config.yaml")
    raw = Path(config_path).read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    data = _substitute_env_vars(data)
    _config = AppConfig(**data)
    return _config


def get_config() -> AppConfig:
    if _config is None:
        raise RuntimeError("Config has not been loaded. Call load_config() first.")
    return _config
