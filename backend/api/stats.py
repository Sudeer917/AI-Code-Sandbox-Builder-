from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.models.schemas import StatsResponse
from backend.services.history_service import history_service
from backend.database.database import get_db

router = APIRouter(prefix="/api/stats", tags=["dashboard"])

@router.get("", response_model=StatsResponse)
async def get_dashboard_stats(db: Session = Depends(get_db)):
    stats = history_service.get_stats(db)
    return StatsResponse(**stats)
