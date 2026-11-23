from fastapi import APIRouter
from app.config import settings

router = APIRouter()


@router.get("/status")
async def status():
    return {
        "project": "HAMSA AVIATOR AI",
        "phase": 2,
        "environment": settings.app_env,
        "telegram_configured": bool(settings.telegram_bot_token),
        "official_data_source_configured": False,
        "research_mode": True,
    }
