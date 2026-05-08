from abc import ABC, abstractmethod

from app.core.models import WebhookPayload


class BotHandler(ABC):
    api_key: str

    @abstractmethod
    async def handle_webhook(self, payload: WebhookPayload) -> None:
        """Called for VoceChat chat messages directed at this bot."""
        ...

    async def handle_proxy_event(self, raw_body: bytes, headers: dict[str, str]) -> None:
        """Called for external service webhook events (Jellyfin, Jellyseerr)."""

    async def startup(self) -> None:
        """Optional async startup hook."""

    async def shutdown(self) -> None:
        """Optional async shutdown hook."""


class BotRegistry:
    def __init__(self) -> None:
        self._bots: dict[str, BotHandler] = {}

    def register(self, webhook_path: str, handler: BotHandler) -> None:
        self._bots[webhook_path] = handler

    def get(self, webhook_path: str) -> BotHandler | None:
        return self._bots.get(webhook_path)

    def all_handlers(self) -> list[BotHandler]:
        return list(self._bots.values())

    def webhook_paths(self) -> list[str]:
        return list(self._bots.keys())
