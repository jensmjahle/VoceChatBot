import json
import logging

from app.bots.jellyseerr import formatter
from app.bots.jellyseerr.client import JellyseerrClient
from app.core.config import JellyseerrProxyConfig
from app.core.models import WebhookPayload
from app.core.registry import BotHandler
from app.core.vocechat_client import VoceChatClient

logger = logging.getLogger(__name__)

HELP_TEXT = """\
**Jellyseerr commands:**
`!search <query>` — search for movies or TV shows
`!request movie <tmdb_id>` — request a movie
`!request tv <tmdb_id>` — request a TV show
`!status` — show recent requests
`!help` — show this message\
"""


class JellyseerrProxyBot(BotHandler):
    def __init__(
        self,
        api_key: str,
        client: VoceChatClient,
        config: JellyseerrProxyConfig,
        jellyseerr: JellyseerrClient,
    ) -> None:
        self.api_key = api_key
        self._client = client
        self._config = config
        self._jellyseerr = jellyseerr

    async def startup(self) -> None:
        logger.info(
            "JellyseerrProxyBot started — channel %d, url %s",
            self._config.target_channel_id,
            self._config.jellyseerr_url,
        )

    async def handle_webhook(self, payload: WebhookPayload) -> None:
        uid = payload.from_uid
        if self._config.allowed_users and uid not in self._config.allowed_users:
            await self._reply(payload, "Sorry, you are not allowed to use this bot.")
            return

        text = payload.detail.content.strip()
        parts = text.split(maxsplit=2)
        command = parts[0].lower() if parts else ""

        if command == "!search":
            query = " ".join(parts[1:])
            if not query:
                await self._reply(payload, "Usage: `!search <query>`")
                return
            results = await self._jellyseerr.search(query)
            await self._reply(payload, formatter.format_search_results(results))

        elif command == "!request":
            if len(parts) < 3:
                await self._reply(payload, "Usage: `!request movie|tv <tmdb_id>`")
                return
            media_type = parts[1].lower()
            if media_type not in ("movie", "tv"):
                await self._reply(payload, "Media type must be `movie` or `tv`.")
                return
            try:
                tmdb_id = int(parts[2])
            except ValueError:
                await self._reply(payload, "Invalid tmdb_id — must be a number.")
                return
            result = await self._jellyseerr.request_media(media_type, tmdb_id)
            if result:
                await self._reply(payload, formatter.format_request_result(result))
            else:
                await self._reply(payload, "Failed to submit request. It may already exist.")

        elif command == "!status":
            requests = await self._jellyseerr.get_requests(count=5)
            if not requests:
                await self._reply(payload, "No recent requests found.")
                return
            lines = ["**Recent requests:**\n"]
            for req in requests:
                media = req.get("media", {}) or {}
                title = media.get("originalTitle") or media.get("originalName") or "Unknown"
                status = req.get("status", 1)
                icon = formatter.STATUS_ICONS.get(status, "📋")
                lines.append(f"{icon} {title}")
            await self._reply(payload, "\n".join(lines))

        elif command == "!help":
            await self._reply(payload, HELP_TEXT)

        else:
            await self._reply(payload, HELP_TEXT)

    async def handle_proxy_event(self, raw_body: bytes, headers: dict[str, str]) -> None:
        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError:
            logger.warning("JellyseerrProxyBot received non-JSON body")
            return

        message = formatter.format_webhook_event(data)
        if message:
            await self._client.send_to_group(
                self._config.target_channel_id, message, "text/markdown"
            )

    async def _reply(self, payload: WebhookPayload, text: str) -> None:
        if payload.target.gid is not None:
            await self._client.send_to_group(payload.target.gid, text, "text/markdown")
        else:
            await self._client.send_to_user(payload.from_uid, text, "text/markdown")
