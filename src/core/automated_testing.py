import logging
import subprocess
import sys


class AutomatedTestingFramework:
    def __init__(self, project_path):
        self.project_path = project_path
        self.last_result = {
            "success": None,
            "returncode": None,
            "stdout": "",
            "stderr": "",
        }

    def run_tests(self):
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "--maxfail=5",
                    "--disable-warnings",
                    "--tb=short",
                ],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=180,
            )

            success = result.returncode == 0
            self.last_result = {
                "success": success,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

            logging.info(result.stdout)
            if result.stderr:
                logging.warning(result.stderr)
            return success

        except Exception as e:
            message = str(e)
            self.last_result = {
                "success": False,
                "returncode": None,
                "stdout": "",
                "stderr": message,
            }
            logging.error(f"Automated testing failed: {message}")
            return False
