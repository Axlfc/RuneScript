from pathlib import Path
from enum import Enum
import sys
import os
import shlex
import json
import subprocess
import logging
import time
import re
import threading
from .tech_detector import TechStackDetector
from src.security.sandbox import SecureSandbox
from src.security.code_analyzer import CodeSecurityAnalyzer
from src.security.exceptions import SecurityException

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

    def __init__(self, security_auditor=None):
        self.security_auditor = security_auditor
        self.sandbox = SecureSandbox()
        self.analyzer = CodeSecurityAnalyzer()
        self.allowed_imports = ['pytest', 'bs4', 'beautifulsoup4', 're', 'json', 'math', 'unittest', 'os', 'pathlib']

    def add_allowed_import(self, module_name: str):
        """Dynamically add a module to the sandbox whitelist."""
        if module_name not in self.allowed_imports:
            self.allowed_imports.append(module_name)

    def validate_red(self, project_path: Path, test_file: str, test_name: str = None, venv_python: str = None, output_callback=None) -> ValidationResult:
        """
        Validate RED phase: test must FAIL.
        """
        result = self._run_test(project_path, test_file, test_name, venv_python, output_callback=output_callback)

        # CRITICAL: Check for execution errors (file not found, etc.)
        execution_errors = [
            "no puede encontrar la ruta",
            "no such file or directory",
            "command not found",
            "is not recognized as an internal or external command",
            "test file not found",
            "python executable not found",
            "ModuleNotFoundError: No module named 'selenium'",
            "Process exceeded time limit",
            "Execution timed out"
        ]

        has_execution_error = any(err.lower() in result.stderr.lower() for err in execution_errors)

        if has_execution_error:
            msg = "RED phase failed: Execution error detected"
            if "time limit" in result.stderr.lower() or "timed out" in result.stderr.lower():
                msg = "RED phase failed: Execution timed out"

            return ValidationResult(
                success=False,
                message=f"{msg} (not a test failure). Check paths and environment.",
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

    def validate_green(self, project_path: Path, test_file: str, test_name: str = None, venv_python: str = None, output_callback=None) -> ValidationResult:
        """
        Validate GREEN phase: test must PASS.
        """
        result = self._run_test(project_path, test_file, test_name, venv_python, output_callback=output_callback)

        # Check for execution errors
        execution_errors = [
            "no puede encontrar la ruta",
            "no such file or directory",
            "command not found",
            "is not recognized as an internal or external command",
            "test file not found",
            "python executable not found",
            "Process exceeded time limit",
            "Execution timed out"
        ]
        has_execution_error = any(err.lower() in result.stderr.lower() for err in execution_errors)

        if has_execution_error:
            msg = "GREEN phase failed: Execution error detected"
            if "time limit" in result.stderr.lower() or "timed out" in result.stderr.lower():
                msg = "GREEN phase failed: Execution timed out"

            return ValidationResult(
                success=False,
                message=f"{msg}. Check paths and environment.",
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

    def validate_refactor(self, project_path: Path, venv_python: str = None, output_callback=None) -> ValidationResult:
        """
        Validate REFACTOR phase: ALL tests must still pass.
        """
        result = self._run_all_tests(project_path, venv_python, output_callback=output_callback)

        # Check for execution errors
        execution_errors = [
            "no puede encontrar la ruta",
            "no such file or directory",
            "command not found",
            "is not recognized as an internal or external command",
            "test file not found",
            "python executable not found",
            "Process exceeded time limit",
            "Execution timed out"
        ]
        has_execution_error = any(err.lower() in result.stderr.lower() for err in execution_errors)

        if has_execution_error:
            msg = "REFACTOR failed: Execution error detected"
            if "time limit" in result.stderr.lower() or "timed out" in result.stderr.lower():
                msg = "REFACTOR failed: Execution timed out"

            return ValidationResult(
                success=False,
                message=f"{msg}. Check paths and environment.",
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

    def _extract_file_dependencies_from_test(self, project_path: Path, test_file: Path) -> list:
        """Extrae archivos que el test espera que existan."""
        try:
            if not test_file.exists():
                return []
            content = test_file.read_text(encoding='utf-8', errors='replace')
            files = []
            # Pattern 1: os.path.join patterns
            join_pattern = r'os\.path\.join\([^)]*["\']([^"\']+)["\']'
            files.extend(re.findall(join_pattern, content))
            # Pattern 2: Direct file references
            file_pattern = r'["\']([a-zA-Z0-9_/.-]+\.(html|css|js|py))["\']'
            files.extend([m[0] for m in re.findall(file_pattern, content)])
            # Pattern 3: CSS/JS paths in HTML checks
            if 'css/' in content or 'js/' in content:
                files.extend(['index.html', 'css/style.css', 'js/app.js', 'css/main.css', 'js/main.js'])
            # Normalize and filter
            result = []
            for f in set(files):
                # Clean up dots if they are at the start of a path like ../index.html
                clean_f = f.lstrip('./').lstrip('../')
                if clean_f and '.' in clean_f:
                    result.append(clean_f)
            return list(set(result))
        except Exception as e:
            logging.warning(f"Error extracting dependencies from test: {e}")
            return []

    def _run_test(self, project_path: Path, test_file: str, test_name: str = None, venv_python: str = None, output_callback=None):
        """Run single test with appropriate runner."""
        project_path = Path(project_path)

        logging.info(f"=== PREPARING TEST EXECUTION ===")
        logging.info(f"Test file: {test_file}")
        logging.info(f"Working directory: {project_path}")

        # 0. Sync and Verify dependencies
        # Esperar un momento para que el filesystem sincronice
        time.sleep(0.1)

        # Verify dependencies mentioned in test
        test_file_path = Path(test_file)
        if not test_file_path.is_absolute():
            test_file_path = project_path / test_file_path

        deps = self._extract_file_dependencies_from_test(project_path, test_file_path)
        if deps:
            logging.info(f"Checking test dependencies: {deps}")
            missing = []
            for dep in deps:
                # Try relative to project root first
                dep_path = project_path / dep
                if not dep_path.exists():
                    # If it starts with ../ it might be looking for something outside tests but in project
                    missing.append(dep)

            if missing:
                # We log it as a warning but continue; the test will likely fail with a better error
                logging.warning(f"⚠️ Missing files referenced in test: {missing}")

        # List files in project for diagnostics
        logging.info("Existing project files:")
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if d not in ['.venv', '.git', '__pycache__', 'node_modules']]
            rel_root = os.path.relpath(root, project_path)
            for file in sorted(files):
                full_rel = os.path.join(rel_root, file) if rel_root != "." else file
                logging.info(f"  - {full_rel}")

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

        # CRITICAL: Verify Python exists
        if not os.path.exists(python_exe):
            msg = f"Python executable not found: {python_exe}"
            logging.error(f"❌ {msg}")
            return subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr=msg)

        # Make test_file relative to project_path if it's absolute
        try:
            rel_test_file = Path(test_file).relative_to(project_path)
        except ValueError:
            rel_test_file = Path(test_file)

        # VERIFY TEST FILE EXISTS
        full_test_path = (project_path / rel_test_file).absolute()
        if not full_test_path.exists():
            msg = f"Test file not found: {full_test_path}"
            logging.error(f"❌ {msg}")
            return subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr=msg)

        # DEFCON 1: Security Analysis & Sandboxing for Python tests
        if str(rel_test_file).endswith('.py'):
            try:
                # Decide if we should skip analysis for autogenerated tests
                # Normalize path for cross-platform comparison
                normalized_rel_path = str(rel_test_file).replace('\\', '/')

                # If it's in tests/ directory, we consider it autogenerated/safe-by-definition
                is_autogenerated_test = normalized_rel_path.startswith('tests/')

                with open(full_test_path, 'r', encoding='utf-8') as f:
                    code = f.read()

                # 1. AST Analysis (with whitelist if it's a test)
                analysis = self.analyzer.analyze(code, is_test=is_autogenerated_test)

                # If it's an autogenerated test and still fails, we might want to be even more permissive
                # but for now, we follow the directive to skip analysis if it's an autogenerated test
                # OR use the whitelist. The user said "Skip analysis for autogenerated tests" in one place
                # and "Whitelist permisiva para tests autogenerados" in another.
                # Let's go with skipping analysis for autogenerated tests as the main directive.

                # If it's an autogenerated test, we are more permissive
                # We already passed is_test=is_autogenerated_test to analyze()
                # which handles the whitelist in Step 2 and Step 3.

                # As per decision DA-003: Skip analysis for autogenerated tests
                # to avoid blocking legitimate testing infrastructure.
                if is_autogenerated_test:
                    analysis['is_safe'] = True
                    analysis['threats'] = []

                if not analysis['is_safe']:
                    msg = f"Security Violation: Test file {rel_test_file} failed code analysis"
                    if self.security_auditor:
                        self.security_auditor.log_security_violation(
                            severity='CRITICAL',
                            category='MALICIOUS_TEST_CODE',
                            description=msg,
                            threats=analysis['threats']
                        )
                    return subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr=msg)

                # 2. Sandbox Execution
                # For now, if it's a simple test, we run it in the Python sandbox.
                # If it's a complex pytest, we might still need a more robust runner,
                # but let's try the sandbox first.
                self.sandbox.timeout = 180 # Match sandbox default for tests

                # Use dynamic whitelist from instance attribute
                allowed = self.allowed_imports

                # Check if we should use pytest
                is_pytest = "import pytest" in code or "def test_" in code

                result = self.sandbox.execute(
                    code,
                    allowed_imports=allowed,
                    cwd=str(project_path),
                    use_pytest=is_pytest
                )

                if self.security_auditor:
                    self.security_auditor.log_code_execution(code, source=str(rel_test_file), approved=result['success'], result=result)

                final_res = subprocess.CompletedProcess(
                    args=['sandbox', str(rel_test_file)],
                    returncode=0 if result['success'] else 1,
                    stdout=result['stdout'] or "",
                    stderr=result['stderr'] or (result['error'] if not result['success'] else "") or ""
                )

                if output_callback:
                    if final_res.stdout:
                        for line in final_res.stdout.splitlines():
                            output_callback(line, 'stdout')
                    if final_res.stderr:
                        for line in final_res.stderr.splitlines():
                            output_callback(line, 'stderr')

                return final_res

            except Exception as e:
                logging.error(f"Error during sandboxed test execution: {e}")
                # Fallback to subprocess if sandbox fails? No, for DEFCON 1, we fail.
                return subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr=f"Sandbox error: {e}")

        test_command_template = tech_config.get("test_command")

        if test_command_template:
            # Use template from config
            # We use full_test_path instead of rel_test_file for better reliability
            # NOTE: We DO NOT quote here, subprocess handles it with shell=False when passed as a list

            # If the template has hardcoded quotes, we try to honor them but shlex.split should handle it
            cmd_str = test_command_template.format(
                python=python_exe,
                test_file=str(full_test_path),
                test_name=test_name or ""
            )

            if "pytest" in cmd_str and test_name and "::" not in cmd_str:
                 # Logic to append test name if using pytest
                 cmd_str = cmd_str.replace(str(full_test_path), f"{full_test_path}::{test_name}")

            # shlex.split handles spaces and quotes correctly to produce a list
            # We use posix=False on Windows if needed, but usually posix=True is fine for basic commands
            cmd = shlex.split(cmd_str, posix=(os.name != 'nt'))

            logging.info(f"Executing test command (list): {cmd} (CWD: {project_path})")

            if output_callback:
                return self._run_with_streaming(cmd, project_path, output_callback)

            # Week 1 Fix: Add timeout to test execution
            return subprocess.run(
                cmd,
                shell=False,
                cwd=str(project_path),
                capture_output=True,
                encoding='utf-8',
                errors='replace',
                timeout=180
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
                    # Explicitly ignore common noise dirs even when running single file to be safe
                    cmd = [python_exe, "-m", "pytest", str(full_test_path), "-v", "--ignore=.venv", "--ignore=venv"]
                    if test_name:
                         cmd = [python_exe, "-m", "pytest", f"{full_test_path}::{test_name}", "-v", "--ignore=.venv", "--ignore=venv"]
                else:
                    # Execute as standalone script
                    cmd = [python_exe, str(full_test_path)]
            except Exception as e:
                logging.warning(f"Error deciding test runner for {test_file}: {e}")
                cmd = [python_exe, str(full_test_path)]
        elif str(rel_test_file).endswith(('.js', '.ts')):
            # For npm, we might still need shell=True on Windows because npm is a .cmd/.bat
            # but let's try with shell=False and full path to npm if possible,
            # or just use the suggested robust way for npm.
            cmd = ["npm.cmd" if os.name == 'nt' else "npm", "test", "--", str(full_test_path)]
        else:
            # Default fallback
            cmd = [python_exe, "-m", "pytest", str(full_test_path), "-v", "--ignore=.venv", "--ignore=venv"]
            if test_name:
                cmd = [python_exe, "-m", "pytest", f"{full_test_path}::{test_name}", "-v", "--ignore=.venv", "--ignore=venv"]

        logging.info(f"Executing (list): {cmd}")

        if output_callback:
            return self._run_with_streaming(cmd, project_path, output_callback)

        # Week 1 Fix: Add timeout to test execution
        return subprocess.run(
            cmd,
            shell=False,
            cwd=str(project_path),
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=180
        )

    def _run_with_streaming(self, cmd, cwd, callback):
        """Run a command and stream its output via callback."""
        stdout_lines = []
        stderr_lines = []

        process = subprocess.Popen(
            cmd,
            shell=False,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            errors='replace',
            bufsize=1,
            universal_newlines=True
        )

        def read_stream(stream, out_type):
            for line in stream:
                line = line.rstrip()
                callback(line, out_type)
                if out_type == 'stdout':
                    stdout_lines.append(line)
                else:
                    stderr_lines.append(line)

        t1 = threading.Thread(target=read_stream, args=(process.stdout, 'stdout'))
        t2 = threading.Thread(target=read_stream, args=(process.stderr, 'stderr'))

        t1.start()
        t2.start()

        # Week 1 Fix: Prevent indefinite hangs during streamed test execution
        try:
            returncode = process.wait(timeout=180)
        except subprocess.TimeoutExpired:
            process.kill()
            returncode = 1
            logging.error("Test execution timed out after 60s")
        t1.join()
        t2.join()

        return subprocess.CompletedProcess(
            args=cmd,
            returncode=returncode,
            stdout='\n'.join(stdout_lines),
            stderr='\n'.join(stderr_lines)
        )

    def _run_all_tests(self, project_path: Path, venv_python: str = None, output_callback=None):
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
            npm_cmd = "npm.cmd" if os.name == 'nt' else "npm"
            # Week 1 Fix: Add timeout to test execution
            return subprocess.run(
                [npm_cmd, "test"],
                shell=False,
                cwd=str(project_path),
                capture_output=True,
                encoding='utf-8',
                errors='replace',
                timeout=240
            )

        # Python/Pytest
        # Buscar si algún archivo de test usa pytest
        uses_pytest = False
        test_dir = project_path / "tests"
        if not test_dir.exists():
            test_dir = project_path

        for py_file in test_dir.glob("**/test_*.py"):
            try:
                if "import pytest" in py_file.read_text(encoding='utf-8'):
                    uses_pytest = True
                    break
            except Exception:
                pass

        if uses_pytest:
            # For REFACTOR phase, running all tests in sandbox
            # We can't easily run multiple files with our current sandbox.execute
            # so we'll run a script that calls pytest on the whole directory.
            code = "import pytest\nimport sys\nsys.exit(pytest.main(['.', '-v', '--ignore=.venv', '--ignore=venv', '--ignore=node_modules']))"

            # Ensure sys is available for this specific execution
            allowed = list(set(self.allowed_imports + ['sys']))

            result = self.sandbox.execute(code, allowed_imports=allowed, cwd=str(project_path))

            final_res = subprocess.CompletedProcess(
                args=['sandbox', 'all_tests'],
                returncode=0 if result['success'] else 1,
                stdout=result['stdout'] or "",
                stderr=result['stderr'] or (result['error'] if not result['success'] else "") or ""
            )

            if output_callback:
                if final_res.stdout:
                    for line in final_res.stdout.splitlines():
                        output_callback(line, 'stdout')
                if final_res.stderr:
                    for line in final_res.stderr.splitlines():
                        output_callback(line, 'stderr')

            return final_res
        else:
            # Run all test files as individual scripts in sandbox
            last_result = None
            for py_file in test_dir.glob("**/test_*.py"):
                try:
                    code = py_file.read_text(encoding='utf-8')
                    # Basic check - ensure it's analyzed as a test to use permissive whitelist
                    analysis = self.analyzer.analyze(code, is_test=True)
                    if not analysis['is_safe']:
                         threats_msg = ", ".join([t['description'] for t in analysis.get('threats', [])])
                         return subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr=f"Security Violation in test file {py_file.name}: {threats_msg}")

                    allowed = self.allowed_imports
                    is_pytest = "import pytest" in code or "def test_" in code

                    res = self.sandbox.execute(code, allowed_imports=allowed, cwd=str(project_path), use_pytest=is_pytest)

                    last_result = subprocess.CompletedProcess(
                        args=['sandbox', str(py_file)],
                        returncode=0 if res['success'] else 1,
                        stdout=res['stdout'] or "",
                        stderr=res['stderr'] or (res['error'] if not res['success'] else "") or ""
                    )
                    if last_result.returncode != 0:
                        return last_result
                except:
                    pass

            if last_result:
                return last_result

            # Si no hay archivos de test
            return subprocess.CompletedProcess(args=[], returncode=0, stdout="No tests found", stderr="")

        # Fallback (should not reach here with new logic)
        return subprocess.CompletedProcess(args=[], returncode=0, stdout="Success", stderr="")
