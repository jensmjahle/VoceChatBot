import logging

import httpx

logger = logging.getLogger(__name__)


class VoceChatClient:
    def __init__(self, server_url: str, api_key: str, http_client: httpx.AsyncClient) -> None:
        self._base = server_url.rstrip("/")
        self._api_key = api_key
        self._client = http_client

    @property
    def _headers(self) -> dict[str, str]:
        return {"x-api-key": self._api_key}

    async def send_to_user(
        self, uid: int, content: str, content_type: str = "text/plain"
    ) -> None:
        url = f"{self._base}/api/bot/send_to_user/{uid}"
        await self._post(url, content, content_type)

    async def send_to_group(
        self, gid: int, content: str, content_type: str = "text/markdown"
    ) -> None:
        url = f"{self._base}/api/bot/send_to_group/{gid}"
        await self._post(url, content, content_type)

    async def get_bot_info(self) -> dict:
        url = f"{self._base}/api/bot"
        try:
            resp = await self._client.get(url, headers=self._headers)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.error("Failed to get bot info: %s", exc)
            return {}

    async def _post(self, url: str, content: str, content_type: str) -> None:
        try:
            resp = await self._client.post(
                url,
                content=content.encode(),
                headers={**self._headers, "Content-Type": content_type},
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error("VoceChat API error %s: %s", exc.response.status_code, exc.response.text)
        except Exception as exc:
            logger.error("Failed to send VoceChat message: %s", exc)
