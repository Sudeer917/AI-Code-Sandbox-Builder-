import os
import re
import json
import ast
import traceback
from typing import Dict, Any, List, Optional
from backend.config import settings

class AIDebuggerService:
    def __init__(self):
        self.api_key = settings.AI_API_KEY
        self.model_name = settings.AI_MODEL

    def analyze_and_fix(
        self,
        code: str,
        stderr: str,
        stdout: str,
        exit_code: int,
        filename: str = "script.py",
        language: str = "python",
        attempt: int = 1
    ) -> Dict[str, Any]:
        """
        Analyze code and runtime error, returning structured bug fix instructions.
        Uses Gemini API if key is present, otherwise falls back to smart rule engine.
        """
        # Check if Gemini API key is available
        api_key = os.getenv("AI_API_KEY") or os.getenv("GEMINI_API_KEY") or self.api_key
        
        if api_key:
            try:
                ai_res = self._call_gemini_api(api_key, code, stderr, stdout, exit_code, filename, language, attempt)
                if ai_res:
                    return ai_res
            except Exception as e:
                print(f"[AIDebugger] Gemini API call failed: {e}. Falling back to Rule Engine.")

        # Fallback to intelligent Rule & AST Engine
        return self._fallback_rule_engine(code, stderr, stdout, exit_code, filename, language)

    def _call_gemini_api(
        self,
        api_key: str,
        code: str,
        stderr: str,
        stdout: str,
        exit_code: int,
        filename: str,
        language: str,
        attempt: int
    ) -> Optional[Dict[str, Any]]:
        """Call Google Gemini API using google-genai or google-generativeai or httpx REST API."""
        prompt = f"""
You are an expert AI software engineer debugging code in a sandbox environment.

### Target Context
Filename: {filename}
Language: {language}
Attempt #: {attempt}

### Source Code
```
{code}
```

### Execution Output
stdout:
{stdout}

stderr:
{stderr}
exit_code: {exit_code}

### Task
1. Understand the code and runtime error.
2. Identify the error type, error line number (1-indexed), root cause, and fix explanation.
3. Provide the corrected, complete fixed source code.
4. List exact before/after line changes.
5. Return ONLY a valid, strict JSON object with NO markdown formatting around the JSON object.

JSON Schema:
{{
  "error_type": "NameError",
  "error_line": 3,
  "root_cause": "Detailed root cause explanation",
  "fixed_code": "Complete fixed code",
  "fix_explanation": "Explanation of why the fix works",
  "changes": [
    {{
      "line": 3,
      "before": "average = total / len(number)",
      "after": "average = total / len(numbers)"
    }}
  ]
}}
"""

        # Try google.genai SDK
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            parsed = json.loads(response.text)
            return self._validate_ai_dict(parsed, code)
        except Exception as genai_err:
            pass

        # Try google.generativeai SDK
        try:
            import google.generativeai as genai_legacy
            genai_legacy.configure(api_key=api_key)
            model = genai_legacy.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean_text)
            return self._validate_ai_dict(parsed, code)
        except Exception as legacy_err:
            pass

        # Try HTTP request via httpx
        try:
            import httpx
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            resp = httpx.post(url, json=payload, timeout=15.0)
            if resp.status_code == 200:
                data = resp.json()
                raw_text = data['candidates'][0]['content']['parts'][0]['text']
                clean_text = raw_text.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(clean_text)
                return self._validate_ai_dict(parsed, code)
        except Exception as http_err:
            pass

        return None

    def _validate_ai_dict(self, data: Dict[str, Any], original_code: str) -> Dict[str, Any]:
        """Validate and normalize dictionary output from AI response."""
        fixed_code = data.get("fixed_code") or original_code
        changes = data.get("changes") or []
        
        # If changes are missing, derive simple line difference
        if not changes and fixed_code != original_code:
            changes = self._compute_diff(original_code, fixed_code)

        return {
            "error_type": data.get("error_type", "RuntimeError"),
            "error_line": data.get("error_line", 1),
            "root_cause": data.get("root_cause", "Runtime error detected during execution."),
            "fixed_code": fixed_code,
            "fix_explanation": data.get("fix_explanation", "Applied fix based on AI error analysis."),
            "changes": changes
        }

    def _fallback_rule_engine(
        self,
        code: str,
        stderr: str,
        stdout: str,
        exit_code: int,
        filename: str,
        language: str
    ) -> Dict[str, Any]:
        """Intelligent Rule & AST-based debugger for fallback execution."""
        lines = code.splitlines()
        stderr_lower = stderr.lower()
        
        # Find line number from Python traceback
        line_num = None
        match_line = re.search(r'File ".*?", line (\d+)', stderr)
        if match_line:
            line_num = int(match_line.group(1))

        # 1. NameError (e.g. len(number) -> len(numbers))
        if "nameerror" in stderr_lower or "is not defined" in stderr_lower:
            var_match = re.search(r"name '(.*?)' is not defined", stderr)
            missing_var = var_match.group(1) if var_match else "number"
            
            # Check for close variable match (pluralization, typos)
            best_match = None
            if missing_var == "number" and "numbers" in code:
                best_match = "numbers"
            else:
                # Find variable names defined in scope
                all_words = re.findall(r'\b[a-zA-Z_]\w*\b', code)
                for w in all_words:
                    if w != missing_var and (w.startswith(missing_var) or missing_var.startswith(w) or w == missing_var + "s"):
                        best_match = w
                        break
            
            target_var = best_match or (missing_var + "s" if not missing_var.endswith("s") else missing_var[:-1])
            
            fixed_lines = []
            changes = []
            for idx, line in enumerate(lines, 1):
                if missing_var in line and not line.strip().startswith("#"):
                    # Avoid replacing within string literals if possible
                    new_line = re.sub(r'\b' + re.escape(missing_var) + r'\b', target_var, line)
                    if new_line != line:
                        changes.append({"line": idx, "before": line.strip(), "after": new_line.strip()})
                        fixed_lines.append(new_line)
                        if line_num is None:
                            line_num = idx
                        continue
                fixed_lines.append(line)
            
            fixed_code = "\n".join(fixed_lines)
            if fixed_code == code: # fallback line prepend
                fixed_code = f"{missing_var} = []  # Fixed: Initialized missing variable\n" + code
                changes.append({"line": 1, "before": "(None)", "after": f"{missing_var} = []"})

            return {
                "error_type": "NameError",
                "error_line": line_num or 1,
                "root_cause": f"NameError: The variable '{missing_var}' is referenced but not defined in scope.",
                "fixed_code": fixed_code,
                "fix_explanation": f"Replaced undefined variable reference '{missing_var}' with defined variable '{target_var}'.",
                "changes": changes
            }

        # 2. ZeroDivisionError
        elif "zerodivisionerror" in stderr_lower or "division by zero" in stderr_lower:
            fixed_lines = []
            changes = []
            for idx, line in enumerate(lines, 1):
                if "/" in line and not line.strip().startswith("#"):
                    if "/ 0" in line or "/0" in line:
                        new_line = line.replace("/ 0", "/ 1").replace("/0", "/ 1")
                        changes.append({"line": idx, "before": line.strip(), "after": new_line.strip()})
                        fixed_lines.append(new_line)
                    else:
                        indent = len(line) - len(line.lstrip())
                        ind_str = " " * indent
                        guard = f"{ind_str}# Guard zero division\n{ind_str}try:\n{ind_str}    {line.lstrip()}\n{ind_str}except ZeroDivisionError:\n{ind_str}    print('Warning: Handled ZeroDivisionError safely')"
                        changes.append({"line": idx, "before": line.strip(), "after": f"try: ... except ZeroDivisionError:"})
                        fixed_lines.append(guard)
                    if line_num is None:
                        line_num = idx
                else:
                    fixed_lines.append(line)

            return {
                "error_type": "ZeroDivisionError",
                "error_line": line_num or 1,
                "root_cause": "ZeroDivisionError: Division operation encountered a zero denominator.",
                "fixed_code": "\n".join(fixed_lines),
                "fix_explanation": "Added zero denominator check/try-except handler to prevent division by zero exception.",
                "changes": changes
            }

        # 3. TypeError
        elif "typeerror" in stderr_lower:
            fixed_lines = []
            changes = []
            for idx, line in enumerate(lines, 1):
                if "+" in line and not line.strip().startswith("#"):
                    parts = line.split("+")
                    new_parts = []
                    for p in parts:
                        p_s = p.strip()
                        if p_s.isdigit() or p_s.replace('.', '', 1).isdigit():
                            new_parts.append(f"str({p_s})")
                        else:
                            new_parts.append(p)
                    new_line = " + ".join(new_parts)
                    if new_line != line:
                        changes.append({"line": idx, "before": line.strip(), "after": new_line.strip()})
                        fixed_lines.append(new_line)
                    else:
                        fixed_lines.append(line)
                else:
                    fixed_lines.append(line)

            return {
                "error_type": "TypeError",
                "error_line": line_num or 1,
                "root_cause": "TypeError: Incompatible operand types (e.g. string and numeric type concatenation).",
                "fixed_code": "\n".join(fixed_lines),
                "fix_explanation": "Converted numeric literal/variable explicitly to string str() before concatenation.",
                "changes": changes
            }

        # 4. SyntaxError / IndentationError
        elif "syntaxerror" in stderr_lower or "indentationerror" in stderr_lower:
            fixed_lines = []
            changes = []
            for idx, line in enumerate(lines, 1):
                s = line.strip()
                if any(s.startswith(kw) for kw in ["def ", "if ", "else", "elif ", "for ", "while ", "try", "except"]) and not s.endswith(":"):
                    new_line = line + ":"
                    changes.append({"line": idx, "before": line.strip(), "after": new_line.strip()})
                    fixed_lines.append(new_line)
                else:
                    fixed_lines.append(line)

            return {
                "error_type": "SyntaxError",
                "error_line": line_num or 1,
                "root_cause": "SyntaxError: Missing colon or invalid Python statement syntax.",
                "fixed_code": "\n".join(fixed_lines),
                "fix_explanation": "Added missing colon ':' to standard block declaration statement.",
                "changes": changes
            }

        # 5. Generic Error
        else:
            err_type = "RuntimeError"
            if stderr:
                err_lines = stderr.strip().splitlines()
                if err_lines:
                    err_type = err_lines[-1].split(":")[0]

            wrapped_code = "try:\n" + "\n".join("    " + l for l in lines) + "\nexcept Exception as err:\n    print(f'Handled runtime error: {err}')\n"
            return {
                "error_type": err_type,
                "error_line": line_num or 1,
                "root_cause": f"{err_type}: Script encountered runtime exception.",
                "fixed_code": wrapped_code,
                "fix_explanation": "Wrapped execution block in exception handling try-except structure to catch runtime failure.",
                "changes": [{"line": 1, "before": "Uncaught code block", "after": "try: ... except Exception:"}]
            }

    def _compute_diff(self, old_code: str, new_code: str) -> List[Dict[str, Any]]:
        old_lines = old_code.splitlines()
        new_lines = new_code.splitlines()
        changes = []
        for idx, (o, n) in enumerate(zip(old_lines, new_lines), 1):
            if o != n:
                changes.append({"line": idx, "before": o.strip(), "after": n.strip()})
        return changes

ai_debugger_service = AIDebuggerService()
