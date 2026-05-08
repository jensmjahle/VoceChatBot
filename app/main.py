import logging
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.router import build_webhook_router
from app.core.config import (
    AIChatConfig,
    AppConfig,
    BotConfig,
    JellyfinProxyConfig,
    JellyseerrProxyConfig,
    load_config,
)
from app.core.registry import BotHandler, BotRegistry
from app.core.vocechat_client import VoceChatClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def _create_ai_chat_bot(
    bot_cfg: BotConfig, app_cfg: AppConfig, http_client: httpx.AsyncClient
) -> BotHandler:
    from app.bots.ai_chat.handler import AIChatBot

    config = AIChatConfig(**bot_cfg.config)
    vocechat = VoceChatClient(app_cfg.vocechat.server_url, bot_cfg.api_key, http_client)
    return AIChatBot(
        api_key=bot_cfg.api_key,
        client=vocechat,
        config=config,
        ollama_base_url=app_cfg.ollama.base_url,
    )


def _create_jellyfin_bot(
    bot_cfg: BotConfig, app_cfg: AppConfig, http_client: httpx.AsyncClient
) -> BotHandler:
    from app.bots.jellyfin.handler import JellyfinProxyBot

    config = JellyfinProxyConfig(**bot_cfg.config)
    vocechat = VoceChatClient(app_cfg.vocechat.server_url, bot_cfg.api_key, http_client)
    return JellyfinProxyBot(api_key=bot_cfg.api_key, client=vocechat, config=config)


def _create_jellyseerr_bot(
    bot_cfg: BotConfig, app_cfg: AppConfig, http_client: httpx.AsyncClient
) -> BotHandler:
    from app.bots.jellyseerr.client import JellyseerrClient
    from app.bots.jellyseerr.handler import JellyseerrProxyBot

    config = JellyseerrProxyConfig(**bot_cfg.config)
    vocechat = VoceChatClient(app_cfg.vocechat.server_url, bot_cfg.api_key, http_client)
    jellyseerr = JellyseerrClient(config.jellyseerr_url, config.jellyseerr_api_key, http_client)
    return JellyseerrProxyBot(
        api_key=bot_cfg.api_key,
        client=vocechat,
        config=config,
        jellyseerr=jellyseerr,
    )


_BOT_FACTORIES: dict[str, Any] = {
    "ai_chat": _create_ai_chat_bot,
    "jellyfin_proxy": _create_jellyfin_bot,
    "jellyseerr_proxy": _create_jellyseerr_bot,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_config()
    http_client = httpx.AsyncClient(timeout=30.0)
    registry = BotRegistry()

    for bot_cfg in config.bots:
        if bot_cfg.api_key.lower() in ("disabled", "none", ""):
            logger.info("Bot '%s' is disabled — skipping", bot_cfg.name)
            continue
        factory = _BOT_FACTORIES.get(bot_cfg.type)
        if factory is None:
            logger.warning("Unknown bot type '%s' for bot '%s' — skipping", bot_cfg.type, bot_cfg.name)
            continue
        handler = factory(bot_cfg, config, http_client)
        registry.register(bot_cfg.webhook_path, handler)
        logger.info("Registered bot '%s' at %s", bot_cfg.name, bot_cfg.webhook_path)

    webhook_router = build_webhook_router(registry)
    app.include_router(webhook_router)

    app.state.registry = registry
    app.state.config = config

    for handler in registry.all_handlers():
        await handler.startup()

    logger.info("VoceChatBot started with %d bot(s)", len(registry.all_handlers()))

    yield

    for handler in registry.all_handlers():
        await handler.shutdown()
    await http_client.aclose()
    logger.info("VoceChatBot shut down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="VoceChatBot",
        description="Multi-bot engine for VoceChat with Jellyfin, Jellyseerr and Ollama AI",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(health_router)
    return app


app = create_app()
