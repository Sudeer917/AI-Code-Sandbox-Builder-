import os
from fastapi import APIRouter
from backend.models.schemas import SettingsSchema
from backend.config import settings

router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("", response_model=SettingsSchema)
async def get_settings():
    api_key = os.getenv("AI_API_KEY") or os.getenv("GEMINI_API_KEY") or settings.AI_API_KEY
    ai_status = "configured" if api_key else "unavailable (using fallback rule engine)"
    
    return SettingsSchema(
        default_language="python",
        default_filename="script.py",
        sandbox_timeout=settings.SANDBOX_TIMEOUT,
        max_debug_attempts=settings.MAX_DEBUG_ATTEMPTS,
        ai_model=settings.AI_MODEL,
        ai_status=ai_status
    )

@router.post("", response_model=SettingsSchema)
async def update_settings(payload: SettingsSchema):
    settings.SANDBOX_TIMEOUT = payload.sandbox_timeout
    settings.MAX_DEBUG_ATTEMPTS = payload.max_debug_attempts
    settings.AI_MODEL = payload.ai_model
    return await get_settings()
