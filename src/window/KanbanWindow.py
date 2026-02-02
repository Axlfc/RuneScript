import tkinter as tk
import customtkinter as ctk
import json
from src.ui.themed_window import ThemedWindow

class KanbanWindow(ThemedWindow):
    def __init__(self, parent=None):
        """Initializes the Kanban board window and loads tasks"""
        if parent is None:
            try:
                from src.views.tk_utils import root
                parent = root
            except ImportError:
                pass
        super().__init__(parent)
        self.title("Kanban Board")
        self.geometry("1280x720")

        self.kanban_data = {
            "columns": ["To Do", "In Progress", "Testing", "Done", "Continuous Improvement"],
            "tasks": [],
            "wip_limits": {
                "To Do": 10, "In Progress": 5, "Testing": 5, "Done": float("inf"),
                "Continuous Improvement": 5
            }
        }
        self.drag_label = None
        self.columns_frame = ctk.CTkFrame(self)
        self.columns_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.load_kanban_data()
        self.refresh_kanban_board()

    def load_kanban_data(self):
        try:
            if os.path.exists("data/kanban_tasks.json"):
                with open("data/kanban_tasks.json", "r") as f:
                    self.kanban_data = json.load(f)
        except Exception:
            self.save_kanban_data()

    def save_kanban_data(self):
        os.makedirs("data", exist_ok=True)
        with open("data/kanban_tasks.json", "w") as f:
            json.dump(self.kanban_data, f, indent=4)

    def refresh_theme(self):
        super().refresh_theme()
        self.refresh_kanban_board()

    def refresh_kanban_board(self):
        for widget in self.columns_frame.winfo_children():
            widget.destroy()

        # Use a grid or a horizontal frame for columns
        for i, column in enumerate(self.kanban_data["columns"]):
            self.create_column(column)

    def create_column(self, column_name):
        col_frame = ctk.CTkFrame(self.columns_frame)
        col_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        limit = self.kanban_data['wip_limits'].get(column_name, "N/A")
        ctk.CTkLabel(col_frame, text=f"{column_name} ({limit})", font=("Arial", 12, "bold")).pack(pady=5)

        # Get theme colors
        is_dark = ctk.get_appearance_mode().lower() == "dark"
        bg = "#2b2b2b" if is_dark else "white"
        fg = "white" if is_dark else "black"

        # We'll use a standard Listbox for now as CTk doesn't have a direct equivalent easily draggable
        from tkinter import Listbox, SINGLE
        task_list = Listbox(col_frame, selectmode=SINGLE, bg=bg, fg=fg, borderwidth=0, highlightthickness=0)
        task_list.pack(fill="both", expand=True, padx=5, pady=5)

        for task in [t for t in self.kanban_data["tasks"] if t["column"] == column_name]:
            task_list.insert("end", task["title"])

        self.setup_drag_and_drop(task_list, column_name)

        entry = ctk.CTkEntry(col_frame, placeholder_text="Add task...")
        entry.pack(fill="x", padx=5, pady=5)
        entry.bind("<Return>", lambda e, c=column_name: self.add_task(e, c))

    def setup_drag_and_drop(self, listbox, column):
        listbox.column = column
        listbox.bind("<ButtonPress-1>", self.on_drag_start)
        listbox.bind("<B1-Motion>", self.on_drag_motion)
        listbox.bind("<ButtonRelease-1>", self.on_drop)

    def on_drag_start(self, event):
        widget = event.widget
        index = widget.nearest(event.y)
        if index >= 0:
            widget.drag_data = widget.get(index)
            self.drag_label = ctk.CTkLabel(self, text=widget.drag_data, fg_color="blue")
            self.drag_label.place(x=event.x_root - self.winfo_rootx(), y=event.y_root - self.winfo_rooty(), anchor="center")

    def on_drag_motion(self, event):
        if self.drag_label:
            self.drag_label.place(x=event.x_root - self.winfo_rootx(), y=event.y_root - self.winfo_rooty(), anchor="center")

    def on_drop(self, event):
        widget = event.widget
        if hasattr(widget, "drag_data"):
            x, y = self.winfo_pointerxy()
            target = self.winfo_containing(x, y)

            from tkinter import Listbox
            if isinstance(target, Listbox) and target != widget:
                item = widget.drag_data
                target_column = target.column
                for task in self.kanban_data["tasks"]:
                    if task["title"] == item:
                        task["column"] = target_column
                        break
                self.save_kanban_data()
                self.refresh_kanban_board()

            if self.drag_label:
                self.drag_label.destroy()
                self.drag_label = None
            delattr(widget, "drag_data")

    def add_task(self, event, column):
        title = event.widget.get().strip()
        if title:
            self.kanban_data["tasks"].append({
                "title": title,
                "description": "",
                "priority": "Medium",
                "column": column
            })
            self.save_kanban_data()
            self.refresh_kanban_board()

    def _on_close(self):
        self.save_kanban_data()
        super()._on_close()
import os
