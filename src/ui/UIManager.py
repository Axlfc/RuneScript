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

from src.ui.styles.theme import IDEStyle
from src.ui.components.top_bar import TopBar
from src.ui.components.sidebar import Sidebar
from src.ui.components.tdd_visualizer import TDDVisualizer
from src.ui.components.code_preview import CodePreview
from src.ui.components.right_panel import RightPanel
from src.ui.components.console import TabbedConsole
from src.ui.components.issue_manager_overlay import IssueManagerOverlay
from src.utils.event_system import EventSystem, Events

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
        self.event_system = EventSystem.get_instance()

        # Apply ttkbootstrap styles
        self.style = IDEStyle.apply_styles(self.controller.root)

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
        """Create the main application layout with the new 20/60/20 structure"""
        try:
            # 1. Top Bar
            self.top_bar = TopBar(
                self.controller.root,
                on_generate=self.controller.project_manager.generate_project_with_ai,
                on_pause=self.controller.project_manager.pause_project,
                on_stop=self.on_stop_button_click
            )
            self.top_bar.pack(side=tk.TOP, fill=tk.X)

            # Legacy pointers for compatibility
            self.prompt_entry = self.top_bar.prompt_entry
            self.generate_btn = self.top_bar.gen_btn
            self.nia_btn = self.top_bar.nia_btn
            self.pause_btn = self.top_bar.pause_btn
            self.stop_btn = self.top_bar.stop_btn

            # 2. Outer PanedWindow (Vertical) to separate Workspace and Console
            self.outer_paned = ttk.PanedWindow(self.controller.root, orient=tk.VERTICAL)
            self.outer_paned.pack(fill=tk.BOTH, expand=True)

            # 3. Main Workspace PanedWindow (Horizontal)
            self.workspace_paned = ttk.PanedWindow(self.outer_paned, orient=tk.HORIZONTAL)
            self.outer_paned.add(self.workspace_paned, weight=5)

            # --- LEFT PANEL (20%) ---
            project_path = self.controller.current_project or os.getcwd()
            self.sidebar = Sidebar(
                self.workspace_paned,
                project_path,
                on_file_open=self._handle_file_open,
                on_file_modified=self._handle_file_modified
            )
            self.workspace_paned.add(self.sidebar, weight=1)

            # Legacy pointers
            self.left_panel = self.sidebar
            self.file_tree_view = self.sidebar.file_tree
            self.project_tree = self.sidebar.file_tree.tree
            self.project_tree.bind('<<TreeviewSelect>>', self.on_file_select)

            # --- CENTER PANEL (60%) ---
            self.center_container = ttk.Frame(self.workspace_paned)
            self.workspace_paned.add(self.center_container, weight=3)

            self.center_panel = ttk.PanedWindow(self.center_container, orient=tk.VERTICAL)
            self.center_panel.pack(fill=tk.BOTH, expand=True)

            # Phase Indicator
            self.phase_indicator = TDDVisualizer(self.center_panel)
            self.center_panel.add(self.phase_indicator, weight=0)

            # File Editor (Code Preview)
            self.code_preview = CodePreview(self.center_panel)
            self.center_panel.add(self.code_preview, weight=3)

            # Legacy pointers for compatibility
            # We take the first text widget for now or implement a proxy
            self.file_editor = None # Will be set on file open

            # Test Results Panel
            self.test_results = TestResultsPanel(self.center_panel)
            self.center_panel.add(self.test_results, weight=1)
            # Legacy pointer
            self.test_result_panel = self.test_results

            # Issue Manager Overlay (hidden by default)
            self.issue_overlay = IssueManagerOverlay(self.center_container)

            # --- RIGHT PANEL (20%) ---
            self.right_panel = RightPanel(self.workspace_paned)
            self.workspace_paned.add(self.right_panel, weight=1)

            # AI Plan (Visualizer + Listbox) in Right Panel
            self.ai_plan_listbox, plan_frame = create_ai_plan(self.right_panel.container)
            self.ai_plan_listbox.pack_configure(expand=False, fill=tk.X)
            self.ai_plan_visualizer = AIPlanVisualizer(plan_frame)
            self.ai_plan_visualizer.pack(fill=tk.BOTH, expand=True, before=self.ai_plan_listbox)
            plan_frame.pack(fill=tk.BOTH, expand=True, pady=5)

            # Git Diff Viewer in Right Panel
            self.diff_viewer = InlineDiffViewer(self.right_panel.container)
            self.diff_viewer.pack(fill=tk.BOTH, expand=True, pady=5)

            # --- BOTTOM CONSOLE ---
            self.console_frame = ttk.Frame(self.outer_paned)
            self.outer_paned.add(self.console_frame, weight=1)

            self.tabbed_console = TabbedConsole(self.console_frame)
            self.tabbed_console.pack(fill=tk.BOTH, expand=True)
            # Legacy pointer
            self.output_console = self.tabbed_console.log_widgets['All Logs']

            # Setup collapsible toggles
            self._setup_toggles()

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

    def _setup_toggles(self):
        """Sets up the event listeners for toggling panels."""
        self.event_system.subscribe(Events.TOGGLE_CONSOLE, self.toggle_console)
        self.event_system.subscribe(Events.OPEN_ISSUE_MANAGER, self.open_issue_manager)
        self.event_system.subscribe(Events.APPLY_FIX, self.apply_issue_fix)
        self.event_system.subscribe(Events.TOGGLE_RIGHT_PANEL, self.toggle_right_panel)
        self.event_system.subscribe(Events.TOGGLE_LEFT_PANEL, self.toggle_left_panel)

        # Add collapse/expand buttons to Top Bar if we want,
        # but for now let's just use shortcuts or internal logic
        self.controller.root.bind("<Control-b>", lambda e: self.toggle_left_panel())
        self.controller.root.bind("<Control-j>", lambda e: self.toggle_console())
        self.controller.root.bind("<Control-l>", lambda e: self.toggle_right_panel())

    def toggle_left_panel(self):
        """Toggles the sidebar visibility."""
        if self.left_panel.winfo_viewable():
            self.workspace_paned.forget(self.left_panel)
        else:
            self.workspace_paned.insert(0, self.left_panel, weight=1)

    def toggle_right_panel(self):
        """Toggles the right panel visibility."""
        if self.right_panel.winfo_viewable():
            self.workspace_paned.forget(self.right_panel)
        else:
            self.workspace_paned.add(self.right_panel, weight=1)

    def toggle_console(self):
        """Toggles the bottom console visibility."""
        if self.console_frame.winfo_viewable():
            self.outer_paned.forget(self.console_frame)
        else:
            self.outer_paned.add(self.console_frame, weight=1)

    def open_issue_manager(self, data=None):
        """Opens the full-screen Issue Manager overlay."""
        if hasattr(self, 'issue_overlay'):
            self.issue_overlay.show(data)

    def apply_issue_fix(self, data):
        """Applies a suggested fix to the code."""
        issue_id = data.get('issue_id')
        suggestion = data.get('suggestion')

        self.log_output(f"Applying fix for Issue #{issue_id}: {suggestion}")

        # Realistic fix application:
        # If suggestion contains code, try to apply it to current editor
        if "```" in suggestion:
            import re
            code_blocks = re.findall(r'```(?:\w+)?\n(.*?)\n```', suggestion, re.DOTALL)
            if code_blocks:
                new_code = code_blocks[0]
                self.log_output(f"Extracted code block for fix.")
                # We could apply it to the active editor
                # self.code_preview.apply_fix_to_current(new_code)

        messagebox.showinfo("Auto-Fix", f"Applying suggested fix for Issue #{issue_id}:\n\n{suggestion}")

        # Bridge to IssueManager to resolve it
        try:
            # We need to find the IssueManager instance.
            # It might be in ProjectLifecycleManager or LoopOrchestrator
            mgr = None
            if hasattr(self.controller.project_manager, 'orchestrator'):
                mgr = self.controller.project_manager.orchestrator.issue_manager

            if mgr:
                mgr.resolve_issue(issue_id, resolution=f"Auto-fixed via UI: {suggestion}")
                self.log_output(f"Issue #{issue_id} marked as RESOLVED.")
        except Exception as e:
            logging.error(f"Error resolving issue: {e}")

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
        internal_phase = UI_TO_INTERNAL_PHASE.get(phase_name, 'IDLE')
        self.event_system.publish(Events.PHASE_CHANGED, internal_phase)

    def update_test_results(self, passed: bool, stdout: str, stderr: str) -> None:
        # Legacy
        if hasattr(self, 'test_result_panel'):
            self.test_result_panel.update_test_results(passed, stdout, stderr)

        # Rich (component is self.test_results)
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
                # Read content
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Use new code preview
                self.code_preview.open_file({'filepath': rel_path, 'content': content})

                # For compatibility with legacy file_manager
                self.file_manager.open_file(rel_path)
            except Exception as e:
                logging.error(f"Error opening file {filepath}: {e}")

    def _handle_file_modified(self, filepath):
        # Reload if it's the current file
        if self.file_manager.current_file_path and os.path.abspath(filepath) == os.path.abspath(self.file_manager.current_file_path):
            self.log_output(f"File modified on disk, reloading: {os.path.basename(filepath)}")
            self._handle_file_open(filepath)

    def update_ai_plan(self, plan_text: str, tasks: Optional[List[Task]] = None):
        if tasks:
            if hasattr(self, 'ai_plan_visualizer'):
                self.ai_plan_visualizer.update_plan(tasks)

            # Update sidebar task list too
            task_list = []
            for t in tasks:
                task_list.append({
                    'description': t.description,
                    'status': 'completed' if t.status == 'completed' else ('blocked' if t.status == 'blocked' else 'pending'),
                    'details': getattr(t, 'details', '')
                })
            self.event_system.publish("update_tasks", task_list)
            return

        # Fallback: Parse from text or file
        if self.controller.current_project:
            plan_path = Path(self.controller.current_project) / 'IMPLEMENTATION_PLAN.md'
            if plan_path.exists():
                parser = PlanParser()
                tasks = parser.parse(plan_path)
                if hasattr(self, 'ai_plan_visualizer'):
                    self.ai_plan_visualizer.update_plan(tasks)

    def log_output(self, message: str):
        # Use tabbed console instead of single output_console
        if hasattr(self, 'tabbed_console'):
            self.tabbed_console.log_all(message)
        else:
            # Fallback
            self.output_console.configure(state=tk.NORMAL)
            self.output_console.insert(tk.END, message + "\n")
            self.output_console.see(tk.END)
            self.output_console.configure(state=tk.DISABLED)
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

        # Stop animations when UI is re-enabled (generation finished)
        if enabled:
            self.stop_all_animations()
        else:
            # Re-enable animations if starting new generation
            if hasattr(self, 'ai_plan_visualizer'):
                self.ai_plan_visualizer.start_animations()

    def stop_all_animations(self):
        """Stop animations in all supporting components."""
        if hasattr(self, 'file_tree_view'):
            self.file_tree_view.stop_animations()
        if hasattr(self, 'ai_plan_visualizer'):
            self.ai_plan_visualizer.stop_animations()

# To avoid NameError in update_phase_ui
UI_TO_INTERNAL_PHASE = {
    "Write Test": "RED",
    "Run Test": "GREEN",
    "Implement": "GREEN",
    "Refactor": "REFACTOR",
    "Idle": "IDLE"
}
