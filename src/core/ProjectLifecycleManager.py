import os
import logging
import threading
import subprocess
import uuid
import time
import json
import re
import glob
from pathlib import Path
from tkinter import messagebox
from typing import Dict, Any

from src.utils.parser_utils import AIResponseParser
from src.utils.ProjectIO import ProjectIO
from src.utils.test_runner import run_pytest
from src.models.WebProjectGenerator import WebProjectGenerator
from src.generators.spec_generator import SpecGenerator
from src.generators.plan_generator import PlanGenerator
from src.generators.plan_reviewer import PlanReviewer
from src.core.loop_orchestrator import LoopOrchestrator
from src.core.plan_parser import PlanParser

class ProjectLifecycleManager:
    """
    Manages project lifecycle including creation, generation, and testing.
    """

    def __init__(self, controller):
        self.controller = controller
        self.generation_in_progress = False
        self.stop_event = threading.Event()

    def generate_project_with_ai(self, nia_mode: bool = False):
        """Start autonomous project generation with AI"""
        raw_prompt = self.controller.ui_manager.prompt_entry.get()
        prompt = AIResponseParser.sanitize_prompt(raw_prompt)

        if not AIResponseParser.validate_prompt(prompt):
            self.controller.safe_ui_call(
                messagebox.showwarning,
                "Invalid Prompt",
                "Please provide a clear, meaningful project description."
            )
            return

        self.controller.ui_manager.log_output("Starting AI-based autonomous project generation...")
        self.controller.ui_manager.toggle_generation_ui(False)
        self.generation_in_progress = True
        self.stop_event.clear()

        try:
            # Create new project
            project_id = str(uuid.uuid4())
            project_path = os.path.normpath(os.path.join(self.controller.projects_base_dir, project_id))
            os.makedirs(project_path, exist_ok=True)
            self.controller.current_project = project_path

            if nia_mode:
                # Start nIA autonomous loop
                self.controller.ui_manager.log_output(f"Launching nIA Autonomous Loop for: {prompt}")
                thread = threading.Thread(
                    target=self._run_nia_autonomous_loop,
                    args=(prompt, project_path)
                )
            else:
                # Start standard AI generation thread
                thread = threading.Thread(
                    target=self.controller.ai_orchestrator.threaded_ai_generation,
                    args=(prompt,)
                )

            thread.daemon = True
            thread.start()

        except Exception as e:
            logging.error(f"Project generation failed: {e}")
            self.controller.safe_ui_call(self.handle_generation_failure, f"Project generation failed: {e}")
            self.controller.ui_manager.toggle_generation_ui(True)
            self.generation_in_progress = False

    def finalize_project_generation(self, parsed_metadata):
        """Finalize project generation with enhanced documentation and structure"""
        try:
            if not self.controller.current_project:
                # Generate a sanitized project ID
                project_id = str(uuid.uuid4()).replace("-", "")
                project_path = os.path.normpath(os.path.join(self.controller.projects_base_dir, project_id))
                os.makedirs(project_path, exist_ok=True)
                self.controller.current_project = project_path
            else:
                project_path = self.controller.current_project

            # Create the project structure
            ProjectIO.create_structure(project_path, parsed_metadata, self.controller.ui_manager.log_output)

            # Generate web project files if it appears to be a web project
            raw_prompt = self.controller.ui_manager.prompt_entry.get()
            web_generator = WebProjectGenerator(project_path, self.controller.ui_manager.log_output)
            web_generator.generate_web_project(parsed_metadata, raw_prompt)

            # Generate and write all files from AI response
            self._process_generated_files(project_path, parsed_metadata)

            # Generate comprehensive project documentation
            self._generate_project_docs(project_path, parsed_metadata)

            # Set the current project and refresh the UI
            self.controller.current_project = project_path
            try:
                self.controller.ui_manager.file_manager.populate_tree_view()
            except Exception as e:
                logging.warning(f"Failed to populate project tree: {e}")

            # Format project structure and tasks for AI Plan
            project_tasks = parsed_metadata.get('project_tasks', [])

            # Update AI Plan with tasks
            formatted_tasks = '\n'.join(project_tasks)
            self.controller.ui_manager.update_ai_plan(formatted_tasks)

            # Run initial tests if applicable
            self._run_initial_tests(project_path)

            self.controller.ui_manager.log_output(
                f"Project generated successfully at {project_path}!"
            )

        except Exception as e:
            logging.error(f"Project finalization error: {e}")
            self.controller.safe_ui_call(messagebox.showerror, "Generation Error", str(e))
        finally:
            self.controller.ui_manager.toggle_generation_ui(True)
            self.generation_in_progress = False

    def _process_generated_files(self, project_path: str, parsed_metadata: Dict[str, Any]):
        """Process and write all files from AI response"""
        # Handle initial files structure
        initial_files = parsed_metadata.get("initial_files", {})

        # Support both dictionary and list formats for initial_files
        if isinstance(initial_files, dict):
            for filepath, content in initial_files.items():
                self._write_file(project_path, filepath, content)
        elif isinstance(initial_files, list):
            for file_entry in initial_files:
                if isinstance(file_entry, dict):
                    filepath = file_entry.get("filename")
                    content = file_entry.get("content", "# Placeholder content\n")
                    if filepath:
                        self._write_file(project_path, filepath, content)

        # Handle code files separately if provided
        code_files = parsed_metadata.get("code_files", [])
        if isinstance(code_files, list):
            for file_entry in code_files:
                if isinstance(file_entry, dict):
                    filepath = file_entry.get("filename") or file_entry.get("path")
                    content = file_entry.get("content", "# Placeholder content\n")
                    if filepath:
                        self._write_file(project_path, filepath, content)

        # Process test files if available
        test_files = parsed_metadata.get("test_files", [])
        if isinstance(test_files, list):
            for file_entry in test_files:
                if isinstance(file_entry, dict):
                    filepath = file_entry.get("filename") or file_entry.get("path")
                    content = file_entry.get("content", "# Placeholder test\n")
                    if filepath:
                        self._write_file(project_path, filepath, content)

    def _write_file(self, project_path: str, filepath: str, content: str):
        """Write file content to the specified path"""
        full_path = os.path.join(project_path, filepath)

        # Create directory if it doesn't exist
        dir_path = os.path.dirname(full_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logging.info(f"Created file: {filepath}")
            self.controller.ui_manager.log_output(f"Generated file: {filepath}")
        except Exception as e:
            logging.error(f"Failed to write file {filepath}: {e}")
            self.controller.ui_manager.log_output(f"Error writing file {filepath}: {e}")

    def _generate_project_docs(self, project_path, parsed_metadata):
        """Generate comprehensive project documentation"""
        # Ensure docs directory exists
        docs_dir = os.path.join(project_path, 'docs')
        os.makedirs(docs_dir, exist_ok=True)

        # Generate README.md
        readme_path = os.path.join(project_path, 'README.md')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(f"# {parsed_metadata.get('project_name', 'Unnamed Project')}\n\n")
            f.write("## Project Overview\n")
            f.write(parsed_metadata.get('project_description', 'No description available') + "\n\n")
            f.write("## Key Features\n")
            for feature in parsed_metadata.get('key_features', []):
                f.write(f"- {feature}\n")
            f.write("\n## Setup and Installation\n")
            f.write("(Add setup instructions here)\n")

        # Generate TODO.md with project tasks
        todo_path = os.path.join(project_path, 'TODO.md')
        with open(todo_path, 'w', encoding='utf-8') as f:
            f.write("# Project Tasks and Milestones\n\n")
            f.write("## Pending Tasks\n")
            for task in parsed_metadata.get('project_tasks', []):
                f.write(f"- [ ] {task}\n")

        # Generate LIST.md for feature tracking and prioritization
        list_path = os.path.join(project_path, 'LIST.md')
        with open(list_path, 'w', encoding='utf-8') as f:
            f.write("# Project Feature Tracking\n\n")

            # Implemented Features
            f.write("## Implemented Features\n")
            for feature in parsed_metadata.get('implemented_features', []):
                f.write(f"- [x] {feature}\n")

            # Planned Features
            f.write("\n## Planned Features\n")
            for feature in parsed_metadata.get('planned_features', []):
                f.write(f"- [ ] {feature}\n")

            # Priority Levels
            f.write("\n## Feature Priorities\n")
            priorities = parsed_metadata.get('feature_priorities', {})
            for priority, features in priorities.items():
                f.write(f"\n### {priority.capitalize()} Priority\n")
                for feature in features:
                    f.write(f"- {feature}\n")

            # Validation Notes
            f.write("\n## Validation Notes\n")
            validations = parsed_metadata.get('validation_notes', [])
            for note in validations:
                f.write(f"- {note}\n")

        # Generate development guide if metadata contains details
        dev_guide_path = os.path.join(docs_dir, 'DEVELOPMENT.md')
        with open(dev_guide_path, 'w', encoding='utf-8') as f:
            f.write("# Development Guide\n\n")
            f.write("## Project Structure\n")
            structure = parsed_metadata.get('project_structure', [])
            for item in structure:
                if isinstance(item, str):
                    f.write(f"- {item}\n")

            f.write("\n## Development Workflow\n")
            f.write("1. Write test case\n")
            f.write("2. Run tests (should fail)\n")
            f.write("3. Implement functionality\n")
            f.write("4. Run tests (should pass)\n")
            f.write("5. Refactor code\n")

    def _run_initial_tests(self, project_path: str):
        """Run initial tests if present in the project"""
        # Check if pytest is available and if there are test files
        test_dir = os.path.join(project_path, 'tests')
        if os.path.exists(test_dir) and os.listdir(test_dir):
            self.controller.ui_manager.log_output("Running initial tests...")
            try:
                success, stdout, stderr = run_pytest(project_path)
                if success:
                    self.controller.ui_manager.log_output("Initial tests passed successfully!")
                else:
                    self.controller.ui_manager.log_output(f"Initial tests failed:\n{stderr}")
            except Exception as e:
                logging.error(f"Failed to run initial tests: {e}")
                self.controller.ui_manager.log_output(f"Error running initial tests: {e}")

    def handle_generation_failure(self, error_message="AI generation failed. Please try again."):
        """Handle AI generation failure and update UI"""
        self.controller.safe_ui_call(messagebox.showerror, "AI Generation Failed", error_message)
        self.controller.ui_manager.toggle_generation_ui(True)
        self.generation_in_progress = False

    def run_tests(self):
        """Run tests for the current project"""
        if not self.controller.current_project:
            self.controller.ui_manager.log_output("No project selected. Create or open a project first.")
            return

        success, stdout, stderr = run_pytest(self.controller.current_project)

        self.controller.ui_manager.log_output(stdout)

        if success:
            self.controller.ui_manager.log_output("Tests passed successfully!")
        else:
            self.controller.ui_manager.log_output(f"Tests failed:\n{stderr}")

    def pause_project(self):
        """Pause project generation"""
        if not self.generation_in_progress:
            self.controller.ui_manager.log_output("No active generation to pause.")
            return

        self.controller.ui_manager.log_output("Project generation paused.")
        # Additional logic to actually pause the generation would go here

    def stop_project(self):
        """Stop project generation"""
        if not self.generation_in_progress:
            self.controller.ui_manager.log_output("No active generation to stop.")
            return

        self.controller.ui_manager.log_output("Stopping project generation...")
        self.stop_event.set()

        self.controller.ui_manager.toggle_generation_ui(True)
        self.generation_in_progress = False

        # Stop orchestrator if running
        if hasattr(self.controller, 'ai_orchestrator'):
            self.controller.ai_orchestrator.stop_generation()

    def _save_metrics(self, project_path, new_metrics):
        """Save project metrics to nia_metrics.json"""
        metrics_path = Path(project_path) / "nia_metrics.json"

        current_metrics = {}
        if metrics_path.exists():
            try:
                current_metrics = json.loads(metrics_path.read_text(encoding='utf-8'))
            except:
                pass

        # Deep merge for top level keys
        for key, value in new_metrics.items():
            if key in current_metrics and isinstance(current_metrics[key], dict) and isinstance(value, dict):
                current_metrics[key].update(value)
            else:
                current_metrics[key] = value

        metrics_path.write_text(json.dumps(current_metrics, indent=2), encoding='utf-8')

    def _initialize_project_files(self, project_path, spec_content):
        """Generates automatically essential project files."""
        import sys

        self.controller.safe_ui_call(self.controller.ui_manager.log_output, "Initializing project files...")

        # 1. Detect project type
        project_types = self._detect_project_type(spec_content)

        # 2. Extract dependencies
        dependencies = self._detect_dependencies(project_path, spec_content)

        # 3. Create requirements.txt (Python)
        requirements_path = Path(project_path) / "requirements.txt"
        if 'python' in project_types or dependencies:
            if not dependencies:
                dependencies = ["pytest"]
            requirements_path.write_text("\n".join(sorted(dependencies)) + "\n", encoding='utf-8')
            self._save_metrics(project_path, {"dependencies": {"requirements_generated": True, "auto_detected": dependencies}})

        # 4. Create .gitignore
        self._create_gitignore(project_path, project_types)
        self._save_metrics(project_path, {"dependencies": {"gitignore_generated": True}})

        # 4.5. Create README.md
        readme_path = Path(project_path) / "README.md"
        if not readme_path.exists():
            readme_content = f"# Project\n\nGenerated by nIA Autonomous Loop.\n\n## Specification\n{spec_content}"
            readme_path.write_text(readme_content, encoding='utf-8')

        # 5. Setup venv and install requirements
        setup_script = Path("scripts/setup_project_venv.py")
        if setup_script.exists():
            self.controller.safe_ui_call(self.controller.ui_manager.log_output, "Setting up virtual environment...")
            cmd = [sys.executable, str(setup_script), str(project_path)]
            if dependencies:
                cmd.extend(dependencies)
            subprocess.run(cmd, capture_output=True)

        # Initial Git Commit for these files
        try:
            subprocess.run(["git", "add", "requirements.txt", ".gitignore", "README.md"], cwd=str(project_path), capture_output=True)
            subprocess.run(["git", "commit", "-m", "chore: Initialize project files (requirements, gitignore, README)"], cwd=str(project_path), capture_output=True)
        except:
            pass

    def _detect_project_type(self, spec_content):
        types = []
        content = spec_content.lower()
        if 'python' in content or '.py' in content:
            types.append('python')
        if any(kw in content for kw in ['node', 'npm', 'react', 'vue', 'nextjs']):
            types.append('node')
        if 'html' in content and 'node' not in types:
            types.append('web')
        return types if types else ['web']

    def _detect_dependencies(self, project_path, spec_content):
        deps = set()

        # Phase 1: Scan test files
        for test_file in glob.glob(os.path.join(project_path, "tests", "**", "*.py"), recursive=True):
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Simple regex for imports
                matches = re.findall(r"^(?:from|import)\s+([a-zA-Z0-9_]+)", content, re.MULTILINE)
                for m in matches:
                    if m not in ['os', 'sys', 'time', 're', 'json', 'unittest', 'pytest', 'pathlib', 'logging', 'subprocess', 'threading', 'math', 'random']:
                        deps.add(m)
            except:
                pass

        # Phase 2: Fallback to spec hints
        hints = {
            "beautifulsoup": "beautifulsoup4",
            "bs4": "beautifulsoup4",
            "requests": "requests",
            "pandas": "pandas",
            "flask": "flask",
            "django": "django",
            "fastapi": "fastapi",
            "numpy": "numpy"
        }
        spec_lower = spec_content.lower()
        for hint, pkg in hints.items():
            if hint in spec_lower:
                deps.add(pkg)

        return list(deps)

    def _create_gitignore(self, project_path, project_types):
        templates = {
            'python': ['__pycache__/', '*.py[cod]', '*$py.class', '.venv/', 'venv/', 'env/', '.pytest_cache/', '*.egg-info/', '.env'],
            'node': ['node_modules/', 'npm-debug.log*', 'yarn-debug.log*', 'yarn-error.log*', 'dist/', '.env'],
            'web': ['.DS_Store', 'Thumbs.db', '.env']
        }

        lines = set()
        for pt in project_types:
            if pt in templates:
                lines.update(templates[pt])

        path = os.path.join(project_path, ".gitignore")
        with open(path, 'w', encoding='utf-8') as f:
            for line in sorted(list(lines)):
                f.write(f"{line}\n")

    def _filter_redundant_tasks(self, project_path, plan_path):
        """Marks tasks as completed if they only involve creating files that already exist."""
        from src.core.task_tracker import TaskTracker
        parser = PlanParser()
        tracker = TaskTracker()
        try:
            tasks = parser.parse(plan_path)
        except:
            return False

        modified = False
        for task in tasks:
            if task.status == 'pending':
                desc = task.description.lower()
                if any(kw in desc for kw in ["create", "initialize", "setup", "generar"]):
                    common_files = [".gitignore", "readme.md", "requirements.txt"]
                    files_to_check = [f for f in common_files if f in desc]

                    if files_to_check:
                        all_exist = all((Path(project_path) / f).exists() for f in files_to_check)
                        if all_exist:
                            self.controller.safe_ui_call(self.controller.ui_manager.log_output, f"⏭️ Skipping redundant task: {task.description}")
                            tracker.mark_completed(plan_path, task)
                            modified = True
        return modified

    def _run_nia_autonomous_loop(self, prompt: str, project_path: str):
        """Internal method to orchestrate the full nIA cycle from initial prompt."""
        path = Path(project_path)

        try:
            # 1. Initialize Git
            subprocess.run(["git", "init"], cwd=project_path, capture_output=True, encoding='utf-8', errors='replace')

            # Check for stop before starting phases
            if self.stop_event.is_set():
                return

            # 2. Generate SPEC.md
            self.controller.safe_ui_call(self.controller.ui_manager.log_output, "Phase 1: Generating Specification...")
            spec_gen = SpecGenerator()
            spec_content = spec_gen.generate(prompt)
            if self.stop_event.is_set(): return
            (path / "SPEC.md").write_text(spec_content, encoding='utf-8')
            self.controller.safe_ui_call(self.controller.ui_manager.file_manager.populate_tree_view)

            # 3. Generate IMPLEMENTATION_PLAN.md
            self.controller.safe_ui_call(self.controller.ui_manager.log_output, "Phase 2: Generating Implementation Plan...")
            plan_gen = PlanGenerator()
            plan_content = plan_gen.generate(spec_content)
            if self.stop_event.is_set(): return
            (path / "IMPLEMENTATION_PLAN.md").write_text(plan_content, encoding='utf-8')
            self.controller.safe_ui_call(self.controller.ui_manager.file_manager.populate_tree_view)

            # Phase 2.5: Plan Review & Critique
            self.controller.safe_ui_call(self.controller.ui_manager.log_output, "Phase 2.5: Reviewing & Critiquing Plan...")
            start_time = time.time()
            reviewer = PlanReviewer()
            approved, critique, improved_data, iterations = reviewer.review_and_improve(spec_content, plan_content, prompt)
            duration = time.time() - start_time

            if improved_data:
                plan_content = plan_gen.env.get_template("IMPLEMENTATION_PLAN.md.jinja2").render(**improved_data)
                (path / "IMPLEMENTATION_PLAN.md").write_text(plan_content, encoding='utf-8')
                self.controller.safe_ui_call(self.controller.ui_manager.log_output, f"Plan improved after {iterations} iterations.")

            if not approved:
                self.controller.safe_ui_call(self.controller.ui_manager.log_output, "⚠️ Plan review reached max iterations without full approval. Proceeding with last version.")

            # Save metrics
            self._save_metrics(path, {
                "project_id": os.path.basename(project_path),
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "plan_review": {
                    "iterations": iterations,
                    "approval_time_seconds": duration,
                    "final_approved": approved,
                    "issues_found": [critique] if critique else []
                }
            })

            # Initial plan list update
            parser = PlanParser()
            tasks = parser.parse(path / "IMPLEMENTATION_PLAN.md")
            plan_text = "\n".join([f"[{'x' if t.status == 'completed' else ('?' if t.status == 'blocked' else ' ')}] {t.description}" for t in tasks])
            self.controller.safe_ui_call(self.controller.ui_manager.update_ai_plan, plan_text)

            # 4. Create NIA_PROMPT.md
            self.controller.safe_ui_call(self.controller.ui_manager.log_output, "Phase 3: Setting up nIA Prompt...")
            template_dir = Path("src/templates")
            prompt_template = template_dir / "NIA_PROMPT.md.jinja2"
            if prompt_template.exists():
                (path / "NIA_PROMPT.md").write_text(prompt_template.read_text(encoding='utf-8'), encoding='utf-8')

            # Initial Commit
            subprocess.run(["git", "add", "."], cwd=project_path, capture_output=True, encoding='utf-8', errors='replace')
            subprocess.run(["git", "commit", "-m", "Initial nIA project setup"], cwd=project_path, capture_output=True, encoding='utf-8', errors='replace')

            # 5. Launch nIA Loop
            self.controller.safe_ui_call(self.controller.ui_manager.log_output, "Phase 4: Launching nIA Autonomous Loop...")

            # Initialize project files (requirements.txt, .gitignore, README.md)
            self._initialize_project_files(path, spec_content)

            # Filter redundant tasks (e.g. creating files that already exist)
            self._filter_redundant_tasks(path, path / "IMPLEMENTATION_PLAN.md")

            orchestrator = LoopOrchestrator(path)

            def log_cb(msg: str):
                self.controller.safe_ui_call(self.controller.ui_manager.log_output, msg)
                # If message indicates progress or failure, refresh UI components
                should_refresh = any(indicator in msg for indicator in ["✅", "❌", "Task completed", "Phase", "Target Task"])

                if should_refresh:
                    self.controller.safe_ui_call(self.controller.ui_manager.file_manager.populate_tree_view)

                    # Update AI Plan listbox with current status
                    parser = PlanParser()
                    tasks = parser.parse(path / "IMPLEMENTATION_PLAN.md")
                    if tasks:
                        plan_text = "\n".join([f"[{'x' if t.status == 'completed' else ('?' if t.status == 'blocked' else ' ')}] {t.description}" for t in tasks])
                        self.controller.safe_ui_call(self.controller.ui_manager.update_ai_plan, plan_text)

            result = orchestrator.run(max_iterations=50, log_callback=log_cb, stop_event=self.stop_event)

            # Save execution metrics
            if result.stats:
                self._save_metrics(path, {
                    "execution": {
                        "tasks_planned": result.stats.get("tasks_planned"),
                        "tasks_completed": result.stats.get("tasks_completed"),
                        "total_duration_seconds": result.stats.get("duration_seconds")
                    },
                    "code_quality": {
                        "average_lines_per_task": result.stats.get("average_lines_per_task"),
                        "total_code_lines": result.stats.get("total_code_lines"),
                        "total_test_lines": result.stats.get("total_test_lines")
                    }
                })

            self.controller.safe_ui_call(self.controller.ui_manager.log_output, f"nIA Loop Finished: {result.message}")

        except Exception as e:
            logging.error(f"nIA Loop Error: {e}")
            self.controller.safe_ui_call(self.controller.ui_manager.log_output, f"❌ nIA Loop Error: {e}")
        finally:
            self.generation_in_progress = False
            self.controller.safe_ui_call(self.controller.ui_manager.toggle_generation_ui, True)
