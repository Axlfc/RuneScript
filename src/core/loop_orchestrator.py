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
from .quality import QualityChecker
from .test_parser import TestParser
from lib.nia_git_manager import GitBasedFileManager
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
        self.project_path = Path(os.path.abspath(project_path))
        self.parser = PlanParser()
        self.tracker = TaskTracker()
        self.validator = TDDValidator()
        self.ai_client = nIAClaudeClient()
        self.quality_checker = QualityChecker()
        self.git_manager = GitBasedFileManager(str(self.project_path))
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

            # 3. Create Checkpoint
            checkpoint = self.git_manager.create_checkpoint(f"Before: {next_task.description}")

            # 4. Get context (all project files)
            context = self._get_project_context()

            # 5. Ask AI for solution (with quality retry)
            max_retries = 2
            ai_feedback = ""
            requirements_feedback = ""
            active_test_file = None
            active_test_name = None

            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        self._log(f"Attempt {attempt+1}: Retrying with quality feedback...", log_callback)

                    combined_context = context
                    if ai_feedback:
                        combined_context += f"\n\nFEEDBACK: {ai_feedback}"
                    if requirements_feedback:
                        combined_context += f"\n\n{requirements_feedback}"

                    response = self.ai_client.execute_nia_iteration(
                        spec=spec,
                        plan=self.plan_path.read_text(encoding='utf-8'),
                        prompt=prompt,
                        task=next_task,
                        context=combined_context
                    )

                    if stop_event.is_set():
                        return LoopResult("STOPPED", iteration, "Loop stopped by user")

                    # DETECT INCORRECT EXECUTION SIGNALS (mkdir, cd, etc.)
                    raw_lower = response.raw.lower()
                    if "mkdir" in raw_lower or "cd " in raw_lower or "npm " in raw_lower:
                        self._log("⚠️ WARNING: AI attempted to use bash commands (mkdir/cd/npm). These are NOT executed. AI must use file blocks.", log_callback)

                    # LOG PARSED FILES DIAGNOSTICS
                    self._log(f"Files detected by parser: {len(response.files)}", log_callback)
                    for filename in response.files:
                        self._log(f"  - {filename} ({len(response.files[filename])} chars)", log_callback)

                    # Specific warning if critical files are missing for frontend_web
                    nia_config = self._get_nia_config()
                    tech_key = nia_config.get("tech_stack", "")
                    if tech_key == 'frontend_web':
                        critical_files = ['index.html', 'css/main.css', 'styles/main.css', 'js/app.js', 'js/main.js']
                        detected_paths = set(response.files.keys())
                        if 'index.html' not in detected_paths:
                            self._log("⚠️ CRITICAL: index.html not detected in AI response!", log_callback)

                        has_css = any(f in detected_paths for f in ['css/main.css', 'styles/main.css', 'css/style.css'])
                        if not has_css:
                             self._log("⚠️ CRITICAL: No CSS file detected in AI response!", log_callback)

                        has_js = any(f in detected_paths for f in ['js/app.js', 'js/main.js', 'js/script.js'])
                        if not has_js:
                             self._log("⚠️ CRITICAL: No JS file detected in AI response!", log_callback)

                    if not response.files:
                        self._log("❌ AI provided no code changes.", log_callback)
                        if attempt == max_retries:
                            self.tracker.mark_blocked(self.plan_path, next_task, "AI provided no code changes after retries.")
                            return LoopResult("BLOCKED", iteration, "AI provided no code changes.", self._get_final_stats(start_time, tasks_planned, tasks_completed))
                        ai_feedback = "You provided no code changes. Please provide the necessary implementation files."
                        continue

                    # 6. TDD Cycle: RED Phase (ONLY on attempt 0)
                    if attempt == 0 and response.test_file:
                        active_test_file = response.test_file
                        active_test_name = response.test_name

                        self._log(f"=== STARTING RED PHASE ===", log_callback)
                        self._log_project_structure(log_callback)

                        # DEBUG ENVIRONMENT
                        self._log(f"DEBUG ENV: Python: {sys.executable}", log_callback)
                        self._log(f"DEBUG ENV: Venv Python: {self.venv_python}", log_callback)
                        self._log(f"DEBUG ENV: Project Path: {self.project_path}", log_callback)

                        self._log(f"Checking RED phase for {active_test_file}...", log_callback)
                        # Write ONLY the test file
                        test_content = response.files[active_test_file]
                        self._write_file(active_test_file, test_content, log_callback)
                        self._log_file_content(active_test_file, log_callback)

                        # DEBUG LOGS
                        test_file_path = self.project_path / active_test_file
                        self._log(f"=" * 60, log_callback)
                        self._log(f"DEBUG COMMAND CONSTRUCTION (RED):", log_callback)
                        self._log(f"venv_python: {self.venv_python}", log_callback)
                        self._log(f"test_file: {active_test_file}", log_callback)
                        self._log(f"project_path: {self.project_path}", log_callback)
                        self._log(f"=" * 60, log_callback)

                        val_red = self.validator.validate_red(
                            self.project_path,
                            str(test_file_path),
                            active_test_name,
                            self.venv_python
                        )
                        self._log_validation_result(val_red, "RED", log_callback)

                        # Extract requirements from test for implementation phase
                        try:
                            reqs = TestParser.extract_requirements(test_content)
                            if any(reqs.values()):
                                self._log(f"📋 Test requirements extracted: IDs: {reqs['required_ids']}, Tags: {reqs['required_tags']}", log_callback)
                                requirements_feedback = f"""
╔══════════════════════════════════════════════════════════╗
║ 🔴 CRITICAL REQUIREMENTS FROM TEST (DO NOT IGNORE)      ║
╚══════════════════════════════════════════════════════════╝

Your implementation MUST include these EXACT values to pass the tests:

✓ Required HTML element IDs:
  {', '.join(reqs['required_ids']) if reqs['required_ids'] else 'None'}

✓ Required HTML tags:
  {', '.join(reqs['required_tags']) if reqs['required_tags'] else 'None'}

✓ Required CSS classes:
  {', '.join(reqs['required_classes']) if reqs['required_classes'] else 'None'}

✓ Required text content:
  {', '.join(reqs['required_text']) if reqs['required_text'] else 'None'}

⚠️ IMPORTANT: Use the EXACT IDs and tags listed above.
For example, if the test expects id="work", DO NOT use id="projects".
"""
                        except Exception as e:
                            logger.error(f"Error extracting requirements: {e}")

                        if not val_red.success:
                            self._log(f"❌ RED Phase failed: {val_red.message}", log_callback)
                            # We proceed anyway to try GREEN, or we could retry RED?
                            # Usually if RED fails (test passes), it means implementation is already there or test is bad.

                    if stop_event.is_set():
                        return LoopResult("STOPPED", iteration, "Loop stopped by user")

                    # 7. TDD Cycle: GREEN Phase
                    self._log("=== APPLYING IMPLEMENTATION CODE ===", log_callback)

                    # WRITE FILES FIRST ✅ (as requested by user)
                    written_files = []
                    self._log(f"📝 Writing {len(response.files)} files to disk...", log_callback)
                    for filename, content in response.files.items():
                        # Don't overwrite the test file if we are in a quality retry,
                        # UNLESS the AI explicitly wants to update the test.
                        if attempt > 0 and filename == active_test_file:
                             continue
                        if self._write_file(filename, content, log_callback):
                            written_files.append(filename)

                    # PHYSICAL VERIFICATION
                    self._log("🔍 Verifying physical file existence...", log_callback)
                    missing_physical = []
                    for f in response.files:
                        if attempt > 0 and f == active_test_file:
                            continue
                        full_p = self.project_path / f
                        exists = full_p.exists()
                        status = "✅" if exists else "❌"
                        self._log(f"{status} {f}: {exists}", log_callback)
                        if not exists:
                            missing_physical.append(f)

                    if missing_physical:
                        self._log(f"❌ CRITICAL ERROR: Files not found on disk after write: {', '.join(missing_physical)}", log_callback)
                        if attempt < max_retries:
                            ai_feedback = f"System failed to write files to disk: {', '.join(missing_physical)}. Please ensure paths are correct and provide full content."
                            continue
                        else:
                            self.tracker.mark_blocked(self.plan_path, next_task, f"File system write failure: {', '.join(missing_physical)}")
                            return LoopResult("ERROR", iteration, "Physical file verification failed")

                    self._log(f"✅ Successfully written: {len(written_files)} files", log_callback)
                    self._log_project_structure(log_callback)

                    # Pre-application validation for placeholders
                    placeholder_file = self._check_for_placeholders(response.files)
                    if placeholder_file:
                        if attempt < max_retries:
                            self._log(f"⚠️ Warning: Placeholder found in {placeholder_file}. Retrying for better quality...", log_callback)
                            ai_feedback = f"Your implementation of {placeholder_file} contains placeholder comments (TODO, ..., etc.). Please provide a COMPLETE implementation with actual content and logic. DO NOT use '...' or 'TODO' as a substitute for real code."
                            continue
                        else:
                            self._log(f"⚠️ Quality warning: Placeholder found in {placeholder_file}, but proceeding anyway (last attempt).", log_callback)

                    # Quality Check AFTER writing files
                    nia_config = self._get_nia_config()
                    tech_config = nia_config.get("tech_config", {})
                    quality_issues = self.quality_checker.validate(response.files, tech_config)

                    if quality_issues:
                        self._log("⚠️ QUALITY ISSUES DETECTED:", log_callback)
                        for issue in quality_issues:
                            self._log(f"  - {issue}", log_callback)

                        if attempt < max_retries:
                            # Generar feedback para retry
                            quality_feedback = self.quality_checker.generate_feedback(quality_issues)
                            ai_feedback += "\n\n" + quality_feedback
                            self._log("🔄 Retrying to improve quality...", log_callback)
                            continue
                        else:
                             self._log("⚠️ Quality below standards, but files created (last attempt).", log_callback)
                    else:
                        self._log("✅ Quality check passed", log_callback)

                    if active_test_file:
                        self._log(f"=== STARTING GREEN PHASE ===", log_callback)

                        # DEBUG ENVIRONMENT
                        self._log(f"DEBUG ENV: Python: {sys.executable}", log_callback)
                        self._log(f"DEBUG ENV: Venv Python: {self.venv_python}", log_callback)
                        self._log(f"DEBUG ENV: Project Path: {self.project_path}", log_callback)

                        test_file_path = self.project_path / active_test_file
                        self._log(f"=" * 60, log_callback)
                        self._log(f"DEBUG COMMAND CONSTRUCTION (GREEN):", log_callback)
                        self._log(f"venv_python: {self.venv_python}", log_callback)
                        self._log(f"test_file: {active_test_file}", log_callback)
                        self._log(f"project_path: {self.project_path}", log_callback)
                        self._log(f"=" * 60, log_callback)

                        val_green = self.validator.validate_green(
                            self.project_path,
                            str(test_file_path),
                            active_test_name,
                            self.venv_python
                        )
                        self._log_validation_result(val_green, "GREEN", log_callback)

                        if not val_green.success:
                            self._log(f"❌ GREEN Phase failed: {val_green.message}", log_callback)

                            # Log failed attempt
                            try:
                                self.git_manager.generate_error_log(
                                    task_description=next_task.description,
                                    phase="GREEN",
                                    error_message=val_green.message,
                                    test_output=val_green.stdout + "\n" + val_green.stderr,
                                    files_generated=list(response.files.keys()),
                                    attempt=attempt + 1
                                )
                            except Exception as e:
                                logger.error(f"Error generating error log: {e}")

                            if attempt == max_retries:
                                self.tracker.mark_blocked(self.plan_path, next_task, f"GREEN phase failed: {val_green.stderr}")
                                return LoopResult("BLOCKED", iteration, "GREEN phase failed.", self._get_final_stats(start_time, tasks_planned, tasks_completed))
                            ai_feedback = f"GREEN phase failed: {val_green.stderr}. Please fix the implementation."
                            continue

                        self._log("✅ GREEN phase passed.", log_callback)

                    # MANDATORY FILES VALIDATION
                    missing_critical = self._validate_critical_files(tech_key)
                    if missing_critical:
                        self._log(f"⚠️ Warning: Missing critical files: {', '.join(missing_critical)}", log_callback)
                        if attempt < max_retries:
                            ai_feedback += f"\n\nMISSING CRITICAL FILES: {', '.join(missing_critical)}\nPlease ensure all required files are generated."
                            # Rollback before retry to have a clean slate
                            self.git_manager.rollback_to(checkpoint)
                            self.git_manager.record_failed_iteration()
                            continue

                    # Success, break retry loop
                    break

                except Exception as e:
                    logger.error(f"Error during iteration attempt: {e}", exc_info=True)
                    self._log(f"❌ Error during iteration attempt: {str(e)}", log_callback)
                    # Rollback on unexpected error
                    self.git_manager.rollback_to(checkpoint)
                    self.git_manager.record_failed_iteration()
                    if attempt == max_retries:
                        self.tracker.mark_blocked(self.plan_path, next_task, str(e))
                        return LoopResult("ERROR", iteration, str(e))
                    ai_feedback = f"Error during implementation: {str(e)}"

            if stop_event.is_set():
                return LoopResult("STOPPED", iteration, "Loop stopped by user")

            # 10. TDD Cycle: REFACTOR Phase
            try:
                self._log("=== STARTING REFACTOR PHASE ===", log_callback)
                self._log("Verifying all tests...", log_callback)
                val_refactor = self.validator.validate_refactor(self.project_path, self.venv_python)
                self._log_validation_result(val_refactor, "REFACTOR", log_callback)

                if not val_refactor.success:
                    self._log(f"❌ REFACTOR Phase failed: {val_refactor.message}", log_callback)
                    # ROLLBACK: If refactor/final validation fails, undo everything from this iteration
                    self._log("⏪ Undoing changes due to validation failure.", log_callback)
                    self.git_manager.rollback_to(checkpoint)
                    self.git_manager.record_failed_iteration()
                    self.tracker.mark_blocked(self.plan_path, next_task, "Regression detected during refactor phase.")
                    return LoopResult("BLOCKED", iteration, "Refactor phase failed.", self._get_final_stats(start_time, tasks_planned, tasks_completed))

                self._log("✅ All tests passed.", log_callback)

                # 11. Code Quality Metrics (Informational)
                try:
                    metrics = self._analyze_code_quality()
                    self._log("📊 Code Quality Metrics (Informational):", log_callback)
                    for key, value in metrics.items():
                        self._log(f"  - {key}: {value}", log_callback)
                except Exception as me:
                    logger.warning(f"Error during quality analysis: {me}")

                # 12. FINALIZE ITERATION: Detect Changes, Commit and Patch System
                self._log("💾 Finalizing task and generating patches...", log_callback)

                # Commit changes (if any)
                commit_msg = f"✅ {next_task.description}"
                current_sha = self.git_manager.create_checkpoint(commit_msg)

                # Detect exactly what changed since the start of this iteration
                changes = self.git_manager.get_changes_since(checkpoint)

                # Generate Patch System files
                patch_path, diff_path = self.git_manager.generate_patch(checkpoint, next_task.description)

                if patch_path:
                    log_path = self.git_manager.generate_patch_log(
                        patch_path,
                        next_task.description,
                        changes,
                        val_refactor
                    )

                    # Update manifest with detailed patch info
                    patch_info = {
                        "sequence": len(self.git_manager._load_manifest()['patches']) + 1,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                        "patch_file": os.path.basename(patch_path),
                        "task": next_task.description,
                        "commit": current_sha,
                        "files_changed": len(changes['added']) + len(changes['modified']) + len(changes['deleted']),
                        "lines_changed": self.git_manager._count_lines_changed(changes),
                        "status": "success"
                    }
                    self.git_manager.update_manifest(patch_info)

                    self._log(f"✅ Patch saved: {os.path.basename(patch_path)}", log_callback)
                    self._log(f"📊 Diff saved: {os.path.basename(diff_path)}", log_callback)
                    self._log(f"📝 Log saved: {os.path.basename(log_path)}", log_callback)
                else:
                    self._log("⚠️ No patch generated (possibly no changes committed).", log_callback)

                # 13. Update Plan
                self.tracker.mark_completed(self.plan_path, next_task)
                tasks_completed += 1

            except Exception as e:
                logger.error(f"Error during iteration: {e}", exc_info=True)
                self._log(f"❌ Error during iteration: {str(e)}", log_callback)
                # Ensure rollback on finalization error
                self.git_manager.rollback_to(checkpoint)
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

    def _validate_file_path(self, filepath: str, tech_stack: str) -> bool:
        """
        Validates that files are created in their correct directories based on tech stack.
        Returns True if valid, False otherwise.
        """
        filename = os.path.basename(filepath)
        ext = os.path.splitext(filename)[1].lower()
        parent_dir = os.path.dirname(filepath).replace('\\', '/')

        # Standardize empty parent dir to empty string
        if parent_dir == '.':
            parent_dir = ''

        # Rules for Frontend Web
        if tech_stack == 'frontend_web':
            # Allow common setup files at root
            if filename.lower() in ['.gitignore', 'readme.md', 'package.json', 'nia_prompt.md', 'spec.md', 'implementation_plan.md']:
                return True

            # HTML files should be at root or in assets/
            if ext == '.html':
                if parent_dir not in ['', 'assets']:
                    return False

            # CSS files MUST be in a css or styles directory
            elif ext == '.css':
                allowed = ['css', 'assets/css', 'styles', 'assets/styles']
                if parent_dir not in allowed:
                    return False

            # JS files MUST be in a js or scripts directory
            elif ext == '.js':
                allowed = ['js', 'assets/js', 'scripts', 'assets/scripts']
                if parent_dir not in allowed:
                    return False

            # Images MUST be in an img or images directory
            elif ext in ['.png', '.jpg', '.jpeg', '.webp', '.svg', '.gif']:
                allowed = ['img', 'assets/img', 'images', 'assets/images', 'assets/icons', 'icons']
                if parent_dir not in allowed:
                    return False

        return True

    def _write_file(self, rel_path: str, content: str, log_callback=None) -> bool:
        """
        Writes a file to the project directory and verifies its existence.
        Returns True if successful, False otherwise.
        """
        try:
            # Clean the filename of markdown formatting and invalid characters
            rel_path = clean_filename(rel_path)

            # Normalize path
            rel_path = os.path.normpath(rel_path).replace('\\', '/')
            if rel_path.startswith('./'):
                rel_path = rel_path[2:]

            # Validate path based on tech stack
            nia_config = self._get_nia_config()
            tech_stack = nia_config.get("tech_stack", "")

            if not self._validate_file_path(rel_path, tech_stack):
                msg = f"Skipping file {rel_path}: violates project structure for {tech_stack}"
                self._log(f"⚠️ {msg}", log_callback)
                logging.warning(msg)
                return False

            full_path = self.project_path / rel_path

            # Ensure parent directory exists
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            full_path.write_text(content, encoding='utf-8')

            # Immediate verification
            if full_path.exists():
                self._log(f"Generated file: {rel_path}", log_callback)
                return True
            else:
                self._log(f"❌ Failed to generate file: {rel_path}", log_callback)
                return False

        except Exception as e:
            self._log(f"❌ Exception writing file {rel_path}: {str(e)}", log_callback)
            return False

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
                        rel_venv_python = line.replace("VENV_PYTHON:", "").strip()
                        self.venv_python = os.path.abspath(rel_venv_python)
                        self._log(f"Project venv ready: {self.venv_python}", log_callback)
                        break

            if not self.venv_python:
                self._log("Using system python as fallback.", log_callback)
                self.venv_python = sys.executable

        except Exception as e:
            self._log(f"Warning during env setup: {e}. Proceeding with system python.", log_callback)
            self.venv_python = sys.executable

    def _git_commit(self, message: str):
        """Safe git commit (Delegated to GitBasedFileManager)."""
        try:
            self.git_manager.create_checkpoint(message)
            logger.info(f"Git commit successful: {message}")
        except Exception as e:
            logger.warning(f"Delegated git commit failed: {e}")

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

    def _validate_critical_files(self, tech_key: str) -> List[str]:
        """Verify existence of critical files for the specific tech stack."""
        # Define alternatives for some files
        ALTERNATIVES = {
            'css/main.css': [
                'styles/main.css', 'css/style.css', 'styles/style.css',
                'assets/css/styles.css', 'assets/css/main.css', 'assets/styles/styles.css',
                'css/styles.css', 'styles/styles.css'
            ],
            'js/app.js': [
                'js/main.js', 'js/script.js', 'js/index.js',
                'assets/js/main.js', 'assets/js/app.js', 'assets/js/script.js',
                'js/app.js', 'main.js'
            ]
        }

        REQUIRED_FILES_BY_STACK = {
            'frontend_web': ['index.html', 'css/main.css', 'js/app.js'],
            'python_backend': ['app.py', 'requirements.txt'],
            'node_js': ['index.js', 'package.json']
        }

        required = REQUIRED_FILES_BY_STACK.get(tech_key, [])
        missing = []

        for filename in required:
            # Check the primary filename
            if (self.project_path / filename).exists():
                continue

            # Check alternatives
            found_alt = False
            for alt in ALTERNATIVES.get(filename, []):
                if (self.project_path / alt).exists():
                    found_alt = True
                    break

            if found_alt:
                continue

            # Smart search: Check if ANY file with the required extension exists (excluding tests)
            ext = os.path.splitext(filename)[1]
            if ext in ['.css', '.js', '.html']:
                found_by_ext = False
                for root, dirs, files in os.walk(self.project_path):
                    # Exclude common noisy directories
                    dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']]

                    for f in files:
                        if f.endswith(ext) and 'test' not in f.lower() and f != 'SPEC.md' and f != 'IMPLEMENTATION_PLAN.md':
                            found_by_ext = True
                            break
                    if found_by_ext:
                        break

                if found_by_ext:
                    continue

            missing.append(filename)

        return missing

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
        self._log(f"Message: {result.message}", log_callback)
        self._log(f"Status: {'✅ PASSED' if result.success else '❌ FAILED'}", log_callback)
        self._log(f"{'='*60}\n", log_callback)
