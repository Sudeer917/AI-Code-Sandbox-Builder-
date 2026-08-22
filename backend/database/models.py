import datetime
import uuid
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime
from backend.database.database import Base

class ExecutionDB(Base):
    __tablename__ = "executions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False, default="script.py")
    language = Column(String(50), nullable=False, default="python")
    original_code = Column(Text, nullable=False)
    fixed_code = Column(Text, nullable=True)
    stdout = Column(Text, default="")
    stderr = Column(Text, default="")
    error_type = Column(String(100), nullable=True)
    error_line = Column(Integer, nullable=True)
    root_cause = Column(Text, nullable=True)
    fix_explanation = Column(Text, nullable=True)
    exit_code = Column(Integer, default=0)
    execution_time = Column(Float, default=0.0)
    attempts = Column(Integer, default=1)
    status = Column(String(50), default="success")  # success, failed, error, timeout
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
