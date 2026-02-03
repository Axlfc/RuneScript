from pathlib import Path
from enum import Enum
import sys
import json
import subprocess
import logging
from .tech_detector import TechStackDetector

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

    def validate_red(self, project_path: Path, test_file: str, test_name: str = None, venv_python: str = None) -> ValidationResult:
        """
        Validate RED phase: test must FAIL.
        """
        result = self._run_test(project_path, test_file, test_name, venv_python)

        # CRITICAL: Check for execution errors (file not found, etc.)
        execution_errors = [
            "no puede encontrar la ruta",
            "no such file or directory",
            "command not found",
            "is not recognized as an internal or external command"
        ]

        has_execution_error = any(err.lower() in result.stderr.lower() for err in execution_errors)

        if has_execution_error:
            return ValidationResult(
                success=False,
                message=f"RED phase failed: Execution error detected (not a test failure). Check paths and environment.",
                stdout=result.stdout,
                stderr=result.stderr
            )

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

    def validate_green(self, project_path: Path, test_file: str, test_name: str = None, venv_python: str = None) -> ValidationResult:
        """
        Validate GREEN phase: test must PASS.
        """
        result = self._run_test(project_path, test_file, test_name, venv_python)

        # Check for execution errors
        execution_errors = [
            "no puede encontrar la ruta",
            "no such file or directory",
            "command not found",
            "is not recognized as an internal or external command"
        ]
        has_execution_error = any(err.lower() in result.stderr.lower() for err in execution_errors)

        if has_execution_error:
            return ValidationResult(
                success=False,
                message=f"GREEN phase failed: Execution error detected. Check paths and environment.",
                stdout=result.stdout,
                stderr=result.stderr
            )

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

        # Check for execution errors
        execution_errors = [
            "no puede encontrar la ruta",
            "no such file or directory",
            "command not found",
            "is not recognized as an internal or external command"
        ]
        has_execution_error = any(err.lower() in result.stderr.lower() for err in execution_errors)

        if has_execution_error:
            return ValidationResult(
                success=False,
                message=f"REFACTOR failed: Execution error detected. Check paths and environment.",
                stdout=result.stdout,
                stderr=result.stderr
            )

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

    def _run_test(self, project_path: Path, test_file: str, test_name: str = None, venv_python: str = None):
        """Run single test with appropriate runner."""
        project_path = Path(project_path)

        # 1. Try to get tech config from .nia_config.json
        config_path = project_path / ".nia_config.json"
        tech_config = {}
        if config_path.exists():
            try:
                nia_config = json.loads(config_path.read_text(encoding='utf-8'))
                tech_config = nia_config.get("tech_config", {})
            except:
                pass

        # 2. Determine command
        # Ensure python_exe is absolute to avoid issues when changing CWD
        python_exe = os.path.abspath(venv_python) if venv_python else sys.executable

        # Make test_file relative to project_path if it's absolute
        try:
            rel_test_file = Path(test_file).relative_to(project_path)
        except ValueError:
            rel_test_file = Path(test_file)

        # VERIFY TEST FILE EXISTS
        full_test_path = (project_path / rel_test_file).absolute()
        if not full_test_path.exists():
            msg = f"Test file not found: {full_test_path}"
            logging.error(msg)
            return subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr=msg)

        # PROPERLY QUOTE PATHS (Especially for Windows)
        # Use absolute paths in the command string to be 100% sure
        q_python = f'"{python_exe}"'
        q_test_file = f'"{full_test_path}"'

        test_command_template = tech_config.get("test_command")

        if test_command_template:
            # Use template from config
            # We use full_test_path instead of rel_test_file for better reliability
            cmd_str = test_command_template.format(
                python=q_python,
                test_file=str(full_test_path), # Template might already have quotes or handle it
                test_name=test_name or ""
            )

            # Ensure test_file is quoted in cmd_str if it's not already
            if str(full_test_path) in cmd_str and f'"{full_test_path}"' not in cmd_str:
                cmd_str = cmd_str.replace(str(full_test_path), q_test_file)

            # For pytest with test_name, we might need a better template approach,
            # but for now let's handle it manually if test_name exists and using pytest
            if "pytest" in cmd_str and test_name and "::" not in cmd_str:
                # Replace quoted test file with quoted test file + ::test_name
                cmd_str = cmd_str.replace(q_test_file, f'"{full_test_path}::{test_name}"')

            logging.info(f"Executing test command: {cmd_str} (CWD: {project_path})")
            return subprocess.run(
                cmd_str,
                shell=True,
                cwd=str(project_path),
                capture_output=True,
                encoding='utf-8',
                errors='replace'
            )

        # Fallback to old logic if no tech_config
        logging.info(f"Running test fallback for: {rel_test_file} (CWD: {project_path})")
        if str(rel_test_file).endswith('.py'):
            # Check if it's a pytest file or a simple script
            try:
                with open(full_test_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # If it uses pytest explicitly (import pytest)
                if "import pytest" in content:
                    cmd = [python_exe, "-m", "pytest", str(rel_test_file)]
                    if test_name:
                        cmd = [python_exe, "-m", "pytest", f"{rel_test_file}::{test_name}", "-v"]
                    else:
                        cmd.append("-v")
                else:
                    # Execute as standalone script
                    cmd = [python_exe, str(rel_test_file)]
            except Exception as e:
                logging.warning(f"Error deciding test runner for {test_file}: {e}")
                cmd = [python_exe, str(rel_test_file)]
        elif str(rel_test_file).endswith(('.js', '.ts')):
            cmd = ["npm", "test", "--", str(rel_test_file)]
        else:
            # Default fallback
            cmd = [python_exe, "-m", "pytest", str(rel_test_file)]
            if test_name:
                cmd = [python_exe, "-m", "pytest", f"{rel_test_file}::{test_name}", "-v"]
            else:
                cmd.append("-v")

        logging.info(f"Executing: {' '.join(cmd)}")
        return subprocess.run(
            cmd,
            cwd=str(project_path),
            capture_output=True,
            encoding='utf-8',
            errors='replace'
        )

    def _run_all_tests(self, project_path: Path, venv_python: str = None):
        """Run all tests with appropriate runner."""
        project_path = Path(project_path)

        # Try to get tech config
        config_path = project_path / ".nia_config.json"
        tech_config = {}
        if config_path.exists():
            try:
                nia_config = json.loads(config_path.read_text(encoding='utf-8'))
                tech_config = nia_config.get("tech_config", {})
            except:
                pass

        python_exe = venv_python or sys.executable

        # Check for package.json (Node.js)
        if (project_path / "package.json").exists():
            return subprocess.run(
                ["npm", "test"],
                cwd=str(project_path),
                capture_output=True,
                encoding='utf-8',
                errors='replace'
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
            cmd = [python_exe, "-m", "pytest", "."]
        else:
            # Run all test files as individual scripts
            # For simplicity, return result of the first failing test or the last success
            last_result = None
            for py_file in test_dir.glob("**/test*.py"):
                # Use relative path for command if possible to avoid issues
                try:
                    rel_py_file = py_file.relative_to(project_path)
                except ValueError:
                    rel_py_file = py_file

                if venv_python:
                    cmd = [venv_python, str(rel_py_file)]
                else:
                    cmd = [sys.executable, str(rel_py_file)]

                last_result = subprocess.run(
                    cmd,
                    cwd=str(project_path),
                    capture_output=True,
                    encoding='utf-8',
                    errors='replace'
                )
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
            encoding='utf-8',
            errors='replace'
        )
