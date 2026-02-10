import multiprocessing
try:
    import resource
except ImportError:
    resource = None
import os
import sys
import signal
import traceback
import json
import builtins
import io
from .path_validator import ParanoidPathValidator
from .exceptions import SandboxExecutionError

class RestrictedImporter:
    """Custom import hook to whitelist modules in the sandbox."""

    def __init__(self, allowed_modules):
        self.allowed_modules = set(allowed_modules)
        if isinstance(builtins, dict):
            self.original_import = builtins['__import__']
        else:
            self.original_import = getattr(builtins, '__import__')

    def __call__(self, name, globals=None, locals=None, fromlist=(), level=0):
        module_name = name.split('.')[0]
        if module_name in self.allowed_modules or level > 0:
            return self.original_import(name, globals, locals, fromlist, level)

        raise ImportError(f"Import of '{name}' is forbidden in sandbox")

class SafeOpen:
    """A restricted version of open() that validates paths."""
    def __init__(self, base_dir):
        self.validator = ParanoidPathValidator(base_dir=base_dir)
        self.original_open = builtins.open

    def __call__(self, file, mode='r', *args, **kwargs):
        # Only allow reading for tests usually.
        # For security, let's start with read-only in the sandbox.
        if any(m in mode for m in ['w', 'a', 'x', '+']):
             raise PermissionError(f"Sandbox blocked write access to file: {file}")

        try:
            safe_path = self.validator.validate(str(file))
            return self.original_open(safe_path, mode, *args, **kwargs)
        except FileNotFoundError:
            # Let FileNotFoundError propagate naturally (expected in RED phase)
            raise
        except PermissionError:
            # Re-raise explicit permission errors
            raise
        except Exception as e:
            raise PermissionError(f"Sandbox blocked access to file: {file} - {e}")

class SecureSandbox:
    """Execute untrusted code in a multiprocessing-based sandbox."""

    def __init__(self, timeout=180, memory_limit_mb=512):
        self.timeout = timeout
        self.memory_limit = memory_limit_mb * 1024 * 1024

    def _apply_resource_limits(self):
        """Apply resource limits if the platform supports it."""
        if resource is None:
            return

        try:
            resource.setrlimit(resource.RLIMIT_CPU, (self.timeout, self.timeout + 5))
            resource.setrlimit(resource.RLIMIT_AS, (self.memory_limit, self.memory_limit))
            resource.setrlimit(resource.RLIMIT_FSIZE, (10 * 1024 * 1024, 10 * 1024 * 1024))
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
        except Exception:
            # Fallback for platforms where some limits might fail
            pass

    def execute(self, code, allowed_imports=None, cwd=None, use_pytest=False):
        """
        Execute code in a separate process with resource limits.
        """
        if allowed_imports is None:
            allowed_imports = ['pytest', 'bs4', 'beautifulsoup4', 'json', 're', 'math', 'unittest', 'os', 'pathlib']

        result_queue = multiprocessing.Queue()

        process = multiprocessing.Process(
            target=self._worker,
            args=(code, allowed_imports, cwd, use_pytest, result_queue)
        )

        process.start()
        process.join(self.timeout + 1)

        if process.is_alive():
            process.terminate()
            process.join()
            return {
                'success': False,
                'error': 'Execution timed out',
                'stdout': '',
                'stderr': 'Process exceeded time limit'
            }

        if result_queue.empty():
            exit_code = process.exitcode
            error_msg = f"Sandbox crashed or exited without result (Exit code: {exit_code})"

            # Common exit codes (Unix-specific signals handled safely for Windows)
            sigsegv = getattr(signal, 'SIGSEGV', None)
            sigabrt = getattr(signal, 'SIGABRT', None)
            sigkill = getattr(signal, 'SIGKILL', None)

            if sigsegv and exit_code == -sigsegv:
                error_msg += " - Segmentation fault"
            elif sigabrt and exit_code == -sigabrt:
                error_msg += " - Aborted"
            elif sigkill and exit_code == -sigkill:
                error_msg += " - Killed (possibly out of memory or timeout)"

            return {
                'success': False,
                'error': error_msg,
                'stdout': '',
                'stderr': error_msg
            }

        return result_queue.get()

    def execute_test(self, test_file_path, project_path, timeout=None, use_pytest=False):
        """
        Execute a test file in an isolated subprocess.
        This avoids multiprocessing 'spawn' issues on Windows where main.py is re-imported.
        """
        import subprocess

        if timeout is None:
            timeout = self.timeout

        # Construction of the command
        if use_pytest:
            # Use module execution for pytest to ensure it's picked up from the correct environment
            cmd = [sys.executable, "-m", "pytest", str(test_file_path), "-v", "--no-header"]
        else:
            cmd = [sys.executable, str(test_file_path)]

        # Environment setup: prevent .pyc files and set PYTHONPATH
        env = {
            **os.environ,
            'PYTHONDONTWRITEBYTECODE': '1',
            'PYTHONPATH': str(project_path)
        }

        try:
            result = subprocess.run(
                cmd,
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env
            )

            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode,
                'error': None if result.returncode == 0 else f"Test execution failed with return code {result.returncode}"
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': f'Test execution exceeded {timeout}s timeout',
                'returncode': 124,
                'error': 'Execution timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': f'Sandbox subprocess error: {str(e)}',
                'returncode': 1,
                'error': str(e)
            }

    def _worker(self, code, allowed_imports, cwd, use_pytest, result_queue):
        """The function that runs in the child process."""
        # 1. Set Working Directory
        if cwd:
            try:
                os.chdir(cwd)
            except:
                pass

        current_cwd = os.getcwd()

        # 2. Set Resource Limits
        self._apply_resource_limits()

        # 3. Capture Output
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture

        # 4. Restrict Environment
        # Get builtins dict safely
        if isinstance(builtins, dict):
            safe_builtins = builtins.copy()
        else:
            safe_builtins = vars(builtins).copy()

        # Replace __import__
        importer = RestrictedImporter(allowed_imports)
        safe_builtins['__import__'] = importer

        # Replace open with SafeOpen
        safe_builtins['open'] = SafeOpen(base_dir=current_cwd)

        # Disable dangerous builtins
        dangerous = ['exec', 'compile', 'input', 'breakpoint']
        for d in dangerous:
            if d in safe_builtins:
                safe_builtins[d] = None

        # Note: We keep 'eval' but it's restricted by the importer

        # 5. Execute Code
        success = False
        error_msg = None
        try:
            if use_pytest:
                # To run pytest, we need to write the code to a file
                # or use a pytest plugin that runs from string.
                # Writing to a temp file is easier.
                import uuid
                test_file = f"test_in_sandbox_{uuid.uuid4().hex[:8]}.py"
                try:
                    with builtins.open(test_file, "w", encoding='utf-8') as f:
                        f.write(code)

                    import pytest
                    # Use pytest.main which returns an ExitCode
                    # 0: all tests passed, 1: tests failed, etc.
                    ret = pytest.main([test_file, "-v", "--no-header"])
                    success = (ret == 0)
                    if not success:
                        error_msg = f"Tests failed with exit code {ret}"
                finally:
                    if os.path.exists(test_file):
                        try:
                            os.remove(test_file)
                        except:
                            pass
            else:
                exec_globals = {
                    '__builtins__': safe_builtins,
                    '__name__': '__main__',
                }
                exec(code, exec_globals)
                success = True
        except BaseException:
            error_msg = traceback.format_exc()
            success = False

        # 6. Send Result
        result_queue.put({
            'success': success,
            'error': error_msg if not success else None,
            'stdout': stdout_capture.getvalue(),
            'stderr': stderr_capture.getvalue()
        })
