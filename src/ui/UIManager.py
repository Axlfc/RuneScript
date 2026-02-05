import os
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List
from pathlib import Path

from src.ui.project_file_manager import ProjectFileManager
from src.ui.ui_components import (
    create_project_tree,
    create_output_console,
    create_ai_plan,
    create_file_editor,
    create_command_bar
)
from src.ui.rich_components import (
    FileTreeView,
    TDDPhaseIndicator,
    TestResultsPanel,
    InlineDiffViewer,
    AccessibilityManager,
    AIPlanVisualizer
)

from src.models.tdd_workflow_panel import TDDWorkflowPanel
from src.models.test_result_panel import TestResultPanel
from src.models.tdd_workflow_manager import TDDWorkflowManager
from src.utils.ProjectIO import ProjectIO
from src.core.plan_parser import PlanParser, Task


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
            # Create command bar FIRST at the top
            self.prompt_entry, self.generate_btn, self.nia_btn, self.pause_btn, self.stop_btn = create_command_bar(
                self.controller.root,
                on_generate=self.controller.project_manager.generate_project_with_ai,
                on_pause=self.controller.project_manager.pause_project,
                on_stop=self.on_stop_button_click
            )

            main_container = ttk.PanedWindow(self.controller.root, orient=tk.HORIZONTAL)
            main_container.pack(fill=tk.BOTH, expand=True)

            # Left Panel: File Tree and Console
            left_panel = ttk.PanedWindow(main_container, orient=tk.VERTICAL)

            project_path = self.controller.current_project or os.getcwd()
            self.file_tree_view = FileTreeView(
                left_panel,
                project_path,
                on_file_open_callback=self._handle_file_open,
                on_file_modified_callback=self._handle_file_modified
            )
            self.project_tree = self.file_tree_view.tree # For backward compatibility
            left_panel.add(self.file_tree_view, weight=3)

            self.output_console = create_output_console(left_panel)
            left_panel.add(self.output_console, weight=1)

            main_container.add(left_panel, weight=1)

            # Right Panel: Phase Indicator, Plan, Editor, Results, Diff
            right_panel = ttk.PanedWindow(main_container, orient=tk.VERTICAL)

            # 1. Phase Indicator
            self.phase_indicator = TDDPhaseIndicator(right_panel)
            right_panel.add(self.phase_indicator, weight=0)

            # 2. AI Plan (Visualizer + Listbox for backup/details)
            self.ai_plan_listbox, plan_frame = create_ai_plan(right_panel)
            # Adjust listbox to not expand too much
            self.ai_plan_listbox.pack_configure(expand=False, fill=tk.X)

            self.ai_plan_visualizer = AIPlanVisualizer(plan_frame)
            # Put visualizer at the top of the plan_frame and make it expand
            self.ai_plan_visualizer.pack(fill=tk.BOTH, expand=True, before=self.ai_plan_listbox)
            right_panel.add(plan_frame, weight=1)

            # 3. File Editor
            self.file_editor, file_editor_frame = create_file_editor(right_panel, self.on_file_modified)
            right_panel.add(file_editor_frame, weight=3)

            # 4. Test Results Panel
            self.test_results = TestResultsPanel(right_panel)
            right_panel.add(self.test_results, weight=1)

            # 5. Git Diff Viewer
            self.diff_viewer = InlineDiffViewer(right_panel)
            right_panel.add(self.diff_viewer, weight=1)

            main_container.add(right_panel, weight=2)

            # Initialize file manager
            self.file_manager = ProjectFileManager(
                tree_widget=self.project_tree,
                file_editor=self.file_editor,
                log_fn=self.log_output
            )

            # Initialize Accessibility Manager
            self.accessibility = AccessibilityManager(self.controller.root, self)


            # ✅ Add TDD Test Result Panel (Legacy, kept for compatibility if needed, but we have rich results now)
            # self.test_result_panel = TestResultPanel(right_panel)
            # right_panel.add(self.test_result_panel, weight=1)

            # ✅ Add TDD Workflow Manager
            project_io = ProjectIO(log_function=self.log_output)
            self.tdd_manager = TDDWorkflowManager(project_io, self)

            # ✅ Add TDD Workflow Panel (Legacy buttons, maybe we can integrate them better later)
            self.tdd_panel = TDDWorkflowPanel(
                self.controller.root, # Put it somewhere else?
                on_run_tests=self.tdd_manager.run_tests,
                on_refactor=self.tdd_manager.refactor_code,
                on_write_test=self.tdd_manager.write_test,
                on_rerun_last=self.tdd_manager.rerun_last_test
            )
            self.tdd_panel.pack(side=tk.BOTTOM, fill=tk.X)

        except Exception as e:
            self.controller.safe_ui_call(
                messagebox.showerror,
                "Layout Initialization Error",
                str(e)
            )
            logging.critical(f"Layout creation failed: {e}")

    def on_stop_button_click(self):
        """Handle stop button click."""
        self.log_output("Stop button clicked...")
        if self.controller.project_manager:
            self.controller.project_manager.stop_project()

    def update_phase_ui(self, phase_name: str, test_status: Optional[str] = None) -> None:
        """
        Update the visual indicator and button state for the current TDD phase.
        """
        if hasattr(self, 'tdd_panel'):
            self.tdd_panel.update_phase(phase_name, test_status)

        # Also update the new rich phase indicator
        if hasattr(self, 'phase_indicator'):
            internal_phase = UI_TO_INTERNAL_PHASE.get(phase_name, 'IDLE')
            self.phase_indicator.set_phase(internal_phase)

    def update_test_results(self, passed: bool, stdout: str, stderr: str) -> None:
        # Legacy
        if hasattr(self, 'test_result_panel'):
            self.test_result_panel.update_test_results(passed, stdout, stderr)

        # Rich
        if hasattr(self, 'test_results'):
            # Clear and stream everything if it's a bulk update
            self.test_results.clear()
            if stdout:
                for line in stdout.splitlines():
                    self.test_results.stream_output(line, 'stdout')
            if stderr:
                for line in stderr.splitlines():
                    self.test_results.stream_output(line, 'stderr')

    def show_message(self, title: str, message: str) -> None:
        messagebox.showinfo(title, message)

    def focus_test_editor(self) -> None:
        possible_test_files = [f for f in self.file_manager.current_project_files.values() if 'test' in f.lower()]
        if possible_test_files:
            relative = os.path.relpath(possible_test_files[0], self.file_manager.current_project)
            self.file_manager.open_file(relative)

    def focus_implementation_editor(self) -> None:
        impl_files = [f for f in self.file_manager.current_project_files.values()
                      if f.endswith('.py') and 'test' not in f.lower()]
        if impl_files:
            relative = os.path.relpath(impl_files[0], self.file_manager.current_project)
            self.file_manager.open_file(relative)

    def on_file_select(self, event):
        self.file_manager.on_file_select(event)

    def on_file_modified(self, event=None):
        self.file_manager.on_file_modified(event)

    def _handle_file_open(self, filepath):
        if self.controller.current_project:
            try:
                rel_path = os.path.relpath(filepath, self.controller.current_project)
                self.file_manager.open_file(rel_path)
            except ValueError:
                # File might be outside project (e.g. during rename/move)
                pass

    def _handle_file_modified(self, filepath):
        # Reload if it's the current file
        if self.file_manager.current_file_path and os.path.abspath(filepath) == os.path.abspath(self.file_manager.current_file_path):
            self.log_output(f"File modified on disk, reloading: {os.path.basename(filepath)}")
            self._handle_file_open(filepath)

    def update_ai_plan(self, plan_text: str, tasks: Optional[List[Task]] = None):
        if tasks:
            self.ai_plan_visualizer.update_plan(tasks)
            return

        # Fallback: Parse from text or file
        if self.controller.current_project:
            plan_path = Path(self.controller.current_project) / 'IMPLEMENTATION_PLAN.md'
            if plan_path.exists():
                parser = PlanParser()
                tasks = parser.parse(plan_path)
                self.ai_plan_visualizer.update_plan(tasks)

    def log_output(self, message: str):
        self.output_console.configure(state='normal')
        self.output_console.insert(tk.END, message + "\n")
        self.output_console.see(tk.END)
        self.output_console.configure(state='disabled')
        logging.info(message)

    def handle_action(self, action: str):
        """Handle actions from keyboard shortcuts."""
        if action == 'run_red_phase':
            self.log_output("Triggering RED phase...")
            if hasattr(self, 'tdd_manager'): self.tdd_manager.write_test()
        elif action == 'run_green_phase':
            self.log_output("Triggering GREEN phase...")
            if hasattr(self, 'tdd_manager'): self.tdd_manager.run_tests()
        elif action == 'run_refactor_phase':
            self.log_output("Triggering REFACTOR phase...")
            if hasattr(self, 'tdd_manager'): self.tdd_manager.refactor_code()
        elif action == 'focus_file_tree':
            self.file_tree_view.tree.focus_set()
        elif action == 'focus_test_results':
            self.test_results.text.focus_set()
        elif action == 'focus_console':
            self.output_console.focus_set()

    def toggle_generation_ui(self, enabled: bool):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.prompt_entry.configure(state=state)
        self.generate_btn.configure(state=state)
        self.nia_btn.configure(state=state)
        pause_stop_state = tk.NORMAL if not enabled else tk.DISABLED
        self.pause_btn.configure(state=pause_stop_state)
        self.stop_btn.configure(state=pause_stop_state)

# To avoid NameError in update_phase_ui
UI_TO_INTERNAL_PHASE = {
    "Write Test": "RED",
    "Run Test": "GREEN",
    "Implement": "GREEN",
    "Refactor": "REFACTOR",
    "Idle": "IDLE"
}
