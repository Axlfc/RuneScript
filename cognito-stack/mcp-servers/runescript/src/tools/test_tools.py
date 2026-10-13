import re
import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from ..sandbox import sandbox_execute

class RunTestsInput(BaseModel):
    path: Optional[str] = Field(default=None, description="Specific test file or directory path relative to RUNESCRIPT_PATH.")
    framework: str = Field(default="pytest", description="Testing framework (pytest).")
    timeout: int = Field(default=300, ge=10, le=600, description="Execution timeout in seconds.")

def parse_pytest_output(stdout: str, stderr: str, exit_code: int) -> Dict[str, Any]:
    """Parses pytest summary output line."""
    passed = 0
    failed = 0
    errors = 0
    duration = 0.0

    # Match summary line like "=== 20 passed in 4.77s ===" or "=== 2 failed, 10 passed in 2.15s ==="
    summary_match = re.search(r"=+\s*(.*?)\s+in\s+([\d\.]+)s\s*=+", stdout)
    if summary_match:
        summary_str = summary_match.group(1)
        try:
            duration = float(summary_match.group(2))
        except ValueError:
            duration = 0.0

        passed_m = re.search(r"(\d+)\s+passed", summary_str)
        failed_m = re.search(r"(\d+)\s+failed", summary_str)
        errors_m = re.search(r"(\d+)\s+errors?", summary_str)

        if passed_m:
            passed = int(passed_m.group(1))
        if failed_m:
            failed = int(failed_m.group(1))
        if errors_m:
            errors = int(errors_m.group(1))

    return {
        "exit_code": exit_code,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "duration_seconds": duration,
        "stdout": stdout,
        "stderr": stderr
    }

async def run_tests(runescript_path: str, path: Optional[str] = None, framework: str = "pytest", timeout: int = 300) -> Dict[str, Any]:
    if framework.lower() != "pytest":
        raise ValueError(f"Unsupported testing framework '{framework}'. Only 'pytest' is supported.")

    target_path = path or "cognito-stack/mcp-servers/runescript/tests"

    script = f"""
import sys, subprocess, os
os.environ['PYTHONPATH'] = '{target_path.split('/tests')[0] if '/tests' in target_path else target_path}'
cmd = [sys.executable, '-m', 'pytest', '{target_path}']
proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
print(proc.stdout)
sys.stderr.write(proc.stderr)
sys.exit(proc.returncode)
"""

    res = await sandbox_execute(
        script=script,
        language="python",
        timeout=timeout,
        profile="trusted-tests",
        repo_path=runescript_path
    )

    return parse_pytest_output(
        stdout=res.get("stdout", ""),
        stderr=res.get("stderr", ""),
        exit_code=res.get("exit_code", -1)
    )
