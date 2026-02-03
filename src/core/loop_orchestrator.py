from pathlib import Path
import time
import os
import re
import json
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
                logger.error(f"Error loading files: {e}", exc_info=True)
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
            max_retries = 2
            ai_feedback = ""
            active_test_file = None
            active_test_name = None

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
                        if attempt == max_retries:
                            self.tracker.mark_blocked(self.plan_path, next_task, "AI provided no code changes after retries.")
                            return LoopResult("BLOCKED", iteration, "AI provided no code changes.", self._get_final_stats(start_time, tasks_planned, tasks_completed))
                        ai_feedback = "You provided no code changes. Please provide the necessary implementation files."
                        continue

                    # 5. TDD Cycle: RED Phase (ONLY on attempt 0)
                    if attempt == 0 and response.test_file:
                        active_test_file = response.test_file
                        active_test_name = response.test_name

                        self._log(f"=== STARTING RED PHASE ===", log_callback)
                        self._log_project_structure(log_callback)

                        self._log(f"Checking RED phase for {active_test_file}...", log_callback)
                        # Write ONLY the test file
                        test_content = response.files[active_test_file]
                        self._write_file(active_test_file, test_content)
                        self._log_file_content(active_test_file, log_callback)

                        # DEBUG LOGS
                        test_file_path = self.project_path / active_test_file
                        self._log(f"DEBUG: About to execute test at: {test_file_path}", log_callback)

                        val_red = self.validator.validate_red(
                            self.project_path,
                            str(test_file_path),
                            active_test_name,
                            self.venv_python
                        )
                        self._log_validation_result(val_red, "RED", log_callback)

                        if not val_red.success:
                            self._log(f"❌ RED Phase failed: {val_red.message}", log_callback)
                            # We proceed anyway to try GREEN, or we could retry RED?
                            # Usually if RED fails (test passes), it means implementation is already there or test is bad.

                    if stop_event.is_set():
                        return LoopResult("STOPPED", iteration, "Loop stopped by user")

                    # 6. TDD Cycle: GREEN Phase
                    self._log("=== APPLYING IMPLEMENTATION CODE ===", log_callback)

                    # Pre-application validation for placeholders
                    placeholder_file = self._check_for_placeholders(response.files)
                    if placeholder_file and attempt < max_retries:
                        self._log(f"⚠️ Warning: Placeholder found in {placeholder_file}. Retrying for better quality...", log_callback)
                        ai_feedback = f"Your implementation of {placeholder_file} contains placeholder comments (TODO, ..., etc.). Please provide a COMPLETE implementation with actual content and logic. DO NOT use '...' or 'TODO' as a substitute for real code."
                        continue

                    for filename, content in response.files.items():
                        # Don't overwrite the test file if we are in a quality retry,
                        # UNLESS the AI explicitly wants to update the test.
                        # But user says "Mantener el test original".
                        if attempt > 0 and filename == active_test_file:
                             continue
                        self._write_file(filename, content)

                    self._log_project_structure(log_callback)

                    if active_test_file:
                        self._log(f"=== STARTING GREEN PHASE ===", log_callback)
                        test_file_path = self.project_path / active_test_file

                        val_green = self.validator.validate_green(
                            self.project_path,
                            str(test_file_path),
                            active_test_name,
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

                    # QUALITY VALIDATION (Line Counts)
                    nia_config = self._get_nia_config()
                    tech_config = nia_config.get("tech_config", {})
                    quality_standards = tech_config.get("quality_standards", {})

                    quality_issues = []
                    for filename in response.files:
                        if 'test' in filename.lower() or '/tests/' in filename:
                            continue

                        ext = Path(filename).suffix.lstrip('.')
                        if ext in quality_standards:
                            min_lines = quality_standards[ext].get('min_lines', 0)
                            # Read current file content from disk (already written)
                            file_path = self.project_path / filename
                            if file_path.exists():
                                current_lines = len([l for l in file_path.read_text(encoding='utf-8').splitlines() if l.strip()])
                                if current_lines < min_lines:
                                    quality_issues.append(f"{filename}: {current_lines} lines (min: {min_lines})")

                    if quality_issues and attempt < max_retries:
                        self._log(f"⚠️ Warning: Quality standards not met: {', '.join(quality_issues)}", log_callback)
                        ai_feedback = (f"CRITICAL: Previous implementation did not meet quality standards:\n" +
                                      "\n".join(quality_issues) +
                                      "\nPlease provide a more complete and detailed implementation with actual content. "
                                      "DO NOT use stubs or placeholder comments.")
                        continue

                    if quality_issues:
                        self._log(f"⚠️ Warning: Quality standards not met after retries. Proceeding anyway.", log_callback)

                    # Success, break retry loop
                    break

                except Exception as e:
                    logger.error(f"Error during iteration attempt: {e}", exc_info=True)
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

                if val_refactor.success:
                    # 7.1. Code Quality Metrics (Informational)
                    try:
                        metrics = self._analyze_code_quality()
                        self._log("📊 Code Quality Metrics (Informational):", log_callback)
                        for key, value in metrics.items():
                            self._log(f"  - {key}: {value}", log_callback)
                    except Exception as me:
                        logger.warning(f"Error during quality analysis: {me}")

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
                logger.error(f"Error during iteration: {e}", exc_info=True)
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
                content = full_path.read_text(encoding='utf-8', errors='replace')
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

    def _check_for_placeholders(self, files: dict) -> Optional[str]:
        """Check for placeholders in implementation files, ignoring tests."""
        placeholder_patterns = [
            r'TODO:',
            r'FIXME:',
            r'PLACEHOLDER',
            r'\/\/\s*Add\s+.+\s+here',
            r'#\s*Add\s+.+\s+here',
            r'Content here'
        ]

        for filename, content in files.items():
            # SKIP test files
            if 'test' in filename.lower() or '/tests/' in filename:
                continue

            # Check basic patterns
            for pattern in placeholder_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return filename

            # Smart check for "..." standalone on a line
            for line in content.splitlines():
                stripped = line.strip()
                if stripped == "..." or stripped == "# ..." or stripped == "// ...":
                    # Allow "..." in tests if it was a test file, but we already skipped tests.
                    return filename

        return None

    def _get_nia_config(self) -> dict:
        """Load project nIA configuration."""
        config_path = self.project_path / ".nia_config.json"
        if config_path.exists():
            try:
                return json.loads(config_path.read_text(encoding='utf-8'))
            except:
                pass
        return {}

    def _analyze_code_quality(self) -> dict:
        """Basic code quality analysis for the project."""
        metrics = {
            "total_files": 0,
            "total_lines": 0,
            "comment_lines": 0,
            "todo_count": 0,
            "approx_complexity": 0 # Number of control flow keywords
        }

        exclude_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'tests'}
        complexity_keywords = ['if ', 'else', 'elif', 'for ', 'while ', 'case ', 'match ', '&&', '||', ' and ', ' or ']

        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.html', '.css')):
                    metrics["total_files"] += 1
                    try:
                        path = Path(root) / file
                        content = path.read_text(encoding='utf-8', errors='replace')
                        lines = content.splitlines()
                        metrics["total_lines"] += len(lines)

                        for line in lines:
                            sline = line.strip()
                            if sline.startswith(('#', '//', '/*', '*')):
                                metrics["comment_lines"] += 1
                            if 'TODO' in sline or 'FIXME' in sline:
                                metrics["todo_count"] += 1

                            for kw in complexity_keywords:
                                if kw in sline:
                                    metrics["approx_complexity"] += 1
                    except:
                        pass
        return metrics

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
