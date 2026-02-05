import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from src.ui.rich_components import FileTreeView
from src.utils.event_system import EventSystem, Events

class Sidebar(tb.Frame):
    """
    Sidebar component containing the File Tree and Task List.
    """
    def __init__(self, parent, project_path, on_file_open, on_file_modified):
        super().__init__(parent)
        self.event_system = EventSystem.get_instance()

        self.paned = tb.PanedWindow(self, orient=VERTICAL)
        self.paned.pack(fill=BOTH, expand=True)

        # 1. File Tree
        self.tree_frame = tb.Frame(self.paned)
        self.paned.add(self.tree_frame, weight=3)

        tb.Label(self.tree_frame, text="📁 FILES", font=('Segoe UI', 10, 'bold')).pack(fill=X, padx=5, pady=5)
        self.file_tree = FileTreeView(
            self.tree_frame,
            project_path,
            on_file_open_callback=on_file_open,
            on_file_modified_callback=on_file_modified
        )
        self.file_tree.pack(fill=BOTH, expand=True)

        # 2. Task List
        self.task_frame = tb.Frame(self.paned)
        self.paned.add(self.task_frame, weight=2)

        header = tb.Frame(self.task_frame)
        header.pack(fill=X, padx=5, pady=5)
        tb.Label(header, text="📋 TASKS", font=('Segoe UI', 10, 'bold')).pack(side=LEFT)

        self.task_container = tb.ScrolledFrame(self.task_frame, autohide=True)
        self.task_container.pack(fill=BOTH, expand=True)

        self._setup_event_listeners()

    def _setup_event_listeners(self):
        self.event_system.subscribe(Events.UPDATE_TASKS, self.update_tasks)

    def update_tasks(self, tasks):
        # Clear existing tasks
        for child in self.task_container.winfo_children():
            child.destroy()

        for i, task in enumerate(tasks):
            status_icon = "⬜"
            color = "#aaaaaa"
            if task.get('status') == 'completed':
                status_icon = "✅"
                color = "#38a169"
            elif task.get('status') == 'in_progress':
                status_icon = "🔄"
                color = "#d69e2e"
            elif task.get('status') == 'blocked':
                status_icon = "❌"
                color = "#e53e3e"

            task_row = tb.Frame(self.task_container)
            task_row.pack(fill=X, pady=2)

            tb.Label(task_row, text=f"{status_icon} {i+1}. {task.get('description')}",
                     wraplength=200, foreground=color, font=('Segoe UI', 9)).pack(side=LEFT, padx=5)

            if task.get('status') == 'in_progress':
                # Show details for current task
                details = tb.Label(self.task_container, text=task.get('details', ''),
                                  wraplength=180, font=('Segoe UI', 8, 'italic'), foreground="#888888")
                details.pack(fill=X, padx=25, pady=(0, 5))
