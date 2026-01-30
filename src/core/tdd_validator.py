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

    def validate_red(self, test_file: str, test_name: str = None) -> ValidationResult:
        """
        Validate RED phase: test must FAIL.
        """
        result = self._run_test(test_file, test_name)

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

    def validate_green(self, test_file: str, test_name: str = None) -> ValidationResult:
        """
        Validate GREEN phase: test must PASS.
        """
        result = self._run_test(test_file, test_name)

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

    def validate_refactor(self, project_path: Path) -> ValidationResult:
        """
        Validate REFACTOR phase: ALL tests must still pass.
        """
        result = self._run_all_tests(project_path)

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

    def _run_test(self, test_file: str, test_name: str = None):
        """Run single test with pytest."""
        cmd = ["pytest", test_file]
        if test_name:
            cmd[1] = f"{test_file}::{test_name}"

        cmd.append("-v")

        return subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

    def _run_all_tests(self, project_path: Path):
        """Run all tests with pytest."""
        # Assume tests are in 'tests' directory
        test_dir = project_path / "tests"
        if not test_dir.exists():
            test_dir = project_path

        return subprocess.run(
            ["pytest", str(test_dir)],
            capture_output=True,
            text=True
        )
