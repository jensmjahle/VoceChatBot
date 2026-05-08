import json
import logging

from app.bots.jellyfin import formatter
from app.core.config import JellyfinProxyConfig
from app.core.models import WebhookPayload
from app.core.registry import BotHandler
from app.core.vocechat_client import VoceChatClient

logger = logging.getLogger(__name__)


class JellyfinProxyBot(BotHandler):
    def __init__(self, api_key: str, client: VoceChatClient, config: JellyfinProxyConfig) -> None:
        self.api_key = api_key
        self._client = client
        self._config = config

    async def startup(self) -> None:
        logger.info(
            "JellyfinProxyBot started — forwarding to channel %d",
            self._config.target_channel_id,
        )

    async def handle_webhook(self, payload: WebhookPayload) -> None:
        pass

    async def handle_proxy_event(self, raw_body: bytes, headers: dict[str, str]) -> None:
        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError:
            logger.warning("JellyfinProxyBot received non-JSON body")
            return

        message = formatter.format_event(data)
        if message:
            await self._client.send_to_group(
                self._config.target_channel_id, message, "text/markdown"
            )
