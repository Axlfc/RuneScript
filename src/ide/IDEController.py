import os
import sys
import logging
import tkinter as tk
import uuid
from tkinter import messagebox, filedialog
import queue

from src.ai.AIAgentOrchestrator import AIAgentOrchestrator
from src.core.ProjectLifecycleManager import ProjectLifecycleManager
from src.ui.UIManager import UIManager
from src.ui.themed_window import ThemedWindow


class IDEController(ThemedWindow):
    """
    Central controller coordinating all IDE components and managing application lifecycle.
    """

    def __init__(self, root=None):
        if root is None:
            try:
                from src.views.tk_utils import root as tk_root
                root = tk_root
            except ImportError:
                pass

        super().__init__(root)
        self.root = self # In this architecture, self IS the window

        self.title("Red-Green-Refactor IDE")
        self.geometry("1400x900")

        # Initialize queues for asynchronous communication
        self.ai_task_queue = queue.Queue()
        self.ai_response_queue = queue.Queue()

        # Initialize paths
        self.projects_base_dir = os.path.join('data', 'projects')
        os.makedirs(self.projects_base_dir, exist_ok=True)

        # Initialize components
        self._current_project = None
        self.current_project_files = {}

        # Setup logging
        self.setup_logging()

        # Initialize managers
        self.project_manager = ProjectLifecycleManager(self)
        self.ui_manager = UIManager(self)
        self.ai_orchestrator = AIAgentOrchestrator(self)

        # Start UI polling
        self.poll_queue()

    @property
    def current_project(self):
        return self._current_project

    @current_project.setter
    def current_project(self, value):
        self._current_project = value

        # Sync with file manager
        if hasattr(self.ui_manager, "file_manager") and self.ui_manager.file_manager:
            self.ui_manager.file_manager.project_path = value

        # Log assignment
        if value:
            logging.info(f"Current project set to: {value}")
        else:
            logging.info("Current project cleared.")

    def safe_ui_call(self, func, *args, **kwargs):
        """Safely execute UI operations on the main thread"""
        if self.root and self.root.winfo_exists():
            try:
                self.root.after(0, lambda: func(*args, **kwargs))
            except RuntimeError as e:
                logging.warning(f"safe_ui_call failed: {e}")
        else:
            logging.warning("safe_ui_call skipped: root window no longer exists.")

    def poll_queue(self):
        """Poll the AI response queue for updates"""
        try:
            while not self.ai_response_queue.empty():
                status, data = self.ai_response_queue.get_nowait()
                if status == "success":
                    self.root.after(0, lambda d=data: self.project_manager.finalize_project_generation(d))
                elif status == "error":
                    self.root.after(0,
                                    lambda msg=data: self.project_manager.handle_generation_failure(error_message=msg))
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.poll_queue)

    def new_project(self):
        """Create a new project"""
        project_id = str(uuid.uuid4())
        project_path = os.path.join(self.projects_base_dir, project_id)
        os.makedirs(project_path, exist_ok=True)
        self.current_project = project_path
        self.ui_manager.log_output(f"New project created: {project_path}")

    def open_project(self):
        """Open an existing project"""
        project_path = filedialog.askdirectory(initialdir=self.projects_base_dir)
        if project_path:
            self.current_project = project_path
            self.ui_manager.log_output(f"Opened project: {project_path}")
            self.ui_manager.file_manager.populate_tree_view()

    def safe_new_project(self):
        """Safely create a new project with error handling"""
        try:
            self.new_project()
        except Exception as e:
            messagebox.showerror("Project Creation Error", str(e))
            logging.error(f"Project creation failed: {e}")

    def safe_open_project(self):
        """Safely open a project with error handling"""
        try:
            self.open_project()
        except Exception as e:
            messagebox.showerror("Project Open Error", str(e))
            logging.error(f"Project open failed: {e}")

    def setup_logging(self):
        """Configure application logging"""
        # Forzar UTF-8 en Windows para stdout/stderr para evitar UnicodeEncodeError con emojis
        if sys.platform == 'win32':
            try:
                if hasattr(sys.stdout, 'reconfigure'):
                    sys.stdout.reconfigure(encoding='utf-8')
                if hasattr(sys.stderr, 'reconfigure'):
                    sys.stderr.reconfigure(encoding='utf-8')
            except Exception as e:
                print(f"Warning: Could not reconfigure stdout/stderr to utf-8: {e}")

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler('project.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )

    def show_about(self):
        """Display about information"""
        messagebox.showinfo(
            "About Red-Green-Refactor IDE",
            "A comprehensive development environment for Test-Driven Development."
        )

    def run(self):
        """Start the application main loop"""
        # If it's a Toplevel, we don't necessarily need a new mainloop
        # but calling it is harmless and allows it to run standalone.
        if isinstance(self.root, tk.Tk):
            self.root.mainloop()
        else:
            # For Toplevel, just ensure it's visible and focused
            self.root.deiconify()
            self.root.focus_set()


