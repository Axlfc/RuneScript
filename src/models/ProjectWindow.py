import os
import logging
import subprocess
import queue
import tkinter as tk
import uuid
from tkinter import ttk, messagebox, filedialog, scrolledtext
from typing import Dict, Optional, Any, Callable

from src.agents.AutonomousProjectAgent import AutonomousProjectAgent
from src.core.project_context import ProjectContext, generate_readme, transition_to_next_phase
from src.utils.parser_utils import AIResponseParser
from src.utils.project_io import ProjectIO
from src.core.ai_runner import run_ai_prompt


from src.ui.project_file_manager import ProjectFileManager
from src.ui.ui_components import (
    create_project_tree,
    create_output_console,
    create_ai_plan,
    create_file_editor,
    create_command_bar
)
from src.utils.test_runner import run_pytest


class RedGreenRefactorIDE:
    def __init__(self, root=None):
        self.root = root or tk.Tk()
        self.root.title("Red-Green-Refactor IDE")
        self.root.geometry("1400x900")

        self.ai_task_queue = queue.Queue()
        self.ai_response_queue = queue.Queue()
        self.setup_menu()
        self.create_main_layout()
        self.poll_queue()  # Start polling the queue
        self.projects_base_dir = os.path.join('data', 'projects')
        self.current_project_files = {}
        os.makedirs(self.projects_base_dir, exist_ok=True)

        self.current_project = None
        self.project_tree = None

        self.setup_logging()
        self.setup_ui()

    @property
    def current_project(self):
        return self._current_project

    @current_project.setter
    def current_project(self, value):
        self._current_project = value

        # Sync into file manager
        if hasattr(self, "file_manager") and self.file_manager:
            self.file_manager.project_path = value

        # Log assignment
        if value:
            logging.info(f"Current project set to: {value}")
        else:
            logging.info("Current project cleared.")

    def safe_ui_call(self, func: Callable, *args, **kwargs):
        if self.root and self.root.winfo_exists():
            try:
                self.root.after(0, lambda: func(*args, **kwargs))
            except RuntimeError as e:
                logging.warning(f"safe_ui_call failed: {e}")
        else:
            logging.warning("safe_ui_call skipped: root window no longer exists.")

    def handle_state_event(self, event_type, data):
        if not self.current_project:
            logging.info("No project loaded.")
            return
        if event_type == "file_created":
            self.file_manager.populate_tree_view()

    def setup_ui(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.new_project)
        file_menu.add_command(label="Open Project", command=self.open_project)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True)

        left_panel = ttk.Frame(main_container)
        self.project_tree = ttk.Treeview(left_panel, columns=('path',), show='tree')
        self.project_tree.pack(fill=tk.BOTH, expand=True)
        main_container.add(left_panel)

        right_panel = ttk.Frame(main_container)
        self.output_console = scrolledtext.ScrolledText(right_panel, wrap=tk.WORD, state='disabled', height=20)
        self.output_console.pack(fill=tk.BOTH, expand=True)
        main_container.add(right_panel)

    def poll_queue(self):
        try:
            while not self.ai_response_queue.empty():
                status, data = self.ai_response_queue.get_nowait()
                if status == "success":
                    self.root.after(0, lambda d=data: self.finalize_project_generation(d))
                elif status == "error":
                    self.root.after(0, lambda msg=data: self.handle_generation_failure(error_message=msg))
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.poll_queue)

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Existing menu setup with additional error handling
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.safe_new_project)
        file_menu.add_command(label="Open Project", command=self.safe_open_project)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

    def safe_new_project(self):
        try:
            self.new_project()
        except Exception as e:
            messagebox.showerror("Project Creation Error", str(e))
            logging.error(f"Project creation failed: {e}")

    def safe_open_project(self):
        try:
            self.open_project()
        except Exception as e:
            messagebox.showerror("Project Open Error", str(e))
            logging.error(f"Project open failed: {e}")

    def create_main_layout(self):
        try:
            main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
            main_container.pack(fill=tk.BOTH, expand=True)

            left_panel = ttk.Frame(main_container)
            self.project_tree = create_project_tree(left_panel, self.on_file_select)
            self.output_console = create_output_console(left_panel)
            main_container.add(left_panel)

            right_panel = ttk.PanedWindow(main_container, orient=tk.VERTICAL)
            self.ai_plan_listbox = create_ai_plan(right_panel)
            self.file_editor = create_file_editor(right_panel, self.on_file_modified)
            main_container.add(right_panel)

            # ✅ safe to initialize file_manager now
            self.file_manager = ProjectFileManager(
                tree_widget=self.project_tree,
                file_editor=self.file_editor,
                log_fn=self.log_output
            )

            self.prompt_entry, self.generate_btn, self.pause_btn, self.stop_btn = create_command_bar(
                self.root,
                on_generate=self.generate_project_with_ai,
                on_pause=self.pause_project,
                on_stop=self.stop_project
            )

        except Exception as e:
            messagebox.showerror("Layout Initialization Error", str(e))
            logging.critical(f"Layout creation failed: {e}")

    def create_left_panel(self, parent):
        left_panel = ttk.Frame(parent)
        self.project_tree = create_project_tree(left_panel)
        self.output_console = create_output_console(left_panel)
        return left_panel

    def create_right_panel(self, parent):
        right_panel = ttk.PanedWindow(parent, orient=tk.VERTICAL)
        self.ai_plan_listbox = create_ai_plan(right_panel)
        self.file_editor = create_file_editor(right_panel)
        return right_panel

    def process_prompt_with_ai(self, combined_input: str) -> Optional[str]:
        try:
            ai_script_path = "src/models/ai_assistant.py"
            result = run_ai_prompt(ai_script_path, combined_input)
            return result
        except Exception as e:
            self.safe_ui_call(self.log_output, f"Failed to communicate with AI: {e}")
            return None

    def new_project(self):
        project_id = str(uuid.uuid4())
        project_path = os.path.join(self.projects_base_dir, project_id)
        os.makedirs(project_path, exist_ok=True)
        self.safe_ui_call(lambda: setattr(self, 'current_project', project_path))
        self.safe_ui_call(self.log_output, f"New project created: {project_path}")

    def open_project(self):
        project_path = filedialog.askdirectory(initialdir=self.projects_base_dir)
        if project_path:
            self.safe_ui_call(lambda: setattr(self, 'current_project', project_path))
            self.safe_ui_call(self.log_output, f"Opened project: {project_path}")

            self.file_manager.populate_tree_view()

    def run_project_generation(self, metadata: Dict[str, Any]):
        """
        Run project generation and ensure tasks are processed.
        """
        if not self.current_project:
            self.safe_ui_call(self.log_output, "No project selected. Create or open a project first.")

            return

        self.safe_ui_call(self.log_output, "Starting project generation...")

        # Initialize project context
        context = ProjectContext(
            project_name=metadata.get("project_name", "Unnamed Project"),
            description=metadata.get("project_description", "No description provided."),
            path=self.current_project
        )

        # Update milestones and tasks
        context.milestones.extend(metadata.get("milestones", []))
        context.tasks.extend(metadata.get("tasks", []))

        # Generate project structure
        ProjectIO.create_structure(self.current_project, metadata, self.log_output)

        # Write TODO.md
        ProjectIO.write_todo(self.current_project, context.tasks, self.log_output)

        # Generate documentation
        generate_readme(context)

        # Run tests
        if ProjectIO.run_tests(self.current_project, self.log_output):
            context.complete_task("Run all tests")
            self.safe_ui_call(self.log_output, "All tests passed successfully!")

        # Update project phase
        transition_to_next_phase(context)

        if context.current_phase == "Ready for Review":
            self.safe_ui_call(self.log_output, "Project development is complete and ready for review.")

        else:
            # Continue autonomous workflow
            self.continue_autonomous_workflow(metadata)

    def continue_autonomous_workflow(self, metadata: Dict[str, Any]):
        """
        Continue the workflow based on AI feedback and project state.
        """
        if not metadata.get("next_steps"):
            self.safe_ui_call(self.log_output, "Project development is complete.")

            return

        self.safe_ui_call(self.log_output, "Requesting additional steps from AI...")

        ai_agent = AutonomousProjectAgent(self.current_project)
        ai_agent.state.register_observer(self.handle_state_event)

        ai_feedback = ai_agent.process_prompt_with_ai("next_steps", {"current_state": metadata})

        if ai_feedback:
            parsed_metadata = AIResponseParser.parse_ai_response(ai_feedback)
            self.run_project_generation(parsed_metadata)
        else:
            self.safe_ui_call(self.log_output, "No further steps provided by AI.")

    def generate_project_with_ai(self):
        """
        Start autonomous project generation with AI.
        """
        raw_prompt = self.prompt_entry.get()
        prompt = AIResponseParser.sanitize_prompt(raw_prompt)

        if not AIResponseParser.validate_prompt(prompt):
            messagebox.showwarning("Invalid Prompt", "Please provide a clear, meaningful project description.")
            return

        self.safe_ui_call(self.log_output, "Starting AI-based autonomous project generation...")
        self.toggle_generation_ui(False)

        try:
            # ✅ Create and assign project path before using it
            project_id = str(uuid.uuid4())
            project_path = os.path.join(self.projects_base_dir, project_id)
            os.makedirs(project_path, exist_ok=True)
            self.current_project = project_path  # Set BEFORE using it

            # ✅ Safe to initialize agent now
            self.ai_agent = AutonomousProjectAgent(self.current_project, ide_instance=self)
            self.ai_agent.state.register_observer(self.handle_state_event)

            # Initial prompt to bootstrap structure/files
            init_context = {
                "prompt": prompt,
                "format": "Return JSON with 'initial_files', 'project_tasks', and 'project_structure'"
            }
            initial_response = self.ai_agent.process_prompt_with_ai("initial_project_setup", init_context)
            initial_metadata = AIResponseParser.parse_ai_response(initial_response)

            if initial_metadata and "initial_files" in initial_metadata:
                initial_files = initial_metadata.get("initial_files", {})

                if isinstance(initial_files, dict):
                    for filename, content in initial_files.items():
                        self.ai_agent.state.add_code_file(filename, content)
                elif isinstance(initial_files, list):
                    for file_entry in initial_files:
                        if isinstance(file_entry, dict):
                            filename = file_entry.get("filename")
                            content = file_entry.get("content", "# Placeholder content\n")
                        else:
                            filename = str(file_entry)
                            content = "# Placeholder content\n"
                        if filename:
                            self.ai_agent.state.add_code_file(filename, content)

            if initial_metadata and "project_structure" in initial_metadata:
                ProjectIO.create_structure(self.ai_agent.project_path, initial_metadata, print)

            self.file_manager.populate_tree_view()
            self.ai_agent.start_autonomous_development(prompt)

            self.safe_ui_call(self.log_output, "Autonomous agent has been launched.")
            self.file_manager.populate_tree_view()

            self.update_ai_plan('\n'.join([
                "Analyzing requirements",
                "Designing architecture",
                "Generating tests",
                "Implementing features",
                "Refactoring code",
                "Validating project"
            ]))

        except Exception as e:
            logging.error(f"Project generation failed: {e}")
            self.safe_ui_call(self.handle_generation_failure, f"Project generation failed: {e}")
            self.toggle_generation_ui(True)

    def threaded_ai_generation(self, prompt):
        """
        Run AI generation logic in a separate thread and enqueue results.
        """
        try:
            ai_response = self.process_prompt_with_ai(prompt)
            if ai_response:
                parsed_metadata = AIResponseParser.parse_ai_response(ai_response)
                self.ai_response_queue.put(("success", parsed_metadata))
            else:
                self.ai_response_queue.put(("error", "AI response is empty."))
        except Exception as e:
            logging.error(f"AI generation thread error: {e}")
            self.ai_response_queue.put(("error", str(e)))

    def finalize_project_generation(self, parsed_metadata):
        """
        Finalize the project generation with enhanced documentation and structure.

        :param parsed_metadata: Metadata returned by AI project generation
        """
        try:
            # Generate a sanitized project ID
            project_id = str(uuid.uuid4()).replace("-", "")
            project_path = os.path.normpath(os.path.join(self.projects_base_dir, project_id))

            # Create the project structure
            ProjectIO.create_structure(project_path, parsed_metadata)

            # Generate comprehensive project documentation
            self._generate_project_docs(project_path, parsed_metadata)

            # Set the current project and refresh the UI
            self.safe_ui_call(lambda: setattr(self, 'current_project', project_path))
            self.safe_ui_call(self.populate_project_tree)

            # Format project structure and tasks for AI Plan
            project_structure = parsed_metadata.get('project_structure', [])
            project_tasks = parsed_metadata.get('project_tasks', [])

            # Update AI Plan with tasks
            formatted_tasks = '\n'.join(project_tasks)
            self.safe_ui_call(self.update_ai_plan, formatted_tasks)

            self.safe_ui_call(self.log_output, f"Project {project_id} generated successfully at {project_path}!")


        except Exception as e:
            logging.error(f"Project finalization error: {e}")
            messagebox.showerror("Generation Error", str(e))
        finally:
            self.ai_response_queue.put(("completed", "Project done"))

    def _generate_project_docs(self, project_path, parsed_metadata):
        """
        Generate comprehensive project documentation.

        :param project_path: Path to the project directory
        :param parsed_metadata: Metadata returned by AI project generation
        """
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

    def handle_generation_failure(self, error_message="AI generation failed. Please try again."):
        """
        Handle AI generation failure and update UI.
        """
        messagebox.showerror("AI Generation Failed", error_message)
        self.toggle_generation_ui(True)

    def toggle_generation_ui(self, enabled: bool):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.prompt_entry.config(state=state)
        self.generate_btn.config(state=state)
        self.pause_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)

    def populate_project_tree(self):
        self.file_manager.populate_tree_view()

    def on_file_select(self, event):
        self.file_manager.on_file_select(event)

    def on_file_modified(self, event=None):
        self.file_manager.on_file_modified(event)

    def update_ai_plan(self, plan_text: str):
        self.ai_plan_listbox.delete(0, tk.END)
        steps = plan_text.split('\n')
        for step in steps:
            if step.strip():
                self.ai_plan_listbox.insert(tk.END, step)

    def run_tests(self):
        success, stdout, stderr = run_pytest(self.current_project)

        self.safe_ui_call(self.log_output, stdout)

        if success:
            self.safe_ui_call(self.log_output, "Tests passed successfully!")
        else:
            self.safe_ui_call(self.log_output, f"Tests failed:\n{stderr}")

    def log_output(self, message: str):
        self.output_console.config(state='normal')
        self.output_console.insert(tk.END, message + "\n")
        self.output_console.see(tk.END)
        self.output_console.config(state='disabled')
        logging.info(message)

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s',
            handlers=[logging.FileHandler('project.log'), logging.StreamHandler()]
        )

    def show_about(self):
        messagebox.showinfo(
            "About Red-Green-Refactor IDE",
            "A comprehensive development environment for Test-Driven Development."
        )

    def pause_project(self):
        self.safe_ui_call(self.log_output, "Project generation paused.")

    def stop_project(self):
        self.safe_ui_call(self.log_output, "Project generation stopped.")

        self.prompt_entry.config(state=tk.NORMAL)
        self.generate_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)


if __name__ == '__main__':
    root = tk.Tk()
    app = RedGreenRefactorIDE(root)
    root.mainloop()
