from pathlib import Path
from enum import Enum
import sys
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

                    # If it uses pytest explicitly (import pytest)
                    if "import pytest" in content:
                        # Asegurarse de que pytest esté instalado
                        try:
                            subprocess.run([venv_python, "-m", "pytest", "--version"], capture_output=True, check=True)
                        except (subprocess.CalledProcessError, FileNotFoundError):
                            logging.info(f"Installing pytest in venv: {venv_python}")
                            subprocess.run([venv_python, "-m", "pip", "install", "pytest"], capture_output=True)

                        cmd = [venv_python, "-m", "pytest", test_file]
                        if test_name:
                            # Ajustar comando para pytest con nombre de test específico
                            cmd = [venv_python, "-m", "pytest", f"{test_file}::{test_name}", "-v"]
                        else:
                            cmd.append("-v")
                    else:
                        # Ejecutar como script independiente
                        cmd = [venv_python, test_file]
                except Exception as e:
                    logging.warning(f"Error deciding test runner for {test_file}: {e}")
                    cmd = [venv_python, test_file]
            else:
                cmd = [sys.executable, test_file]
        elif test_file.endswith(('.js', '.ts')):
            cmd = ["npm", "test", "--", test_file]
        else:
            # Default fallback using system python -m pytest to avoid [WinError 2]
            cmd = [sys.executable, "-m", "pytest", test_file]
            if test_name:
                cmd = [sys.executable, "-m", "pytest", f"{test_file}::{test_name}", "-v"]
            else:
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
        # Buscar si algún archivo de test usa pytest
        uses_pytest = False
        test_dir = project_path / "tests"
        if not test_dir.exists():
            test_dir = project_path

        for py_file in test_dir.glob("**/test*.py"):
            try:
                if "import pytest" in py_file.read_text(encoding='utf-8'):
                    uses_pytest = True
                    break
            except Exception:
                pass

        if uses_pytest:
            if venv_python:
                # Ensure pytest is installed
                subprocess.run([venv_python, "-m", "pip", "install", "pytest"], capture_output=True)
                cmd = [venv_python, "-m", "pytest", "."]
            else:
                cmd = [sys.executable, "-m", "pytest", "."]
        else:
            # Run all test files as individual scripts
            # For simplicity, return result of the first failing test or the last success
            last_result = None
            for py_file in test_dir.glob("**/test*.py"):
                if venv_python:
                    cmd = [venv_python, str(py_file)]
                else:
                    cmd = [sys.executable, str(py_file)]

                last_result = subprocess.run(cmd, capture_output=True, text=True)
                if last_result.returncode != 0:
                    return last_result

            if last_result:
                return last_result

            # Si no hay archivos de test
            return subprocess.CompletedProcess(args=[], returncode=0, stdout="No tests found", stderr="")

        return subprocess.run(
            cmd,
            cwd=str(project_path),
            capture_output=True,
            text=True
        )
