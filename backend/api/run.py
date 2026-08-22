from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.models.schemas import RunRequest, RunResponse
from backend.services.sandbox_executor import sandbox_executor
from backend.services.history_service import history_service
from backend.database.database import get_db

router = APIRouter(prefix="/api", tags=["execution"])

@router.post("/run", response_model=RunResponse)
async def run_code(req: RunRequest, db: Session = Depends(get_db)):
    if not req.code or not req.code.strip():
        raise HTTPException(status_code=400, detail="Source code cannot be empty.")

    res = sandbox_executor.execute_code(
        code=req.code,
        filename=req.filename,
        language=req.language
    )

    status_str = "success" if res["success"] else ("timeout" if res["timed_out"] else "error")

    # Persist execution in DB
    history_service.create_record(
        db=db,
        filename=req.filename,
        language=req.language,
        original_code=req.code,
        fixed_code=None,
        stdout=res["stdout"],
        stderr=res["stderr"],
        error_type=res.get("error_type"),
        error_line=None,
        root_cause=None,
        fix_explanation=None,
        exit_code=res["exit_code"],
        execution_time=res["execution_time"],
        attempts=1,
        status=status_str
    )

    return RunResponse(
        success=res["success"],
        stdout=res["stdout"],
        stderr=res["stderr"],
        exit_code=res["exit_code"],
        execution_time=res["execution_time"],
        timed_out=res["timed_out"],
        error_type=res.get("error_type")
    )
