from pathlib import Path
import time
import os
import sys
import subprocess
import threading
from typing import Optional, List
from .plan_parser import PlanParser, Task
from .task_tracker import TaskTracker
from .tdd_validator import TDDValidator
from .nia_claude_client import nIAClaudeClient, nIAResponse
from src.utils.path_utils import clean_filename
import logging

logger = logging.getLogger(__name__)

class LoopResult:
    def __init__(self, status: str, iterations: int, message: str, stats: dict = None):
        self.status = status
        self.iterations = iterations
        self.message = message
        self.stats = stats or {}

class LoopOrchestrator:
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.parser = PlanParser()
        self.tracker = TaskTracker()
        self.validator = TDDValidator()
        self.ai_client = nIAClaudeClient()
        self.venv_python: Optional[str] = None

        self.spec_path = project_path / "SPEC.md"
        self.plan_path = project_path / "IMPLEMENTATION_PLAN.md"
        self.prompt_path = project_path / "NIA_PROMPT.md"

    def run(self, max_iterations: int = 20, log_callback=None, stop_event: threading.Event = None) -> LoopResult:
        if stop_event is None:
            stop_event = threading.Event()

        if not self.spec_path.exists() or not self.plan_path.exists() or not self.prompt_path.exists():
            return LoopResult("ERROR", 0, "Missing required nIA files (SPEC.md, IMPLEMENTATION_PLAN.md, or NIA_PROMPT.md)")

        start_time = time.time()
        tasks_planned = 0
        tasks_completed = 0

        for iteration in range(max_iterations):
            # CHECK STOP EVENT
            if stop_event.is_set():
                self._log(f"Loop stopped by user at iteration {iteration}", log_callback)
                return LoopResult("STOPPED", iteration, "Loop stopped by user", self._get_final_stats(start_time, tasks_planned, tasks_completed))

            self._log(f"\n=== nIA ITERATION {iteration + 1}/{max_iterations} ===", log_callback)

            # 0. Ensure environment is ready
            if iteration == 0:
                self._setup_environment(log_callback)

            # 1. Load fresh state
            try:
                spec = self.spec_path.read_text(encoding='utf-8')
                tasks = self.parser.parse(self.plan_path)
                tasks_planned = len(tasks)
                prompt = self.prompt_path.read_text(encoding='utf-8')
            except Exception as e:
                self._log(f"❌ Error loading files: {str(e)}", log_callback)
                return LoopResult("ERROR", iteration, f"File loading error: {e}", self._get_final_stats(start_time, tasks_planned, tasks_completed))

            # 2. Find next task
            next_task = self.parser.find_next_pending(tasks)
            if not next_task:
                return LoopResult("ALL_COMPLETE", iteration, "✅ All tasks completed!", self._get_final_stats(start_time, tasks_planned, tasks_completed))

            self._log(f"Target Task: {next_task.description}", log_callback)

            # 3. Get context (all project files)
            context = self._get_project_context()

            # 4. Ask AI for solution (with quality retry)
            max_retries = 1
            ai_feedback = ""
            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        self._log(f"Attempt {attempt+1}: Retrying with quality feedback...", log_callback)

                    response = self.ai_client.execute_nia_iteration(
                        spec=spec,
                        plan=self.plan_path.read_text(encoding='utf-8'),
                        prompt=prompt,
                        task=next_task,
                        context=context + (f"\n\nFEEDBACK: {ai_feedback}" if attempt > 0 else "")
                    )

                    if stop_event.is_set():
                        return LoopResult("STOPPED", iteration, "Loop stopped by user")

                    if not response.files:
                        self._log("❌ AI provided no code changes.", log_callback)
                        self.tracker.mark_blocked(self.plan_path, next_task, "AI provided no code changes.")
                        return LoopResult("BLOCKED", iteration, "AI provided no code changes.", self._get_final_stats(start_time, tasks_planned, tasks_completed))

                    # 5. TDD Cycle: RED Phase
                    if response.test_file:
                        self._log(f"=== STARTING RED PHASE ===", log_callback)
                        self._log_project_structure(log_callback)

                        self._log(f"Checking RED phase for {response.test_file}...", log_callback)
                        # Write ONLY the test file
                        test_content = response.files[response.test_file]
                        self._write_file(response.test_file, test_content)
                        self._log_file_content(response.test_file, log_callback)

                        # DEBUG LOGS
                        test_file_path = self.project_path / response.test_file
                        self._log(f"DEBUG: About to execute test at: {test_file_path}", log_callback)
                        self._log(f"DEBUG: Test file exists: {test_file_path.exists()}", log_callback)
                        if test_file_path.exists():
                            self._log(f"DEBUG: Test file size: {test_file_path.stat().st_size} bytes", log_callback)

                        val_red = self.validator.validate_red(
                            self.project_path,
                            str(test_file_path),
                            response.test_name,
                            self.venv_python
                        )
                        self._log_validation_result(val_red, "RED", log_callback)

                        if not val_red.success:
                            self._log(f"❌ RED Phase failed: {val_red.message}", log_callback)

                    if stop_event.is_set():
                        return LoopResult("STOPPED", iteration, "Loop stopped by user")

                    # 6. TDD Cycle: GREEN Phase
                    self._log("=== APPLYING IMPLEMENTATION CODE ===", log_callback)
                    for filename, content in response.files.items():
                        self._write_file(filename, content)

                    self._log_project_structure(log_callback)

                    if response.test_file:
                        self._log(f"=== STARTING GREEN PHASE ===", log_callback)

                        # DEBUG LOGS
                        test_file_path = self.project_path / response.test_file
                        self._log(f"DEBUG: About to execute test at: {test_file_path}", log_callback)
                        self._log(f"DEBUG: Test file exists: {test_file_path.exists()}", log_callback)

                        val_green = self.validator.validate_green(
                            self.project_path,
                            str(test_file_path),
                            response.test_name,
                            self.venv_python
                        )
                        self._log_validation_result(val_green, "GREEN", log_callback)

                        if not val_green.success:
                            self._log(f"❌ GREEN Phase failed: {val_green.message}", log_callback)
                            if attempt == max_retries:
                                self.tracker.mark_blocked(self.plan_path, next_task, f"GREEN phase failed: {val_green.stderr}")
                                return LoopResult("BLOCKED", iteration, "GREEN phase failed.", self._get_final_stats(start_time, tasks_planned, tasks_completed))
                            ai_feedback = f"GREEN phase failed: {val_green.stderr}. Please fix the implementation."
                            continue

                        self._log("✅ GREEN phase passed.", log_callback)

                    # QUALITY VALIDATION
                    total_lines = self._count_project_code_lines()
                    if total_lines < 50 and attempt < max_retries:
                        ai_feedback = f"Previous implementation was too minimal ({total_lines} lines). Please provide a complete, production-quality implementation with actual functionality and complete styling."
                        self._log(f"⚠️ Warning: Only {total_lines} lines generated. Retrying for better quality...", log_callback)
                        continue

                    if total_lines < 50:
                        self._log(f"⚠️ Warning: Only {total_lines} lines generated. Proceeding as max retries reached.", log_callback)

                    # Success, break retry loop
                    break

                except Exception as e:
                    self._log(f"❌ Error during iteration attempt: {str(e)}", log_callback)
                    if attempt == max_retries:
                        self.tracker.mark_blocked(self.plan_path, next_task, str(e))
                        return LoopResult("ERROR", iteration, str(e))
                    ai_feedback = f"Error during implementation: {str(e)}"

            if stop_event.is_set():
                return LoopResult("STOPPED", iteration, "Loop stopped by user")

            # 7. TDD Cycle: REFACTOR Phase
            try:
                self._log("=== STARTING REFACTOR PHASE ===", log_callback)
                self._log("Verifying all tests...", log_callback)
                val_refactor = self.validator.validate_refactor(self.project_path, self.venv_python)
                self._log_validation_result(val_refactor, "REFACTOR", log_callback)

                if not val_refactor.success:
                    self._log(f"❌ REFACTOR Phase failed: {val_refactor.message}", log_callback)
                    self.tracker.mark_blocked(self.plan_path, next_task, "Regression detected during refactor phase.")
                    return LoopResult("BLOCKED", iteration, "Refactor phase failed.", self._get_final_stats(start_time, tasks_planned, tasks_completed))
                self._log("✅ All tests passed.", log_callback)

                # 8. Update Plan
                self.tracker.mark_completed(self.plan_path, next_task)
                tasks_completed += 1

                # 9. Git Commit
                self._git_commit(f"✅ {next_task.description}")
                self._log(f"Task completed and committed.", log_callback)

            except Exception as e:
                self._log(f"❌ Error during iteration: {str(e)}", log_callback)
                self.tracker.mark_blocked(self.plan_path, next_task, str(e))
                return LoopResult("ERROR", iteration, str(e), self._get_final_stats(start_time, tasks_planned, tasks_completed))

            time.sleep(1)

        return LoopResult("MAX_ITERATIONS", max_iterations, f"Reached max iterations ({max_iterations})", self._get_final_stats(start_time, tasks_planned, tasks_completed))

    def _get_project_context(self) -> str:
        """Collect all relevant source files for context."""
        context = []
        # Exclude common directories
        exclude = {'.git', '__pycache__', 'node_modules', '.venv', 'venv'}
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in exclude]
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.html', '.css', '.md')):
                    path = Path(root) / file
                    rel_path = path.relative_to(self.project_path)
                    if rel_path.name in ['SPEC.md', 'IMPLEMENTATION_PLAN.md', 'NIA_PROMPT.md']:
                        continue
                    try:
                        content = path.read_text(encoding='utf-8')
                        context.append(f"File: {rel_path}\n```\n{content}\n```")
                    except Exception:
                        pass
        return "\n\n".join(context)

    def _write_file(self, rel_path: str, content: str):
        # Clean the filename of markdown formatting and invalid characters
        rel_path = clean_filename(rel_path)
        full_path = self.project_path / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding='utf-8')

    def _setup_environment(self, log_callback):
        """Initialize project virtual environment and dependencies."""
        self._log("Setting up project environment...", log_callback)
        try:
            # Check if it's a Python project based on SPEC.md
            spec_content = self.spec_path.read_text(encoding='utf-8')
            is_python = "Language: Python" in spec_content or "pytest" in spec_content
            is_frontend = "HTML/CSS" in spec_content or "BeautifulSoup" in spec_content

            setup_script = Path("scripts/setup_project_venv.py")
            if setup_script.exists():
                deps = []
                if is_python:
                    deps.append("pytest")
                if is_frontend:
                    deps.extend(["beautifulsoup4", "lxml"])

                cmd = [sys.executable, str(setup_script), str(self.project_path)] + deps
                result = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='replace')

                # Extract VENV_PYTHON from output
                for line in result.stdout.splitlines():
                    if line.startswith("VENV_PYTHON:"):
                        self.venv_python = line.replace("VENV_PYTHON:", "").strip()
                        self._log(f"Project venv ready: {self.venv_python}", log_callback)
                        break

            if not self.venv_python:
                self._log("Using system python as fallback.", log_callback)
                self.venv_python = sys.executable

        except Exception as e:
            self._log(f"Warning during env setup: {e}. Proceeding with system python.", log_callback)
            self.venv_python = sys.executable

    def _git_commit(self, message: str):
        """Safe git commit."""
        try:
            # Check if git is installed
            subprocess.run(["git", "--version"], capture_output=True, check=True, encoding='utf-8', errors='replace')

            # Check if git repo
            if not (self.project_path / ".git").exists():
                logger.info("Initializing new git repository")
                subprocess.run(["git", "init"], cwd=self.project_path, capture_output=True, check=True, encoding='utf-8', errors='replace')

            subprocess.run(["git", "add", "."], cwd=self.project_path, capture_output=True, check=True, encoding='utf-8', errors='replace')
            subprocess.run(["git", "commit", "-m", message], cwd=self.project_path, capture_output=True, check=True, encoding='utf-8', errors='replace')
            logger.info(f"Git commit successful: {message}")
        except FileNotFoundError:
            logger.warning("Git binary not found. Skipping commit.")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Git operation failed: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error during git commit: {e}")

    def _log(self, message: str, callback):
        if callback:
            callback(message)
        print(message)

    def _log_project_structure(self, log_callback):
        """Log current project file structure."""
        self._log(f"\n{'='*60}", log_callback)
        self._log("CURRENT PROJECT STRUCTURE:", log_callback)
        self._log(f"{'='*60}", log_callback)

        try:
            for root, dirs, files in os.walk(self.project_path):
                # Ignore common directories
                dirs[:] = [d for d in dirs if d not in ['.venv', '.git', '__pycache__', 'node_modules']]

                level = Path(root).relative_to(self.project_path).parts
                indent = '  ' * len(level)
                folder_name = os.path.basename(root) or os.path.basename(self.project_path)
                self._log(f"{indent}📁 {folder_name}/", log_callback)

                subindent = '  ' * (len(level) + 1)
                for file in sorted(files):
                    self._log(f"{subindent}📄 {file}", log_callback)
        except Exception as e:
            self._log(f"Error logging structure: {e}", log_callback)

        self._log(f"{'='*60}\n", log_callback)

    def _log_file_content(self, rel_path: str, log_callback):
        """Log the content of a specific file."""
        self._log(f"=== Content of {rel_path} ===", log_callback)
        try:
            full_path = self.project_path / rel_path
            if full_path.exists():
                content = full_path.read_text(encoding='utf-8')
                self._log(content, log_callback)
            else:
                self._log(f"File {rel_path} does not exist.", log_callback)
        except Exception as e:
            self._log(f"Error reading file {rel_path}: {e}", log_callback)
        self._log("=== End of file content ===\n", log_callback)

    def _get_final_stats(self, start_time, tasks_planned, tasks_completed) -> dict:
        """Calculate final execution statistics."""
        total_code_lines = self._count_project_code_lines()
        total_test_lines = self._count_test_lines()
        duration = time.time() - start_time

        return {
            "tasks_planned": tasks_planned,
            "tasks_completed": tasks_completed,
            "duration_seconds": duration,
            "total_code_lines": total_code_lines,
            "total_test_lines": total_test_lines,
            "average_lines_per_task": total_code_lines / tasks_completed if tasks_completed > 0 else 0
        }

    def _count_test_lines(self) -> int:
        """Count total lines of code in the tests directory."""
        total_lines = 0
        test_dir = self.project_path / "tests"
        if not test_dir.exists():
            return 0

        for root, dirs, files in os.walk(test_dir):
            for file in files:
                if file.endswith('.py'):
                    try:
                        path = Path(root) / file
                        content = path.read_text(encoding='utf-8')
                        total_lines += len([line for line in content.splitlines() if line.strip()])
                    except:
                        pass
        return total_lines

    def _count_project_code_lines(self) -> int:
        """Count total lines of code in the project, excluding tests and common dirs."""
        total_lines = 0
        exclude_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'tests'}
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.html', '.css')):
                    try:
                        path = Path(root) / file
                        content = path.read_text(encoding='utf-8')
                        total_lines += len([line for line in content.splitlines() if line.strip()])
                    except:
                        pass
        return total_lines

    def _log_validation_result(self, result, phase_name: str, log_callback):
        """Log detailed validation result."""
        self._log(f"\n{'='*60}", log_callback)
        self._log(f"{phase_name} TEST OUTPUT:", log_callback)
        self._log(f"{'='*60}", log_callback)

        if result.stdout:
            for line in result.stdout.splitlines():
                self._log(f"STDOUT: {line}", log_callback)

        if result.stderr:
            for line in result.stderr.splitlines():
                self._log(f"STDERR: {line}", log_callback)

        self._log(f"{'='*60}", log_callback)
        self._log(f"Status: {'✅ PASSED' if result.success else '❌ FAILED'}", log_callback)
        self._log(f"{'='*60}\n", log_callback)
