import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class JellyseerrClient:
    def __init__(self, base_url: str, api_key: str, http_client: httpx.AsyncClient) -> None:
        self._base = base_url.rstrip("/")
        self._headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
        self._client = http_client

    async def search(self, query: str, page: int = 1) -> list[dict[str, Any]]:
        try:
            resp = await self._client.get(
                f"{self._base}/api/v1/search",
                params={"query": query, "page": page},
                headers=self._headers,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("results", [])
        except Exception as exc:
            logger.error("Jellyseerr search error: %s", exc)
            return []

    async def request_media(
        self,
        media_type: str,
        tmdb_id: int,
        seasons: list[int] | None = None,
    ) -> dict[str, Any] | None:
        payload: dict[str, Any] = {"mediaType": media_type, "mediaId": tmdb_id}
        if seasons:
            payload["seasons"] = seasons
        try:
            resp = await self._client.post(
                f"{self._base}/api/v1/request",
                json=payload,
                headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Jellyseerr request error %d: %s",
                exc.response.status_code,
                exc.response.text,
            )
            return None
        except Exception as exc:
            logger.error("Jellyseerr request error: %s", exc)
            return None

    async def get_requests(self, status: str = "all", count: int = 10) -> list[dict[str, Any]]:
        try:
            params: dict[str, Any] = {"take": count, "skip": 0}
            if status != "all":
                params["status"] = status
            resp = await self._client.get(
                f"{self._base}/api/v1/request",
                params=params,
                headers=self._headers,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("results", [])
        except Exception as exc:
            logger.error("Jellyseerr get_requests error: %s", exc)
            return []
