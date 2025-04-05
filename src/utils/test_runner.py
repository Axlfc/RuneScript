import subprocess
import logging
from typing import Optional, Tuple


def run_pytest(project_path: str) -> Tuple[bool, str, str]:
    """
    Executes pytest in the specified project directory.

    Returns:
        (success: bool, stdout: str, stderr: str)
    """
    try:
        result = subprocess.run(
            ['pytest'],
            capture_output=True,
            text=True,
            cwd=project_path
        )

        success = result.returncode == 0
        return success, result.stdout.strip(), result.stderr.strip()

    except Exception as e:
        logging.error(f"Test runner failed: {e}")
        return False, "", str(e)
