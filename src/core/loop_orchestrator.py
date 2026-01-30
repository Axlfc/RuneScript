from pathlib import Path
import time
import os
import subprocess
from typing import Optional, List
from .plan_parser import PlanParser, Task
from .task_tracker import TaskTracker
from .tdd_validator import TDDValidator
from .nia_ai_client import nIAAIClient, nIAResponse

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
        self.ai_client = nIAAIClient()

        self.spec_path = project_path / "SPEC.md"
        self.plan_path = project_path / "IMPLEMENTATION_PLAN.md"
        self.prompt_path = project_path / "NIA_PROMPT.md"

    def run(self, max_iterations: int = 20, log_callback=None) -> LoopResult:
        if not self.spec_path.exists() or not self.plan_path.exists() or not self.prompt_path.exists():
            return LoopResult("ERROR", 0, "Missing required nIA files (SPEC.md, IMPLEMENTATION_PLAN.md, or NIA_PROMPT.md)")

        for iteration in range(max_iterations):
            self._log(f"\n=== nIA ITERATION {iteration + 1}/{max_iterations} ===", log_callback)

            # 1. Load fresh state
            spec = self.spec_path.read_text()
            tasks = self.parser.parse(self.plan_path)
            prompt = self.prompt_path.read_text()

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
                    plan=self.plan_path.read_text(),
                    prompt=prompt,
                    task=next_task,
                    context=context
                )

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

                    val_red = self.validator.validate_red(str(self.project_path / response.test_file), response.test_name)
                    if not val_red.success:
                        self._log(f"❌ RED Phase failed: {val_red.message}", log_callback)
                        # Maybe the implementation already existed?
                        # Continue to GREEN anyway if it passes, but TDD says it should fail.
                        # For now, we follow strict TDD.

                # 6. TDD Cycle: GREEN Phase
                self._log("Applying implementation code...", log_callback)
                for filename, content in response.files.items():
                    self._write_file(filename, content)

                if response.test_file:
                    val_green = self.validator.validate_green(str(self.project_path / response.test_file), response.test_name)
                    if not val_green.success:
                        self._log(f"❌ GREEN Phase failed: {val_green.message}", log_callback)
                        self.tracker.mark_blocked(self.plan_path, next_task, f"GREEN phase failed: {val_green.stderr}")
                        return LoopResult("BLOCKED", iteration, "GREEN phase failed.")
                    self._log("✅ GREEN phase passed.", log_callback)

                # 7. TDD Cycle: REFACTOR Phase
                self._log("Verifying all tests...", log_callback)
                val_refactor = self.validator.validate_refactor(self.project_path)
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
                        content = path.read_text()
                        context.append(f"File: {rel_path}\n```\n{content}\n```")
                    except Exception:
                        pass
        return "\n\n".join(context)

    def _write_file(self, rel_path: str, content: str):
        full_path = self.project_path / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)

    def _git_commit(self, message: str):
        try:
            # Check if git repo
            if not (self.project_path / ".git").exists():
                subprocess.run(["git", "init"], cwd=self.project_path, capture_output=True)

            subprocess.run(["git", "add", "."], cwd=self.project_path, capture_output=True)
            subprocess.run(["git", "commit", "-m", message], cwd=self.project_path, capture_output=True)
        except Exception:
            pass

    def _log(self, message: str, callback):
        if callback:
            callback(message)
        print(message)
