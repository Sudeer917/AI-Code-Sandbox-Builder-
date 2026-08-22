from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.models.schemas import DebugRequest, DebugResponse, ChangeDetail
from backend.services.sandbox_executor import sandbox_executor
from backend.services.ai_debugger import ai_debugger_service
from backend.services.history_service import history_service
from backend.database.database import get_db
from backend.config import settings

router = APIRouter(prefix="/api", tags=["debugging"])

@router.post("/debug", response_model=DebugResponse)
async def debug_code(req: DebugRequest, db: Session = Depends(get_db)):
    if not req.code or not req.code.strip():
        raise HTTPException(status_code=400, detail="Source code cannot be empty.")

    logs: List[str] = []
    logs.append(f"[INIT] AI Code Sandbox Debugger instantiated.")
    logs.append(f"[CONFIG] Target filename: {req.filename} ({req.language})")

    current_code = req.code
    original_code = req.code
    max_attempts = settings.MAX_DEBUG_ATTEMPTS
    attempt = 0
    final_res = None
    last_analysis = None

    # Step 1: Initial Execution
    logs.append(f"[STEP 1] Running initial code execution in isolated sandbox...")
    initial_exec = sandbox_executor.execute_code(current_code, req.filename, req.language)
    
    if initial_exec["success"]:
        logs.append(f"[SUCCESS] Code executed with exit code 0. No bugs detected!")
        # Store clean run in DB
        history_service.create_record(
            db=db,
            filename=req.filename,
            language=req.language,
            original_code=original_code,
            fixed_code=None,
            stdout=initial_exec["stdout"],
            stderr=initial_exec["stderr"],
            error_type=None,
            error_line=None,
            root_cause="Clean Execution: No syntax or runtime errors detected.",
            fix_explanation="Original script is valid and runs without issues.",
            exit_code=0,
            execution_time=initial_exec["execution_time"],
            attempts=1,
            status="success"
        )
        return DebugResponse(
            success=True,
            original_code=original_code,
            fixed_code=original_code,
            error_type=None,
            error_line=None,
            root_cause="Clean Execution: Code executed successfully without errors.",
            fix_explanation="No modifications required.",
            changes=[],
            stdout=initial_exec["stdout"],
            stderr=initial_exec["stderr"],
            exit_code=0,
            execution_time=initial_exec["execution_time"],
            attempts=1,
            logs=logs
        )

    # Error detected -> Autonomous Debug Loop (Max 3 attempts)
    logs.append(f"[ERROR_DETECTED] Initial run failed with exit code {initial_exec['exit_code']}.")
    if initial_exec["stderr"]:
        for line in initial_exec["stderr"].strip().splitlines()[:5]:
            logs.append(f"[STDERR] {line}")

    while attempt < max_attempts:
        attempt += 1
        logs.append(f"[ATTEMPT {attempt}/{max_attempts}] Autonomous debugging iteration started.")

        # Execute code if not first iteration
        if attempt > 1:
            exec_res = sandbox_executor.execute_code(current_code, req.filename, req.language)
            if exec_res["success"]:
                logs.append(f"[VERIFY_SUCCESS] Iteration {attempt} code execution passed! Exit code 0.")
                final_res = exec_res
                break
            else:
                logs.append(f"[EXECUTION_FAIL] Iteration {attempt} code execution failed.")
                current_stderr = exec_res["stderr"]
                current_stdout = exec_res["stdout"]
                current_exit = exec_res["exit_code"]
        else:
            current_stderr = initial_exec["stderr"]
            current_stdout = initial_exec["stdout"]
            current_exit = initial_exec["exit_code"]

        # Call AI Debugger Service
        logs.append(f"[AI_ANALYSIS] Sending code and stderr to AI Debugger...")
        analysis = ai_debugger_service.analyze_and_fix(
            code=current_code,
            stderr=current_stderr,
            stdout=current_stdout,
            exit_code=current_exit,
            filename=req.filename,
            language=req.language,
            attempt=attempt
        )
        last_analysis = analysis
        logs.append(f"[AI_ROOT_CAUSE] {analysis['root_cause']}")
        logs.append(f"[AI_FIX_PROPOSED] Line {analysis.get('error_line', 1)}: {analysis['fix_explanation']}")

        current_code = analysis["fixed_code"]

        # Immediate verification run
        logs.append(f"[VERIFY] Testing generated code fix in sandbox...")
        verify_res = sandbox_executor.execute_code(current_code, req.filename, req.language)
        if verify_res["success"]:
            logs.append(f"[VERIFY_PASSED] Verified fix successfully! Exit code: 0.")
            if verify_res["stdout"]:
                logs.append(f"[STDOUT] {verify_res['stdout'].strip()}")
            final_res = verify_res
            break
        else:
            logs.append(f"[VERIFY_FAILED] Fix attempt {attempt} still generated errors.")

    # Determine final outcome
    is_success = final_res is not None and final_res["success"]
    status_str = "fixed" if is_success else "failed"

    stdout_out = final_res["stdout"] if final_res else ""
    stderr_out = final_res["stderr"] if final_res else (initial_exec["stderr"] if initial_exec else "")
    exit_code_out = final_res["exit_code"] if final_res else -1
    exec_time_out = final_res["execution_time"] if final_res else 0.0

    error_type = last_analysis.get("error_type") if last_analysis else "RuntimeError"
    error_line = last_analysis.get("error_line") if last_analysis else 1
    root_cause = last_analysis.get("root_cause") if last_analysis else "Multiple debug attempts failed."
    fix_explanation = last_analysis.get("fix_explanation") if last_analysis else "AI could not automatically resolve this issue."
    raw_changes = last_analysis.get("changes", []) if last_analysis else []

    changes = [ChangeDetail(**c) if isinstance(c, dict) else c for c in raw_changes]

    # Save session to DB
    history_service.create_record(
        db=db,
        filename=req.filename,
        language=req.language,
        original_code=original_code,
        fixed_code=current_code if is_success else None,
        stdout=stdout_out,
        stderr=stderr_out,
        error_type=error_type,
        error_line=error_line,
        root_cause=root_cause,
        fix_explanation=fix_explanation,
        exit_code=exit_code_out,
        execution_time=exec_time_out,
        attempts=attempt,
        status=status_str
    )

    if is_success:
        logs.append(f"[COMPLETE] Bug fixed and verified after {attempt} attempt(s).")
    else:
        logs.append(f"[FAILED] AI could not automatically resolve the issue after {max_attempts} attempts.")

    return DebugResponse(
        success=is_success,
        original_code=original_code,
        fixed_code=current_code,
        error_type=error_type,
        error_line=error_line,
        root_cause=root_cause,
        fix_explanation=fix_explanation,
        changes=changes,
        stdout=stdout_out,
        stderr=stderr_out,
        exit_code=exit_code_out,
        execution_time=exec_time_out,
        attempts=attempt,
        logs=logs
    )
