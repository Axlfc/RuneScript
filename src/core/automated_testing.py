import subprocess
import logging
import os

class AutomatedTestingFramework:
    def __init__(self, project_path):
        self.project_path = project_path

    def run_tests(self):
        try:
            result = subprocess.run([
                "pytest", "--maxfail=5", "--disable-warnings", "--tb=short"
            ], cwd=self.project_path, capture_output=True, text=True)

            logging.info(result.stdout)
            if result.stderr:
                logging.warning(result.stderr)
            return result.returncode == 0

        except Exception as e:
            logging.error(f"Automated testing failed: {e}")
            return False
