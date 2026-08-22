from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional, Dict, Any
from backend.database.models import ExecutionDB
from backend.models.schemas import HistoryItemResponse, StatsResponse

class HistoryService:
    def create_record(
        self,
        db: Session,
        filename: str,
        language: str,
        original_code: str,
        fixed_code: Optional[str],
        stdout: str,
        stderr: str,
        error_type: Optional[str],
        error_line: Optional[int],
        root_cause: Optional[str],
        fix_explanation: Optional[str],
        exit_code: int,
        execution_time: float,
        attempts: int,
        status: str
    ) -> ExecutionDB:
        record = ExecutionDB(
            filename=filename,
            language=language,
            original_code=original_code,
            fixed_code=fixed_code,
            stdout=stdout,
            stderr=stderr,
            error_type=error_type,
            error_line=error_line,
            root_cause=root_cause,
            fix_explanation=fix_explanation,
            exit_code=exit_code,
            execution_time=execution_time,
            attempts=attempts,
            status=status
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def get_all(self, db: Session, limit: int = 50, offset: int = 0) -> List[ExecutionDB]:
        return db.query(ExecutionDB).order_by(desc(ExecutionDB.created_at)).offset(offset).limit(limit).all()

    def get_by_id(self, db: Session, session_id: str) -> Optional[ExecutionDB]:
        return db.query(ExecutionDB).filter(ExecutionDB.id == session_id).first()

    def delete_by_id(self, db: Session, session_id: str) -> bool:
        record = self.get_by_id(db, session_id)
        if record:
            db.delete(record)
            db.commit()
            return True
        return False

    def clear_all(self, db: Session) -> int:
        count = db.query(ExecutionDB).delete()
        db.commit()
        return count

    def get_stats(self, db: Session) -> Dict[str, Any]:
        total_executions = db.query(func.count(ExecutionDB.id)).scalar() or 0
        bugs_detected = db.query(func.count(ExecutionDB.id)).filter(ExecutionDB.error_type != None).scalar() or 0
        bugs_fixed = db.query(func.count(ExecutionDB.id)).filter(ExecutionDB.status == "fixed").scalar() or 0
        successful_executions = db.query(func.count(ExecutionDB.id)).filter(
            (ExecutionDB.status == "success") | (ExecutionDB.status == "fixed")
        ).scalar() or 0

        success_rate = round((successful_executions / total_executions * 100), 1) if total_executions > 0 else 100.0

        recent = self.get_all(db, limit=10)
        recent_items = [HistoryItemResponse.model_validate(r) for r in recent]

        return {
            "total_executions": total_executions,
            "bugs_detected": bugs_detected,
            "bugs_fixed": bugs_fixed,
            "success_rate": success_rate,
            "recent_activity": recent_items
        }

history_service = HistoryService()
