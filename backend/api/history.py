from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from backend.models.schemas import HistoryItemResponse
from backend.services.history_service import history_service
from backend.database.database import get_db

router = APIRouter(prefix="/api/history", tags=["history"])

@router.get("", response_model=List[HistoryItemResponse])
async def list_history(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    records = history_service.get_all(db, limit=limit, offset=offset)
    return [HistoryItemResponse.model_validate(r) for r in records]

@router.get("/{session_id}", response_model=HistoryItemResponse)
async def get_history_item(session_id: str, db: Session = Depends(get_db)):
    record = history_service.get_by_id(db, session_id)
    if not record:
        raise HTTPException(status_code=404, detail="History session not found.")
    return HistoryItemResponse.model_validate(record)

@router.delete("/{session_id}")
async def delete_history_item(session_id: str, db: Session = Depends(get_db)):
    deleted = history_service.delete_by_id(db, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="History session not found.")
    return {"status": "ok", "message": f"Session {session_id} deleted successfully."}

@router.delete("")
async def clear_all_history(db: Session = Depends(get_db)):
    count = history_service.clear_all(db)
    return {"status": "ok", "message": f"Cleared {count} history records."}
