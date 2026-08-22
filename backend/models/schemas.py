from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ChangeDetail(BaseModel):
    line: Optional[int] = None
    before: str
    after: str

class RunRequest(BaseModel):
    filename: str = Field(default="script.py", description="Name of file to execute")
    language: str = Field(default="python", description="Programming language")
    code: str = Field(..., description="Source code to execute")

class RunResponse(BaseModel):
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    timed_out: bool = False
    error_type: Optional[str] = None
    error_message: Optional[str] = None

class DebugRequest(BaseModel):
    filename: str = Field(default="script.py", description="Name of file to debug")
    language: str = Field(default="python", description="Programming language")
    code: str = Field(..., description="Source code to debug")

class DebugResponse(BaseModel):
    success: bool
    original_code: str
    fixed_code: str
    error_type: Optional[str] = None
    error_line: Optional[int] = None
    root_cause: str
    fix_explanation: str
    changes: List[ChangeDetail] = []
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float = 0.0
    attempts: int = 1
    logs: List[str] = []

class HistoryItemResponse(BaseModel):
    id: str
    filename: str
    language: str
    original_code: str
    fixed_code: Optional[str] = None
    stdout: str
    stderr: str
    error_type: Optional[str] = None
    error_line: Optional[int] = None
    root_cause: Optional[str] = None
    fix_explanation: Optional[str] = None
    exit_code: int
    execution_time: float
    attempts: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

class StatsResponse(BaseModel):
    total_executions: int
    bugs_detected: int
    bugs_fixed: int
    success_rate: float
    recent_activity: List[HistoryItemResponse]

class SettingsSchema(BaseModel):
    default_language: str = "python"
    default_filename: str = "script.py"
    sandbox_timeout: int = 10
    max_debug_attempts: int = 3
    ai_model: str = "gemini-2.5-flash"
    ai_status: str = "unknown"
