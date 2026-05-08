from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health_check(request: Request) -> dict:
    from app.core.registry import BotRegistry
    registry: BotRegistry = request.app.state.registry
    return {
        "status": "ok",
        "bots": registry.webhook_paths(),
    }
