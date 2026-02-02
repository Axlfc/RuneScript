from pathlib import Path
from enum import Enum
import subprocess
import logging

class CyclePhase(Enum):
    RED = "red"
    GREEN = "green"
    REFACTOR = "refactor"

class ValidationResult:
    def __init__(self, success: bool, message: str, stdout: str = "", stderr: str = ""):
        self.success = success
        self.message = message
        self.stdout = stdout
        self.stderr = stderr

class TDDValidator:
    """Validate each phase of TDD cycle."""

    def validate_red(self, test_file: str, test_name: str = None, venv_python: str = None) -> ValidationResult:
        """
        Validate RED phase: test must FAIL.
        """
        result = self._run_test(test_file, test_name, venv_python)

        # In RED phase, returncode != 0 is GOOD (test failed)
        if result.returncode == 0:
            return ValidationResult(
                success=False,
                message="RED phase failed: test passed when it should fail",
                stdout=result.stdout,
                stderr=result.stderr
            )

        return ValidationResult(
            success=True,
            message=f"RED phase ✓: test failed as expected",
            stdout=result.stdout,
            stderr=result.stderr
        )

    def validate_green(self, test_file: str, test_name: str = None, venv_python: str = None) -> ValidationResult:
        """
        Validate GREEN phase: test must PASS.
        """
        result = self._run_test(test_file, test_name, venv_python)

        if result.returncode != 0:
            return ValidationResult(
                success=False,
                message=f"GREEN phase failed: test still failing",
                stdout=result.stdout,
                stderr=result.stderr
            )

        return ValidationResult(
            success=True,
            message="GREEN phase ✓: test passing",
            stdout=result.stdout,
            stderr=result.stderr
        )

    def validate_refactor(self, project_path: Path, venv_python: str = None) -> ValidationResult:
        """
        Validate REFACTOR phase: ALL tests must still pass.
        """
        result = self._run_all_tests(project_path, venv_python)

        if result.returncode != 0:
            return ValidationResult(
                success=False,
                message=f"REFACTOR failed: regression detected",
                stdout=result.stdout,
                stderr=result.stderr
            )

        return ValidationResult(
            success=True,
            message="REFACTOR ✓: all tests still passing",
            stdout=result.stdout,
            stderr=result.stderr
        )

    def _run_test(self, test_file: str, test_name: str = None, venv_python: str = None):
        """Run single test with appropriate runner."""

        # Determine runner
        if test_file.endswith('.py'):
            if venv_python:
                # Check if it's a pytest file or a simple script
                try:
                    with open(test_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    if "pytest" in content or "def test_" in content:
                        cmd = [venv_python, "-m", "pytest", test_file]
                        if test_name:
                            cmd[3] = f"{test_file}::{test_name}"
                        cmd.append("-v")
                    else:
                        cmd = [venv_python, test_file]
                except Exception:
                    cmd = [venv_python, test_file]
            else:
                cmd = ["python", test_file]
        elif test_file.endswith(('.js', '.ts')):
            cmd = ["npm", "test", "--", test_file]
        else:
            cmd = ["pytest", test_file] # Default fallback
            if test_name:
                cmd[1] = f"{test_file}::{test_name}"
            cmd.append("-v")

        return subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

    def _run_all_tests(self, project_path: Path, venv_python: str = None):
        """Run all tests with appropriate runner."""
        # Check for package.json (Node.js)
        if (project_path / "package.json").exists():
            return subprocess.run(
                ["npm", "test"],
                cwd=str(project_path),
                capture_output=True,
                text=True
            )

        # Python/Pytest
        if venv_python:
            cmd = [venv_python, "-m", "pytest", "."]
        else:
            cmd = ["pytest", "."]

        return subprocess.run(
            cmd,
            cwd=str(project_path),
            capture_output=True,
            text=True
        )
