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
from .quality import QualityChecker, QualityIssue
from .test_parser import TestParser
from .iteration_state import IterationState
from .issue_manager import IssueManager
from .file_structure_validator import FileStructureValidator
from .tech_detector import TechStackDetector
from .exceptions import QuotaExhaustedError
from src.utils.telemetry import RateLimitedTelemetry
from .storage import FileSystemStorage
from .config.manager import ConfigManager
from .intelligence_orchestrator import IntelligenceOrchestrator
from lib.nia_git_manager import GitBasedFileManager
from src.utils.path_utils import clean_filename
from src.security.path_validator import ParanoidPathValidator
from src.security.audit import SecurityAuditor
from src.security.exceptions import SecurityException
import logging

logger = logging.getLogger(__name__)

class LoopResult:
    def __init__(self, status: str, iterations: int, message: str, stats: dict = None):
        self.status = status
        self.iterations = iterations
        self.message = message
        self.stats = stats or {}

class LoopOrchestrator:
    def __init__(self, project_path: Path, ui_callbacks=None):
        self.project_path = Path(os.path.abspath(project_path))
        self.ui_callbacks = ui_callbacks or {}

        # 1. Initialize Basic Config & Storage First (Critical Path)
        try:
            self.storage = FileSystemStorage(self.project_path)
            self.config_manager = ConfigManager()
            logger.info("✓ ConfigManager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize config/storage: {e}")
            # Fallback to defaults
            from .config.defaults import DEFAULT_CONFIG
            # Correctly handle method arguments in mock
            self.config_manager = type('MockConfigManager', (), {
                'config': DEFAULT_CONFIG,
                'get_feedback_config': lambda self_inner: DEFAULT_CONFIG.feedback,
                'get_intelligence_config': lambda self_inner: DEFAULT_CONFIG.intelligence,
                'get_security_config': lambda self_inner: DEFAULT_CONFIG.security
            })()

        # 2. Initialize Intelligence (can be None in degraded mode)
        try:
            self.intelligence = IntelligenceOrchestrator(
                config=self.config_manager.get_intelligence_config(),
                storage=self.storage
            )
        except Exception as e:
            logger.error(f"Failed to initialize intelligence: {e}")
            self.intelligence = None

        # 3. Initialize Telemetry (using config)
        if self.config_manager:
            feedback_config = self.config_manager.get_feedback_config()
            self.telemetry = RateLimitedTelemetry(
                callback=self._notify_ui,
                max_events_per_second=feedback_config.max_events_per_second
            )
        else:
            # Emergency fallback for telemetry
            self.telemetry = RateLimitedTelemetry(callback=self._notify_ui, max_events_per_second=10)

        self.parser = PlanParser()
        self.tracker = TaskTracker()
        self.validator = TDDValidator()
        self.ai_client = nIAClaudeClient()
        self.quality_checker = QualityChecker()
        self.git_manager = GitBasedFileManager(str(self.project_path))
        self.issue_manager = IssueManager(self.project_path)
        self.structure_validator = FileStructureValidator(self.issue_manager)
        self.tech_detector = TechStackDetector()
        self.tech_stack = ""
        self.current_phase = "IDLE"
        self.venv_python: Optional[str] = None

        # Security Components
        self.security_auditor = SecurityAuditor(log_dir=os.path.join(self.project_path, ".nia", "security"))
        self.git_manager.set_security_auditor(self.security_auditor)
        self.path_validator = ParanoidPathValidator(base_dir=self.project_path)
        self.validator.security_auditor = self.security_auditor

        self.spec_path = project_path / "SPEC.md"
        self.plan_path = project_path / "IMPLEMENTATION_PLAN.md"
        self.prompt_path = project_path / "NIA_PROMPT.md"

    def _notify_ui(self, event_type, data):
        """Notify UI of state changes."""
        if event_type == 'phase_change':
            self.current_phase = data

        if event_type in self.ui_callbacks:
            try:
                # Many UI frameworks require calls from the main thread
                # but we leave that responsibility to the callback itself
                # or use a safe wrapper if needed.
                self.ui_callbacks[event_type](data)
            except Exception as e:
                logger.error(f"Error in UI callback {event_type}: {e}")

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

            # CHECK FOR BLOCKING ISSUES
            open_issues = self.issue_manager.get_issues(status='Open')
            critical_issues = [i for i in open_issues if i['priority'] == 'Critical']
            if critical_issues:
                self._log(f"🛑 BLOCKING: Found {len(critical_issues)} CRITICAL issues. Autonomous loop paused.", log_callback)
                self._notify_ui('phase_change', 'IDLE')
                # Wait or abort? Let's abort this run so user can fix and resume.
                return LoopResult("BLOCKED", iteration, f"Blocked by {len(critical_issues)} critical issues.", self._get_final_stats(start_time, tasks_planned, tasks_completed))

            self._log(f"\n=== nIA ITERATION {iteration + 1}/{max_iterations} ===", log_callback)
            self._log(f"📍 Project Path: {self.project_path}", log_callback)
            self._log(f"📂 Current Work Dir: {os.getcwd()}", log_callback)

            # Publish telemetry update
            self._notify_ui('telemetry_update', {
                'loop_current': iteration + 1,
                'loop_total': max_iterations
            })

            # 0. Ensure environment is ready
            if iteration == 0:
                self._setup_environment(log_callback)
                # Initialize tech_stack
                nia_config = self._get_nia_config()
                self.tech_stack = nia_config.get("tech_stack", "")
                if not self.tech_stack:
                    self._log("⚠️ No tech_stack specified in .nia_config.json, defaulting to 'frontend_web'", log_callback)
                    self.tech_stack = "frontend_web"

                # Auto-align structure
                self._align_project_structure(log_callback)

            # 1. Load fresh state
            try:
                spec = self.spec_path.read_text(encoding='utf-8')
                tasks = self.parser.parse(self.plan_path)
                tasks_planned = len(tasks)
                prompt = self.prompt_path.read_text(encoding='utf-8')
            except Exception as e:
                logger.error(f"Error loading files: {e}", exc_info=True)
                self._log(f"❌ Error loading files: {str(e)}", log_callback)
                self.issue_manager.create_issue(
                    category=self.issue_manager.CAT_DEPENDENCIES,
                    priority=self.issue_manager.PRIO_HIGH,
                    title=f"File loading error in iteration {iteration}",
                    description=f"File loading error: {str(e)}",
                    stack_trace=f"Iteration: {iteration}\n{str(e)}"
                )
                return LoopResult("ERROR", iteration, f"File loading error: {e}", self._get_final_stats(start_time, tasks_planned, tasks_completed))

            # 2. Find next task
            next_task = self.parser.find_next_pending(tasks)
            if not next_task:
                return LoopResult("ALL_COMPLETE", iteration, "✅ All tasks completed!", self._get_final_stats(start_time, tasks_planned, tasks_completed))

            # Mark as in_progress for UI
            next_task.status = 'in_progress'
            self._notify_ui('update_ai_plan', tasks)

            self._log(f"Target Task: {next_task.description}", log_callback)

            # 3. Create Checkpoint
            checkpoint = self.git_manager.create_checkpoint(f"Before: {next_task.description}")

            # 4. Get context (all project files)
            context = self._get_project_context()

            # 5. Ask AI for solution (with quality retry)
            max_retries = 3
            ai_feedback = ""
            requirements_feedback = ""
            active_test_file = None
            active_test_name = None

            # Initialize iteration state
            iter_state = IterationState(next_task.description)

            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        self._log(f"Attempt {attempt+1}: Retrying with targeted feedback...", log_callback)

                    combined_context = context
                    if ai_feedback:
                        combined_context += f"\n\nCRITICAL FEEDBACK FROM PREVIOUS ATTEMPT:\n{ai_feedback}"
                    if requirements_feedback:
                        combined_context += f"\n\n{requirements_feedback}"

                    # If we have a locked test file, insist on it
                    if iter_state.test_file:
                        combined_context += f"\n\n⚠️ CRITICAL: You must include the original test file in your response exactly as shown below:\n\n"
                        combined_context += f"File: {iter_state.test_file}\n"
                        combined_context += f"```python\n{iter_state.test_file_content}\n```\n"
                        combined_context += f"\nDO NOT modify the test file. Fix ONLY the implementation issues."

                        # Ensure we use the locked file even if the AI didn't return it in this specific response
                        active_test_file = iter_state.test_file
                        active_test_name = iter_state.test_name

                    # Fetch intelligence context
                    ram_context = ""
                    if self.intelligence:
                        try:
                            ram_context = self.intelligence.get_context()
                        except Exception as e:
                            logger.warning(f"Failed to fetch intelligence context: {e}")

                    try:
                        self._log(f"🤖 Calling AI Assistant (Attempt {attempt+1}/{max_retries+1})...", log_callback)
                        start_ai = time.time()

                        # Added a conceptual timeout if execute_nia_iteration supported it,
                        # but usually it's handled inside the client.
                        response = self.ai_client.execute_nia_iteration(
                            spec=spec,
                            plan=self.plan_path.read_text(encoding='utf-8'),
                            prompt=prompt,
                            task=next_task,
                            context=combined_context,
                            ram_context=ram_context
                        )
                        self._log(f"✅ AI response received in {time.time() - start_ai:.2f}s", log_callback)
                    except QuotaExhaustedError as qe:
                        self._log(f"⛔ CRITICAL: API Quota Exhausted. {str(qe)}", log_callback)
                        self.git_manager.create_checkpoint(f"Paused: Quota Exhausted during {next_task.description}")
                        return LoopResult("QUOTA_EXHAUSTED", iteration, str(qe), self._get_final_stats(start_time, tasks_planned, tasks_completed))

                    if stop_event.is_set():
                        return LoopResult("STOPPED", iteration, "Loop stopped by user")

                    # DETECT INCORRECT EXECUTION SIGNALS (mkdir, cd, etc.)
                    raw_lower = response.raw.lower()
                    if "mkdir" in raw_lower or "cd " in raw_lower or "npm " in raw_lower:
                        self._log("⚠️ WARNING: AI attempted to use bash commands (mkdir/cd/npm). These are NOT executed. AI must use file blocks.", log_callback)

                    # LOG PARSED FILES DIAGNOSTICS
                    self._log(f"\n=== FILE PROCESSING DEBUG ===", log_callback)
                    self._log(f"Files detected by parser: {len(response.files)}", log_callback)
                    for filename in response.files:
                        content = response.files[filename]
                        self._log(f"  - {filename} ({len(content)} chars)", log_callback)

                        if filename.endswith('.gitkeep'):
                            self._log(f"    ⚠️ .gitkeep file (empty content expected)", log_callback)

                        if '/' in filename or '\\' in filename:
                            parts = filename.replace('\\', '/').split('/')
                            if len(parts) > 1:
                                self._log(f"    📁 Nested path detected: {'/'.join(parts[:-1])}", log_callback)

                    # VALIDATE & AUTO-FIX structure
                    parsed_files = [{"path": p, "content": c} for p, c in response.files.items()]
                    fixed_files, warnings = self.structure_validator.validate_and_fix(
                        files=parsed_files,
                        tech_stack=self.tech_stack
                    )

                    for warning in warnings:
                        self._log(f"⚠️ {warning}", log_callback)

                    # Convert back to dict format
                    response.files = {f["path"]: f["content"] for f in fixed_files}

                    # RE-IDENTIFY test file after structure correction
                    response.test_file = response._identify_test_file()

                    # VALIDATE CONSISTENCY with IterationState
                    is_consistent, consistency_error = iter_state.validate_retry_attempt(response.files, response.test_file)
                    if not is_consistent:
                        self._log(f"⚠️ AI response inconsistent: {consistency_error}", log_callback)
                        if attempt < max_retries:
                            ai_feedback = f"INCONSISTENCY ERROR: {consistency_error}. Please stick to the previously established test file and structure."
                            continue
                        else:
                            self._log("❌ Consistency failed after all retries.", log_callback)
                            # Fallback to graceful degradation if possible
                            break

                    # Specific warning if critical files are missing for frontend_web
                    if self.tech_stack == 'frontend_web':
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
                            self.issue_manager.create_issue(
                                category=self.issue_manager.CAT_AI,
                                priority=self.issue_manager.PRIO_MEDIUM,
                                title=f"AI Empty Response: {next_task.description}",
                                description="AI provided no code changes after multiple retries",
                                task=next_task.description
                            )
                            self.tracker.mark_blocked(self.plan_path, next_task, "AI provided no code changes after retries.")
                            return LoopResult("BLOCKED", iteration, "AI provided no code changes.", self._get_final_stats(start_time, tasks_planned, tasks_completed))
                        ai_feedback = "You provided no code changes. Please provide the necessary implementation files."
                        continue

                    # 6. TDD Cycle: RED Phase (ONLY on attempt 0)
                    if attempt == 0:
                        active_test_file = response.test_file
                        active_test_name = response.test_name

                        # Register first attempt to lock in files (and test file if present)
                        iter_state.register_attempt(response.files, False, active_test_file, active_test_name)

                    if attempt == 0 and active_test_file:
                        self._log(f"=== STARTING RED PHASE ===", log_callback)
                        self._notify_ui('phase_change', 'RED')
                        self._log_progress_bars(log_callback)
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

                        # Capture test output for UI streaming
                        def red_test_cb(line, out_type='stdout'):
                            self._notify_ui('test_output', {'line': line, 'type': out_type})

                        val_red = self.validator.validate_red(
                            self.project_path,
                            str(test_file_path),
                            active_test_name,
                            self.venv_python,
                            output_callback=red_test_cb
                        )
                        self._log_validation_result(val_red, "RED", log_callback)

                        # AUTO-FIX for missing selenium in frontend_web
                        if not val_red.success and "ModuleNotFoundError: No module named 'selenium'" in val_red.stderr and self.tech_stack == 'frontend_web':
                            self._log("🔍 Detected missing 'selenium' dependency in RED phase. Auto-fixing...", log_callback)
                            self._handle_missing_dependency("selenium", log_callback)

                            # Retry RED phase
                            self._log("🔄 Retrying RED phase after auto-fix...", log_callback)
                            val_red = self.validator.validate_red(
                                self.project_path,
                                str(test_file_path),
                                active_test_name,
                                self.venv_python,
                                output_callback=red_test_cb
                            )
                            self._log_validation_result(val_red, "RED (RETRY)", log_callback)

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
                            # Note: If RED fails because test PASSES, it's not always a blocker,
                            # but it might indicate AI is using existing code.
                            self.issue_manager.create_issue(
                                category=self.issue_manager.CAT_TESTING,
                                priority=self.issue_manager.PRIO_MEDIUM,
                                title=f"RED Phase Failure: {next_task.description}",
                                description=f"RED phase failed: {val_red.message}",
                                task=next_task.description,
                                stack_trace=val_red.stderr
                            )
                            # We proceed anyway to try GREEN, or we could retry RED?
                            # Usually if RED fails (test passes), it means implementation is already there or test is bad.

                    if stop_event.is_set():
                        return LoopResult("STOPPED", iteration, "Loop stopped by user")

                    # 7. TDD Cycle: GREEN Phase
                    self._log("=== APPLYING IMPLEMENTATION CODE ===", log_callback)

                    # Week 2 Fix: Auto-inject test file if missing from AI response
                    if iter_state.test_file and iter_state.test_file not in response.files:
                        self._log(f"⚠️ LLM omitted test file {iter_state.test_file}. Auto-injecting from IterationState.", log_callback)
                        response.files[iter_state.test_file] = iter_state.test_file_content

                    # WRITE FILES FIRST ✅ (as requested by user)
                    written_files = []
                    self._log(f"📝 Writing {len(response.files)} files to disk (Attempt {attempt+1}):", log_callback)
                    for filename, content in response.files.items():
                        # If it's a retry, we only skip writing the test file if it ALREADY exists.
                        # This prevents losing the test file after a Git rollback.
                        if attempt > 0 and filename == active_test_file:
                            if (self.project_path / filename).exists():
                                self._log(f"  (Skipping existing test file: {filename})", log_callback)
                                continue
                            else:
                                self._log(f"  (Restoring missing test file: {filename})", log_callback)

                        self._log(f"  - Writing: {filename} ({len(content)} bytes)", log_callback)
                        if self._write_file(filename, content, log_callback):
                            written_files.append(filename)

                    # PHYSICAL VERIFICATION
                    self._log("🔍 Verifying physical file existence...", log_callback)
                    missing_physical = []
                    for f in response.files:
                        full_p = self.project_path / f
                        exists = full_p.exists()
                        status = "✅" if exists else "❌"
                        self._log(f"    {status} {f}: {exists}", log_callback)
                        if not exists:
                            missing_physical.append(f)

                    if missing_physical:
                        self._log(f"❌ CRITICAL ERROR: Files not found on disk after write: {', '.join(missing_physical)}", log_callback)
                        if attempt < max_retries:
                            ai_feedback = f"System failed to write files to disk: {', '.join(missing_physical)}. Please ensure paths are correct and provide full content."
                            continue
                        else:
                            self.issue_manager.create_issue(
                                category=self.issue_manager.CAT_GIT,
                                priority=self.issue_manager.PRIO_CRITICAL,
                                title=f"File Write Failure: {next_task.description}",
                                description=f"Physical file verification failed: {', '.join(missing_physical)}",
                                task=next_task.description,
                                files_affected=missing_physical
                            )
                            self.tracker.mark_blocked(self.plan_path, next_task, f"File system write failure: {', '.join(missing_physical)}")
                            return LoopResult("ERROR", iteration, "Physical file verification failed")

                    self._log(f"✅ Successfully written: {len(written_files)} files", log_callback)
                    self._log_project_structure(log_callback)

                    # Quality Check AFTER writing files
                    nia_config = self._get_nia_config()
                    tech_config = nia_config.get("tech_config", {})
                    quality_issues = self.quality_checker.validate(response.files, tech_config)

                    # MANDATORY CRITICAL FILES for frontend_web (Informational only now)
                    if self.tech_stack == 'frontend_web':
                        detected_paths = set(response.files.keys())
                        if 'index.html' not in detected_paths:
                            quality_issues.append(QualityIssue(
                                "index.html",
                                "Recommended: index.html missing. It is usually needed to maintain project state.",
                                "WARNING", "MISSING_CRITICAL"
                            ))

                        has_css = any(f in detected_paths for f in ['css/main.css', 'styles/main.css', 'css/style.css', 'style.css'])
                        if not has_css:
                            quality_issues.append(QualityIssue(
                                "css/style.css",
                                "Recommended: No CSS file detected. Providing styles is best practice.",
                                "WARNING", "MISSING_CRITICAL"
                            ))

                    if quality_issues:
                        # Split issues into errors and warnings
                        errors = [i for i in quality_issues if i.severity == "ERROR"]
                        warnings = [i for i in quality_issues if i.severity == "WARNING"]

                        if warnings:
                            self._log("⚠️ QUALITY WARNINGS (Proceeding anyway):", log_callback)
                            for w in warnings:
                                self._log(f"  - {w}", log_callback)

                        if errors:
                            self._log("❌ QUALITY ERRORS DETECTED:", log_callback)
                            for e in errors:
                                self._log(f"  - {e}", log_callback)

                            if attempt < max_retries:
                                # DA-005: Incremental Quality Improvement
                                quality_feedback = self.quality_checker.generate_feedback(errors)
                                ai_feedback += "\n\n" + quality_feedback

                                # DA-001: Smart Rollback (Selective)
                                failed_files = list(set([i.filename for i in errors]))
                                self._log(f"🔄 Quality failed. Attempting selective rollback of {len(failed_files)} files...", log_callback)

                                self.git_manager.smart_rollback(failed_files, checkpoint)
                                self._log("⏪ Selective rollback complete. Retrying with targeted feedback.", log_callback)
                                continue
                            else:
                                error_msgs = [str(e) for e in errors]
                                self.issue_manager.create_issue(
                                    category=self.issue_manager.CAT_QUALITY,
                                    priority=self.issue_manager.PRIO_MEDIUM,
                                    title=f"Quality Check Failure: {next_task.description}",
                                    description=f"Quality standards not met: {', '.join(error_msgs[:3])}",
                                    task=next_task.description
                                )
                                self._log("❌ Quality below standards after all retries.", log_callback)
                                self.tracker.mark_blocked(self.plan_path, next_task, f"Quality standards not met: {', '.join(error_msgs)}")
                                return LoopResult("BLOCKED", iteration, "Quality standards not met")
                        else:
                            self._log("✅ Quality check passed (with warnings)", log_callback)
                    else:
                        self._log("✅ Quality check passed", log_callback)

                    tests_passed = False
                    if active_test_file:
                        self._log(f"=== STARTING GREEN PHASE ===", log_callback)
                        self._notify_ui('phase_change', 'GREEN')
                        self._log_progress_bars(log_callback)

                        test_file_path = self.project_path / active_test_file

                        # Capture test output for UI streaming
                        def green_test_cb(line, out_type='stdout'):
                            self._notify_ui('test_output', {'line': line, 'type': out_type})

                        val_green = self.validator.validate_green(
                            self.project_path,
                            str(test_file_path),
                            active_test_name,
                            self.venv_python,
                            output_callback=green_test_cb
                        )
                        self._log_validation_result(val_green, "GREEN", log_callback)

                        if not val_green.success:
                            self._log(f"❌ GREEN Phase failed: {val_green.message}", log_callback)

                            # Update Intelligence with failure
                            if self.intelligence:
                                try:
                                    self.intelligence.update_after_iteration({
                                        "phase": "GREEN",
                                        "success": False,
                                        "failure_type": "LogicError", # Could be more specific
                                        "solution_attempted": next_task.description
                                    })
                                except: pass

                            # Register failed attempt
                            if attempt > 0: # Already registered attempt 0
                                iter_state.register_attempt(response.files, False)

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
                                # Before blocking, check if ANY previous attempt passed tests
                                last_good_files = iter_state.get_last_successful_files()
                                if last_good_files:
                                    self._log("💡 Graceful degradation: Tests passed in a previous attempt. Using that version.", log_callback)
                                    # Restore that version
                                    for f, c in last_good_files.items():
                                        self._write_file(f, c, log_callback)
                                    tests_passed = True
                                    break

                                self.issue_manager.create_issue(
                                    category=self.issue_manager.CAT_TESTING,
                                    priority=self.issue_manager.PRIO_HIGH,
                                    title=f"GREEN Phase Failure: {next_task.description}",
                                    description=f"GREEN phase failed after {max_retries+1} attempts",
                                    task=next_task.description,
                                    stack_trace=val_green.stderr
                                )
                                self.tracker.mark_blocked(self.plan_path, next_task, f"GREEN phase failed: {val_green.stderr}")
                                return LoopResult("BLOCKED", iteration, "GREEN phase failed.", self._get_final_stats(start_time, tasks_planned, tasks_completed))

                            similar = self.issue_manager.get_similar_issues(val_green.message)
                            ai_feedback = f"TEST FAILURE: {val_green.stderr}\n\nFIX REQUIRED: Please ensure the implementation satisfies the test requirements. Do NOT change the test file name or structure."
                            ai_feedback += self.issue_manager.format_suggestions(similar)

                            # Selective rollback of implementation files to try again
                            impl_files = [f for f in response.files if f != active_test_file]
                            self.git_manager.smart_rollback(impl_files, checkpoint)
                            continue

                        self._log("✅ GREEN phase passed.", log_callback)
                        tests_passed = True
                        self._last_test_passed = True

                    # Register successful attempt (for future degradation if quality fails later)
                    if attempt > 0:
                        iter_state.register_attempt(response.files, tests_passed)
                    else:
                        # Attempt 0 was already registered but we update the pass status
                        iter_state.update_attempt_status(0, tests_passed)

                    # Create a checkpoint after successful GREEN phase
                    # This allows REFACTOR phase to rollback to this state instead of pre-iteration state
                    green_checkpoint = self.git_manager.create_checkpoint(f"GREEN passed: {next_task.description}")

                    # MANDATORY FILES VALIDATION (Informational)
                    missing_critical = self._validate_critical_files(self.tech_stack)
                    if missing_critical:
                        self._log(f"⚠️ Warning: Missing expected files for {self.tech_stack}: {', '.join(missing_critical)}", log_callback)
                        # We no longer block on this, just log it as a warning.
                        # If the tests pass, the implementation is likely sufficient for the task.

                    # Success, break retry loop
                    break

                except Exception as e:
                    logger.error(f"Error during iteration attempt: {e}", exc_info=True)
                    self._log(f"❌ Error during iteration attempt: {str(e)}", log_callback)

                    self.issue_manager.create_issue(
                        category=self.issue_manager.CAT_AI,
                        priority=self.issue_manager.PRIO_HIGH,
                        title=f"Iteration Error: {next_task.description}",
                        description=f"Error during iteration attempt: {str(e)}",
                        task=next_task.description,
                        stack_trace=str(e)
                    )

                    # Rollback on unexpected error - Preservation fix
                    self.git_manager.rollback_preserving_tests(checkpoint)
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
                self._notify_ui('phase_change', 'REFACTOR')
                self._log_progress_bars(log_callback)
                self._log("Verifying all tests...", log_callback)
                # Capture test output for UI streaming
                def refactor_test_cb(line, out_type='stdout'):
                    self._notify_ui('test_output', {'line': line, 'type': out_type})

                val_refactor = self.validator.validate_refactor(
                    self.project_path,
                    self.venv_python,
                    output_callback=refactor_test_cb
                )
                self._log_validation_result(val_refactor, "REFACTOR", log_callback)

                if not val_refactor.success:
                    self._last_test_passed = False
                    self._log(f"❌ REFACTOR Phase failed: {val_refactor.message}", log_callback)
                    self.issue_manager.create_issue(
                        category=self.issue_manager.CAT_TESTING,
                        priority=self.issue_manager.PRIO_HIGH,
                        title=f"Refactor Failure: {next_task.description}",
                        description=f"REFACTOR phase failed (Regression): {val_refactor.message}",
                        task=next_task.description,
                        stack_trace=val_refactor.stderr
                    )
                    # DA-004: Rollback preserving tests to the GREEN state
                    self._log("⏪ Undoing REFACTOR changes due to validation failure (preserving tests).", log_callback)
                    # Rollback to green_checkpoint if it exists, otherwise to iteration checkpoint
                    target_sha = green_checkpoint if 'green_checkpoint' in locals() else checkpoint
                    self.git_manager.rollback_preserving_tests(target_sha)
                    self.git_manager.record_failed_iteration()
                    self.tracker.mark_blocked(self.plan_path, next_task, f"Regression detected during refactor phase: {val_refactor.message}")
                    return LoopResult("BLOCKED", iteration, "Refactor phase failed.", self._get_final_stats(start_time, tasks_planned, tasks_completed))

                self._log("✅ All tests passed.", log_callback)
                self._last_test_passed = True

                # 11. Code Quality Metrics (Informational)
                try:
                    q_metrics = self._analyze_code_quality()
                    self._log("📊 Code Quality Metrics (Informational):", log_callback)
                    for key, value in q_metrics.items():
                        self._log(f"  - {key}: {value}", log_callback)

                    # Update Intelligence with quality data
                    if self.intelligence:
                        # Extract per-file quality
                        file_quality = {}
                        exclude_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'tests'}
                        for root, dirs, files in os.walk(self.project_path):
                            dirs[:] = [d for d in dirs if d not in exclude_dirs]
                            for file in files:
                                if file.endswith(('.py', '.js', '.ts', '.html', '.css')):
                                    path = Path(root) / file
                                    rel_path = str(path.relative_to(self.project_path))
                                    try:
                                        content = path.read_text(encoding='utf-8', errors='replace')
                                        lines = len([l for l in content.splitlines() if l.strip()])
                                        file_quality[rel_path] = {"current": lines}
                                    except: pass

                        self.intelligence.update_after_iteration({
                            "quality_update": file_quality
                        })
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

                    # Notify UI of commit and diff
                    try:
                        diff_content = Path(diff_path).read_text(encoding='utf-8')
                        self._notify_ui('git_commit', {'message': commit_msg, 'diff': diff_content})
                    except:
                        pass
                else:
                    self._log("⚠️ No patch generated (possibly no changes committed).", log_callback)

                # 13. Update Plan
                self._log(f"📝 Marking task as completed in plan: {next_task.description}", log_callback)
                self.tracker.mark_completed(self.plan_path, next_task)

                # IMPORTANT: Commit the plan update so it's not lost if a subsequent step or iteration fails
                self.git_manager.create_checkpoint(f"Plan Update: Completed {next_task.description}")

                tasks_completed += 1

                # 14. Auto-resolve related issues
                try:
                    self.issue_manager.resolve_issues_by_task(
                        task_description=next_task.description,
                        resolution=f"Successfully completed task: {next_task.description}",
                        prevention="Verified by TDD cycle and REFACTOR phase passing."
                    )

                    # Regenerate Wiki
                    self.issue_manager.generate_wiki()
                except Exception as we:
                    logger.warning(f"Error updating issues or generating wiki: {we}")

                # 15. Update UI Metrics
                self._publish_metrics()

                # 16. Update Intelligence
                if self.intelligence:
                    try:
                        # Collect iteration results
                        it_data = {
                            "iteration_increment": True,
                            "phase": "REFACTOR", # Final phase of successful loop
                            "success": True,
                            "tech_stack": self.tech_stack,
                            "iterations": iteration + 1,
                            "quality_standards": "standard", # Could be more dynamic
                            "active_test": active_test_file,
                            "solution_attempted": next_task.description
                        }
                        self.intelligence.update_after_iteration(it_data)
                    except Exception as e:
                        logger.warning(f"Failed to update intelligence: {e}")

                # Back to IDLE
                self._notify_ui('phase_change', 'IDLE')

            except Exception as e:
                self._notify_ui('phase_change', 'IDLE')
                logger.error(f"Error during iteration: {e}", exc_info=True)
                self._log(f"❌ Error during iteration: {str(e)}", log_callback)

                self.issue_manager.create_issue(
                    category=self.issue_manager.CAT_DEPENDENCIES,
                    priority=self.issue_manager.PRIO_CRITICAL,
                    title=f"Critical Iteration Error: {next_task.description}",
                    description=f"Critical error during iteration: {str(e)}",
                    task=next_task.description,
                    stack_trace=str(e)
                )

                # Ensure rollback on finalization error
                self.git_manager.rollback_preserving_tests(checkpoint)
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
        # Allow common setup files at root regardless of tech stack
        filename = os.path.basename(filepath).lower()
        if filename in ['.gitignore', 'readme.md', 'package.json', 'nia_prompt.md', 'spec.md', 'implementation_plan.md']:
            return True

        return self.structure_validator.is_valid(filepath, tech_stack)

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
            tech_stack = self.tech_stack or self._get_nia_config().get("tech_stack", "frontend_web")

            # DEFCON 1 Path Validation
            try:
                safe_path = self.path_validator.validate(rel_path)
                full_path = Path(safe_path)
            except SecurityException as se:
                self.security_auditor.log_security_violation(
                    severity='HIGH',
                    category='PATH_TRAVERSAL_ATTEMPT',
                    description=f"Blocked attempt to write to forbidden path: {rel_path}",
                    error=str(se)
                )
                self._log(f"❌ SECURITY ALERT: Blocked attempt to write to forbidden path: {rel_path}", log_callback)
                return False

            if not self._validate_file_path(rel_path, tech_stack):
                msg = f"Skipping file {rel_path}: violates project structure for {tech_stack}"
                self._log(f"⚠️ {msg}", log_callback)
                logging.warning(msg)
                return False

            # VALIDATION: Prevent writing empty files (unless allowed like .gitkeep)
            if not content.strip() and not rel_path.endswith('.gitkeep'):
                msg = f"Refusing to write empty file: {rel_path}"
                self._log(f"❌ {msg}", log_callback)
                logging.error(msg)
                return False

            # Week 1 Fix: Use atomic writes to prevent corruption on crash
            self.storage.write_atomic(rel_path, content)

            self.security_auditor.log_file_access('write', rel_path, approved=True)

            # Immediate verification
            if full_path.exists():
                self._log(f"Generated file: {rel_path}", log_callback)
                self._notify_ui('file_created', {'path': str(full_path), 'size': len(content)})
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
                # Week 1 Fix: Prevent indefinite hangs during env setup
                result = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='replace', timeout=180)

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

    def _publish_metrics(self):
        """Calculates and publishes project metrics to the UI."""
        try:
            open_issues = self.issue_manager.get_issues(status='Open')
            quality_issues = [i for i in open_issues if i['category'] == self.issue_manager.CAT_QUALITY]

            # Basic stats
            stats = self._analyze_code_quality()

            # For tests, we use the last validation result if available
            # This is a simplified version; real suite parsing would be better
            test_info = "0/0"
            if hasattr(self, '_last_test_passed'):
                test_info = "1/1" if self._last_test_passed else "0/1"

            metrics = {
                'tests': test_info,
                'coverage': 0, # Placeholder
                'quality': len(quality_issues)
            }
            self._notify_ui('update_metrics', metrics)
        except Exception as e:
            logger.error(f"Error publishing metrics: {e}")

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
            'frontend_web': ['index.html'],
            'python_backend': ['requirements.txt'],
            'node_js': ['package.json']
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

    def _handle_missing_dependency(self, package: str, log_callback=None):
        """
        Adds package to requirements.txt, updates sandbox whitelist, and installs it.
        Strictly follows whitelist and security patterns.
        """
        # Validate package name security
        security_config = self.config_manager.get_security_config()
        pattern = security_config.package_name_pattern
        if not re.match(pattern, package):
            self._log(f"❌ SECURITY ALERT: Blocked invalid package name: {package}", log_callback)
            return False

        if package not in security_config.safe_packages:
            self._log(f"⚠️ Package '{package}' is not in safe whitelist. Skipping auto-install.", log_callback)
            return False

        self._log(f"📦 Auto-adding missing dependency: {package}...", log_callback)

        try:
            # 1. Add to requirements.txt
            req_path = self.project_path / "requirements.txt"
            content = ""
            if req_path.exists():
                try:
                    content = req_path.read_text(encoding='utf-8')
                except Exception:
                    pass

            if package.lower() not in content.lower():
                new_content = content.rstrip() + f"\n{package}\n"
                req_path.write_text(new_content, encoding='utf-8')
                self._log(f"✅ Added '{package}' to {req_path.name}", log_callback)

            # 2. Add to SecureSandbox whitelist via TDDValidator
            if hasattr(self.validator, 'add_allowed_import'):
                self.validator.add_allowed_import(package)
                self._log(f"✅ Added '{package}' to sandbox whitelist", log_callback)

            # 3. Install package
            python_exe = self.venv_python or sys.executable
            self._log(f"Installing {package} using {python_exe}...", log_callback)

            # Use --break-system-packages if we're using system python
            cmd = [python_exe, "-m", "pip", "install", package]
            if python_exe == sys.executable:
                cmd.append("--break-system-packages")

            timeout = security_config.pip_install_timeout
            result = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='replace', timeout=timeout)

            if result.returncode == 0:
                self._log(f"✅ {package} installed successfully.", log_callback)
                if self.intelligence:
                    self.intelligence.update_after_iteration({
                        "auto_fix": {"type": "dependency", "package": package},
                        "auto_detected": [package]
                    })
                return True
            else:
                self._log(f"❌ Failed to install {package}: {result.stderr}", log_callback)
                return False

        except subprocess.TimeoutExpired:
             self._log(f"❌ Timeout installing {package} (max {timeout}s)", log_callback)
             return False
        except Exception as e:
            self._log(f"❌ Error during {package} auto-fix: {e}", log_callback)
            return False

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

    def _align_project_structure(self, log_callback=None):
        """Auto-creates missing folders from default_structure with .gitkeep."""
        if not self.tech_stack:
            return

        tech_config = self.tech_detector.get_config(self.tech_stack)
        default_structure = tech_config.get('default_structure', [])

        if not default_structure:
            return

        self._log(f"🏗️ Aligning project structure for {self.tech_stack}...", log_callback)
        self._log(f"  Target directory: {self.project_path}", log_callback)
        created_dirs = []

        for item in default_structure:
            if item.endswith('/'):
                dir_path = self.project_path / item
                if not dir_path.exists():
                    try:
                        dir_path.mkdir(parents=True, exist_ok=True)
                        # Add .gitkeep to ensure git tracks the empty directory
                        gitkeep = dir_path / ".gitkeep"
                        gitkeep.touch()
                        created_dirs.append(item)
                        self._log(f"  ✅ Auto-created: {item} (with .gitkeep)", log_callback)
                    except Exception as e:
                        logger.error(f"Failed to create directory {item}: {e}")

        if created_dirs and self.intelligence:
            # Provide more complete data for RAM refresh
            self.intelligence.update_after_iteration({
                "tech_stack": self.tech_stack,
                "phase": "INIT",
                "auto_fix": {"type": "structure", "dirs": created_dirs},
                "warnings": [f"Auto-created: {', '.join(created_dirs)}"]
            })

    def _log_progress_bars(self, log_callback=None):
        """Displays ASCII progress bars for the project."""
        if not self.intelligence or not self.intelligence.metrics_manager:
            return

        metrics = self.intelligence.metrics_manager.get_metrics()

        # Calculate percentages (simplified)
        tasks = self.parser.parse(self.plan_path)
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == 'completed'])

        goal_pct = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0

        # Structure alignment pct
        tech_config = self.tech_detector.get_config(self.tech_stack)
        default_structure = tech_config.get('default_structure', [])
        existing_dirs = 0
        total_dirs = len([i for i in default_structure if i.endswith('/')])
        if total_dirs > 0:
            for item in default_structure:
                if item.endswith('/') and (self.project_path / item).exists():
                    existing_dirs += 1
            struct_pct = int((existing_dirs / total_dirs * 100))
        else:
            struct_pct = 100

        # Quality pct
        quality_standards = tech_config.get('quality_standards', {})
        total_q_types = len(quality_standards)
        quality_pct = 0
        if total_q_types > 0:
             q_prog = metrics.get('quality_progress', {})
             total_score = 0
             for ext, std in quality_standards.items():
                 target = std.get('min_lines', 0)
                 if target > 0:
                     # Find max current lines for this extension
                     current_max = 0
                     for f_path, f_data in q_prog.items():
                         if f_path.endswith(ext):
                             current_max = max(current_max, f_data.get('current', 0))

                     score = min(1.0, current_max / target)
                     total_score += score
                 else:
                     total_score += 1.0
             quality_pct = int((total_score / total_q_types) * 100)
        else:
             quality_pct = 100

        def get_bar(pct):
            filled = int(pct / 10)
            return "█" * filled + "░" * (10 - filled)

        self._log("\n📈 Project Progress", log_callback)
        self._log(f"├─ Structure: {get_bar(struct_pct)} {struct_pct}%", log_callback)
        self._log(f"├─ Quality:   {get_bar(quality_pct)} {quality_pct}%", log_callback)
        self._log(f"├─ Goal:      {get_bar(goal_pct)} {goal_pct}%", log_callback)
        self._log("└─ Phase:     " + self._get_current_phase(), log_callback)

        # Emit telemetry
        self.telemetry.emit('progress_update', {
            "structure": struct_pct,
            "quality": quality_pct,
            "goal": goal_pct,
            "phase": self._get_current_phase()
        })

    def _get_current_phase(self) -> str:
        return self.current_phase
