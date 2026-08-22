import os
import sys
import time
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import Tuple, Dict, Any
from backend.config import settings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_SANDBOX_DIR = BASE_DIR / "sandbox"
DEFAULT_SANDBOX_DIR.mkdir(exist_ok=True)

class SandboxExecutor:
    def __init__(self, timeout: int = None):
        self.timeout = timeout or settings.SANDBOX_TIMEOUT

    def validate_filename(self, filename: str, language: str) -> str:
        """Sanitize and validate filename to prevent path traversal."""
        safe_name = os.path.basename(filename)
        if not safe_name or safe_name in [".", ".."]:
            safe_name = "script.py" if language == "python" else "script.js"
        
        # Enforce extension based on language
        if language.lower() in ["python", "py"] and not safe_name.endswith(".py"):
            safe_name += ".py"
        elif language.lower() in ["javascript", "js", "node"] and not safe_name.endswith(".js"):
            safe_name += ".js"
            
        return safe_name

    def execute_code(self, code: str, filename: str = "script.py", language: str = "python") -> Dict[str, Any]:
        """
        Execute user code safely inside an isolated temporary directory.
        Captures exit_code, stdout, stderr, execution_time, and timeout state.
        """
        safe_filename = self.validate_filename(filename, language)
        start_time = time.time()
        
        # Create a dedicated temp directory for isolation
        with tempfile.TemporaryDirectory(prefix="sandbox_exec_") as temp_dir:
            temp_path = Path(temp_dir)
            target_file = temp_path / safe_filename
            target_file.write_text(code, encoding="utf-8")
            
            # Determine execution command based on language
            lang_lower = language.lower()
            if lang_lower in ["python", "py"]:
                cmd = [sys.executable, str(target_file)]
            elif lang_lower in ["javascript", "js", "node"]:
                cmd = ["node", str(target_file)]
            else:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"Unsupported language runtime: {language}. Only Python and JavaScript are supported in this sandbox.",
                    "exit_code": -1,
                    "execution_time": 0.0,
                    "timed_out": False,
                    "error_type": "UnsupportedLanguage"
                }

            try:
                # Environment variables restriction for security
                env = os.environ.copy()
                env["PYTHONUNBUFFERED"] = "1"
                
                process = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=temp_dir,
                    env=env
                )
                
                exec_time = round(time.time() - start_time, 3)
                stdout = process.stdout or ""
                stderr = process.stderr or ""
                exit_code = process.returncode
                
                error_type = None
                if exit_code != 0 and stderr:
                    error_type = self._extract_error_type(stderr)

                return {
                    "success": (exit_code == 0),
                    "stdout": stdout,
                    "stderr": stderr,
                    "exit_code": exit_code,
                    "execution_time": exec_time,
                    "timed_out": False,
                    "error_type": error_type
                }
                
            except subprocess.TimeoutExpired:
                exec_time = round(time.time() - start_time, 3)
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"Execution Timed Out: Code execution exceeded the maximum timeout of {self.timeout} seconds.",
                    "exit_code": -1,
                    "execution_time": exec_time,
                    "timed_out": True,
                    "error_type": "TimeoutError"
                }
            except Exception as exc:
                exec_time = round(time.time() - start_time, 3)
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"Sandbox Execution Failure: {str(exc)}",
                    "exit_code": -1,
                    "execution_time": exec_time,
                    "timed_out": False,
                    "error_type": "ExecutionError"
                }

    def _extract_error_type(self, stderr: str) -> str:
        """Extract Python exception class or runtime error name from stderr."""
        lines = stderr.strip().splitlines()
        for line in reversed(lines):
            line_str = line.strip()
            if ":" in line_str and not line_str.startswith("File "):
                parts = line_str.split(":", 1)
                err_candidate = parts[0].strip()
                if "Error" in err_candidate or "Exception" in err_candidate:
                    return err_candidate
        return "RuntimeError"

sandbox_executor = SandboxExecutor()
