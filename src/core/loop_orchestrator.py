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
import logging

logger = logging.getLogger(__name__)

class LoopResult:
    def __init__(self, status: str, iterations: int, message: str):
        self.status = status
        self.iterations = iterations
        self.message = message

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

        for iteration in range(max_iterations):
            # CHECK STOP EVENT
            if stop_event.is_set():
                self._log(f"Loop stopped by user at iteration {iteration}", log_callback)
                return LoopResult("STOPPED", iteration, "Loop stopped by user")

            self._log(f"\n=== nIA ITERATION {iteration + 1}/{max_iterations} ===", log_callback)

            # 0. Ensure environment is ready
            if iteration == 0:
                self._setup_environment(log_callback)

            # 1. Load fresh state
            try:
                spec = self.spec_path.read_text(encoding='utf-8')
                tasks = self.parser.parse(self.plan_path)
                prompt = self.prompt_path.read_text(encoding='utf-8')
            except Exception as e:
                self._log(f"❌ Error loading files: {str(e)}", log_callback)
                return LoopResult("ERROR", iteration, f"File loading error: {e}")

            # 2. Find next task
            next_task = self.parser.find_next_pending(tasks)
            if not next_task:
                return LoopResult("ALL_COMPLETE", iteration, "✅ All tasks completed!")

            self._log(f"Target Task: {next_task.description}", log_callback)

            # 3. Get context (all project files)
            context = self._get_project_context()

            # 4. Ask AI for solution
            try:
                response = self.ai_client.execute_nia_iteration(
                    spec=spec,
                    plan=self.plan_path.read_text(encoding='utf-8'),
                    prompt=prompt,
                    task=next_task,
                    context=context
                )

                if stop_event.is_set():
                    return LoopResult("STOPPED", iteration, "Loop stopped by user")

                if not response.files:
                    self._log("❌ AI provided no code changes.", log_callback)
                    self.tracker.mark_blocked(self.plan_path, next_task, "AI provided no code changes.")
                    return LoopResult("BLOCKED", iteration, "AI provided no code changes.")

                # 5. TDD Cycle: RED Phase
                if response.test_file:
                    self._log(f"Checking RED phase for {response.test_file}...", log_callback)
                    # Write ONLY the test file
                    test_content = response.files[response.test_file]
                    self._write_file(response.test_file, test_content)

                    val_red = self.validator.validate_red(
                        str(self.project_path / response.test_file),
                        response.test_name,
                        self.venv_python
                    )
                    if not val_red.success:
                        self._log(f"❌ RED Phase failed: {val_red.message}", log_callback)

                if stop_event.is_set():
                    return LoopResult("STOPPED", iteration, "Loop stopped by user")

                # 6. TDD Cycle: GREEN Phase
                self._log("Applying implementation code...", log_callback)
                for filename, content in response.files.items():
                    self._write_file(filename, content)

                if response.test_file:
                    val_green = self.validator.validate_green(
                        str(self.project_path / response.test_file),
                        response.test_name,
                        self.venv_python
                    )
                    if not val_green.success:
                        self._log(f"❌ GREEN Phase failed: {val_green.message}", log_callback)
                        self.tracker.mark_blocked(self.plan_path, next_task, f"GREEN phase failed: {val_green.stderr}")
                        return LoopResult("BLOCKED", iteration, "GREEN phase failed.")
                    self._log("✅ GREEN phase passed.", log_callback)

                if stop_event.is_set():
                    return LoopResult("STOPPED", iteration, "Loop stopped by user")

                # 7. TDD Cycle: REFACTOR Phase
                self._log("Verifying all tests...", log_callback)
                val_refactor = self.validator.validate_refactor(self.project_path, self.venv_python)
                if not val_refactor.success:
                    self._log(f"❌ REFACTOR Phase failed: {val_refactor.message}", log_callback)
                    self.tracker.mark_blocked(self.plan_path, next_task, "Regression detected during refactor phase.")
                    return LoopResult("BLOCKED", iteration, "Refactor phase failed.")
                self._log("✅ All tests passed.", log_callback)

                # 8. Update Plan
                self.tracker.mark_completed(self.plan_path, next_task)

                # 9. Git Commit
                self._git_commit(f"✅ {next_task.description}")
                self._log(f"Task completed and committed.", log_callback)

            except Exception as e:
                self._log(f"❌ Error during iteration: {str(e)}", log_callback)
                self.tracker.mark_blocked(self.plan_path, next_task, str(e))
                return LoopResult("ERROR", iteration, str(e))

            time.sleep(1)

        return LoopResult("MAX_ITERATIONS", max_iterations, f"Reached max iterations ({max_iterations})")

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
        # Strip backticks from filename if any escaped through
        rel_path = rel_path.replace("`", "")
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
