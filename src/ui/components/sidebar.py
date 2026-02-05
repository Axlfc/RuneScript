import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from src.ui.rich_components import FileTreeView
from src.utils.event_system import EventSystem, Events

class Sidebar(tb.Frame):
    """
    Sidebar component containing the File Tree and Task List.
    """
    def __init__(self, parent, project_path, on_file_open, on_file_modified):
        super().__init__(parent)
        self.event_system = EventSystem.get_instance()

        self.paned = ttk.PanedWindow(self, orient=VERTICAL)
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

        # 2. Task List & Details
        self.task_frame = tb.Frame(self.paned)
        self.paned.add(self.task_frame, weight=2)

        # Current Task Details (Collapsible)
        self.details_visible = tk.BooleanVar(value=True)
        self.details_container = tb.Frame(self.task_frame)
        self.details_container.pack(fill=X, padx=5, pady=(5, 0))

        details_header = tb.Frame(self.details_container)
        details_header.pack(fill=X)
        tb.Label(details_header, text="🎯 CURRENT TASK", font=('Segoe UI', 10, 'bold')).pack(side=LEFT)
        self.toggle_details_btn = tb.Button(details_header, text="▼", bootstyle="link",
                                            command=self._toggle_details)
        self.toggle_details_btn.pack(side=RIGHT)

        self.details_content = tb.Frame(self.details_container, bootstyle=DARK, padding=10)
        self.details_content.pack(fill=X, pady=5)

        self.current_task_label = tb.Label(self.details_content, text="No active task",
                                          wraplength=200, font=('Segoe UI', 9, 'italic'))
        self.current_task_label.pack(fill=X)

        # Tasks Header
        tasks_header = tb.Frame(self.task_frame)
        tasks_header.pack(fill=X, padx=5, pady=5)
        tb.Label(tasks_header, text="📋 ALL TASKS", font=('Segoe UI', 10, 'bold')).pack(side=LEFT)

        self.task_container = ScrolledFrame(self.task_frame, autohide=True)
        self.task_container.pack(fill=BOTH, expand=True)

        self._setup_event_listeners()

    def _setup_event_listeners(self):
        self.event_system.subscribe(Events.UPDATE_TASKS, self.update_tasks)

    def _toggle_details(self):
        if self.details_visible.get():
            self.details_content.pack_forget()
            self.toggle_details_btn.configure(text="▶")
            self.details_visible.set(False)
        else:
            self.details_content.pack(fill=X, pady=5)
            self.toggle_details_btn.configure(text="▼")
            self.details_visible.set(True)

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
                # Update current task details section
                self.current_task_label.configure(text=f"\"{task.get('description')}\"\n\n{task.get('details', '')}")
