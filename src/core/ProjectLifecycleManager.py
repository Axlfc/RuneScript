import os
import logging
import threading
import uuid
from tkinter import messagebox
from typing import Dict, Any

from src.utils.parser_utils import AIResponseParser
from src.utils.ProjectIO import ProjectIO
from src.utils.test_runner import run_pytest
from src.models.WebProjectGenerator import WebProjectGenerator

class ProjectLifecycleManager:
    """
    Manages project lifecycle including creation, generation, and testing.
    """

    def __init__(self, controller):
        self.controller = controller
        self.generation_in_progress = False

    def generate_project_with_ai(self):
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

        try:
            # Create new project
            project_id = str(uuid.uuid4())
            project_path = os.path.join(self.controller.projects_base_dir, project_id)
            os.makedirs(project_path, exist_ok=True)
            self.controller.current_project = project_path

            # Start AI generation thread
            thread = threading.Thread(
                target=self.controller.ai_orchestrator.threaded_ai_generation,
                args=(prompt)
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

        self.controller.ui_manager.log_output("Project generation stopped.")
        self.controller.ui_manager.toggle_generation_ui(True)
        self.generation_in_progress = False
        # Additional logic to actually stop the generation would go here
