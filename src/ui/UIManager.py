import os
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from src.ui.project_file_manager import ProjectFileManager
from src.ui.ui_components import create_project_tree, create_output_console, create_ai_plan, create_file_editor, \
    create_command_bar


from src.models.tdd_workflow_panel import TDDWorkflowPanel
from src.models.test_result_panel import TestResultPanel
from src.models.tdd_workflow_manager import TDDWorkflowManager
from src.utils.ProjectIO import ProjectIO


class UIManager:
    """
    Manages all UI components and interactions within the IDE.
    """

    def __init__(self, controller):
        self.controller = controller
        self.setup_menu()
        self.create_main_layout()

    def setup_menu(self):
        """Set up the application menu bar"""
        menubar = tk.Menu(self.controller.root)
        self.controller.root.configure(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.controller.safe_new_project)
        file_menu.add_command(label="Open Project", command=self.controller.safe_open_project)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.controller.root.quit)

    def create_main_layout(self):
        """Create the main application layout"""
        try:
            main_container = ttk.PanedWindow(self.controller.root, orient=tk.HORIZONTAL)
            main_container.pack(fill=tk.BOTH, expand=True)

            left_panel = ttk.Frame(main_container)
            self.project_tree = create_project_tree(left_panel, self.on_file_select)
            self.output_console = create_output_console(left_panel)
            main_container.add(left_panel)

            right_panel = ttk.PanedWindow(main_container, orient=tk.VERTICAL)
            self.ai_plan_listbox = create_ai_plan(right_panel)
            self.file_editor = create_file_editor(right_panel, self.on_file_modified)
            main_container.add(right_panel)

            # Initialize file manager
            self.file_manager = ProjectFileManager(
                tree_widget=self.project_tree,
                file_editor=self.file_editor,
                log_fn=self.log_output
            )

            # Create command bar
            self.prompt_entry, self.generate_btn, self.pause_btn, self.stop_btn = create_command_bar(
                self.controller.root,
                on_generate=self.controller.project_manager.generate_project_with_ai,
                on_pause=self.controller.project_manager.pause_project,
                on_stop=self.controller.project_manager.stop_project
            )

            # ✅ Add TDD Test Result Panel
            self.test_result_panel = TestResultPanel(right_panel)
            self.test_result_panel.pack(fill=tk.BOTH, expand=False)

            # ✅ Add TDD Workflow Manager
            project_io = ProjectIO(log_function=self.log_output)
            self.tdd_manager = TDDWorkflowManager(project_io, self)

            # ✅ Add TDD Workflow Panel
            self.tdd_panel = TDDWorkflowPanel(
                right_panel,
                on_run_tests=self.tdd_manager.run_tests,
                on_refactor=self.tdd_manager.refactor_code,
                on_write_test=self.tdd_manager.write_test,
                on_rerun_last=self.tdd_manager.rerun_last_test
            )
            self.tdd_panel.pack(fill=tk.X)

        except Exception as e:
            self.controller.safe_ui_call(
                messagebox.showerror,
                "Layout Initialization Error",
                str(e)
            )
            logging.critical(f"Layout creation failed: {e}")

    def update_phase_ui(self, phase_name: str, test_status: Optional[str] = None) -> None:
        """
        Update the visual indicator and button state for the current TDD phase.

        Args:
            phase_name (str): The current phase name (e.g., "Write Test", "Run Test").
            test_status (Optional[str]): The result of the last test run, e.g. "passed" or "failed".
        """
        if hasattr(self, 'tdd_panel'):
            self.tdd_panel.update_phase(phase_name, test_status)

    def update_test_results(self, passed: bool, stdout: str, stderr: str) -> None:
        if hasattr(self, 'test_result_panel'):
            self.test_result_panel.update_test_results(passed, stdout, stderr)

    def show_message(self, title: str, message: str) -> None:
        """
        Show a popup information message box to the user.

        Args:
            title (str): The title of the message box.
            message (str): The message to be displayed.
        """
        messagebox.showinfo(title, message)

    def focus_test_editor(self) -> None:
        """
        Bring focus to the most recent test file.
        """
        # In a real system, you'd pull this from state, for now, fallback to convention
        possible_test_files = [f for f in self.file_manager.current_project_files.values() if 'test' in f.lower()]
        if possible_test_files:
            relative = os.path.relpath(possible_test_files[0], self.file_manager.current_project)
            self.file_manager.open_file(relative)
        else:
            self.log_output("No test file found to focus on.")

    def focus_implementation_editor(self) -> None:
        """
        Bring focus to a recently edited implementation file.
        """
        # Naive: just find any .py file that isn't in /tests/
        impl_files = [f for f in self.file_manager.current_project_files.values()
                      if f.endswith('.py') and 'test' not in f.lower()]
        if impl_files:
            relative = os.path.relpath(impl_files[0], self.file_manager.current_project)
            self.file_manager.open_file(relative)
        else:
            self.log_output("No implementation file found to focus on.")

    def on_file_select(self, event):
        """Handle file selection in project tree"""
        self.file_manager.on_file_select(event)

    def on_file_modified(self, event=None):
        """Handle file content modifications"""
        self.file_manager.on_file_modified(event)

    def update_ai_plan(self, plan_text: str):
        """Update the AI plan listbox with new content"""
        self.ai_plan_listbox.delete(0, tk.END)
        steps = plan_text.split('\n')
        for step in steps:
            if step.strip():
                self.ai_plan_listbox.insert(tk.END, step)

    def log_output(self, message: str):
        """Log message to output console"""
        self.output_console.configure(state='normal')
        self.output_console.insert(tk.END, message + "\n")
        self.output_console.see(tk.END)
        self.output_console.configure(state='disabled')
        logging.info(message)

    def toggle_generation_ui(self, enabled: bool):
        """Toggle UI components based on generation state"""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.prompt_entry.configure(state=state)
        self.generate_btn.configure(state=state)

        # Pause and stop buttons are enabled during generation and disabled otherwise
        pause_stop_state = tk.NORMAL if not enabled else tk.DISABLED
        self.pause_btn.configure(state=pause_stop_state)
        self.stop_btn.configure(state=pause_stop_state)
