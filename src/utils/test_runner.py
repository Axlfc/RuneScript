import subprocess
import logging
from typing import NamedTuple


class TestResult(NamedTuple):
    success: bool
    stdout: str
    stderr: str


def run_pytest(project_path: str) -> TestResult:
    """
    Executes pytest in the specified project directory.

    Returns:
        TestResult(success, stdout, stderr)
    """
    try:
        result = subprocess.run(
            ['pytest'],
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            cwd=project_path
        )

        return TestResult(
            success=result.returncode == 0,
            stdout=result.stdout.strip(),
            stderr=result.stderr.strip()
        )

    except Exception as e:
        logging.error(f"Test runner failed: {e}")
        return TestResult(False, "", str(e))

