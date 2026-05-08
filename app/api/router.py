import logging

from fastapi import APIRouter, Request, Response

from app.core.models import WebhookPayload
from app.core.registry import BotHandler, BotRegistry

logger = logging.getLogger(__name__)


def build_webhook_router(registry: BotRegistry) -> APIRouter:
    router = APIRouter()

    for path, handler in registry._bots.items():
        _attach_routes(router, path, handler)

    return router


def _attach_routes(router: APIRouter, path: str, handler: BotHandler) -> None:
    def make_get():
        async def get_webhook() -> Response:
            return Response(status_code=200)
        get_webhook.__name__ = f"get_{path.replace('/', '_').strip('_')}"
        return get_webhook

    def make_post(h: BotHandler):
        async def post_webhook(request: Request) -> Response:
            api_key = request.headers.get("x-api-key", "")
            if api_key != h.api_key:
                return Response(status_code=401)

            body = await request.body()
            content_type = request.headers.get("content-type", "")

            if "application/json" in content_type or not content_type:
                try:
                    import json
                    data = json.loads(body)
                    if "from_uid" in data:
                        payload = WebhookPayload(**data)
                        await h.handle_webhook(payload)
                    else:
                        await h.handle_proxy_event(body, dict(request.headers))
                except Exception as exc:
                    logger.error("Webhook handler error on %s: %s", request.url.path, exc)
            else:
                await h.handle_proxy_event(body, dict(request.headers))

            return Response(status_code=200)

        post_webhook.__name__ = f"post_{path.replace('/', '_').strip('_')}"
        return post_webhook

    router.get(path)(make_get())
    router.post(path)(make_post(handler))
