import json
from tkinter import *


class Kanban:
    def __init__(self):
        """Initializes the Kanban board window and loads tasks"""
        self.kanban_data = {
            "columns": [
                "To Do",
                "In Progress",
                "Testing",
                "Done",
                "Continuous Improvement",
            ],
            "tasks": [
                {
                    "title": "Task 1",
                    "description": "Description 1",
                    "priority": "High",
                    "column": "To Do",
                },
                {
                    "title": "Task 2",
                    "description": "Description 2",
                    "priority": "Medium",
                    "column": "In Progress",
                },
            ],
            "wip_limits": {
                "To Do": 10,
                "In Progress": 5,
                "Testing": 5,
                "Done": float("inf"),
                "Continuous Improvement": 5,
            },
        }
        self.drag_label = None
        self.columns_frame = None
        self.kanban_window = None
        self.open_kanban_window()

    def open_kanban_window(self):
        """Opens the Kanban board window and loads the columns and tasks"""
        self.kanban_window = Toplevel()
        self.kanban_window.title("Kanban Board")
        self.kanban_window.geometry("1280x720")
        self.columns_frame = Frame(self.kanban_window)
        self.columns_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        self.load_kanban_data()
        self.refresh_kanban_board()
        self.kanban_window.protocol(
            "WM_DELETE_WINDOW", lambda: (self.save_kanban_data(), self.kanban_window.destroy())
        )

    def load_kanban_data(self):
        """Loads Kanban tasks from a file or creates a new file if it does not exist"""
        try:
            with open("data/kanban_tasks.json", "r") as f:
                self.kanban_data = json.load(f)
        except FileNotFoundError:
            self.save_kanban_data()

    def save_kanban_data(self):
        """Saves Kanban tasks to a file"""
        with open("data/kanban_tasks.json", "w") as f:
            json.dump(self.kanban_data, f, indent=4)

    def on_drag_start(self, event):
        """Handles the drag start event for tasks"""
        widget = event.widget
        index = widget.nearest(event.y)
        _, y, _, height = widget.bbox(index)
        if y <= event.y < y + height:
            widget.drag_data = widget.get(index)
            widget.selection_clear(0, END)
            widget.selection_set(index)
            widget.itemconfig(index, {"bg": "lightblue"})
            self.drag_label = Label(self.kanban_window, text=widget.drag_data, relief=RAISED)
            self.drag_label.place(x=event.x_root, y=event.y_root, anchor="center")

    def on_drag_motion(self, event):
        """Handles the drag motion event"""
        widget = event.widget
        if hasattr(widget, "drag_data") and self.drag_label:
            x, y = self.kanban_window.winfo_pointerxy()
            self.drag_label.place(x=x, y=y, anchor="center")
            target = widget.winfo_containing(x, y)
            if isinstance(target, Listbox):
                for child in self.columns_frame.winfo_children():
                    if isinstance(child, Frame):
                        child.config(bg="SystemButtonFace")
                target.master.config(bg="lightgreen")

    def on_drop(self, event):
        """Handles the drop event for tasks"""
        widget = event.widget
        if hasattr(widget, "drag_data"):
            x, y = widget.winfo_pointerxy()
            target = widget.winfo_containing(x, y)
            if isinstance(target, Listbox) and target != widget:
                item = widget.drag_data
                origin_column = widget.column
                target_column = target.column
                for task in self.kanban_data["tasks"]:
                    if task["title"] == item:
                        task["column"] = target_column
                        break
                self.save_kanban_data()
                self.refresh_kanban_board()
            for child in self.columns_frame.winfo_children():
                if isinstance(child, Frame):
                    child.config(bg="SystemButtonFace")
            if self.drag_label:
                self.drag_label.destroy()
                self.drag_label = None
            delattr(widget, "drag_data")

    def setup_drag_and_drop(self, listbox, column):
        """Configures drag and drop functionality for the listbox"""
        listbox.column = column
        listbox.bind("<ButtonPress-1>", self.on_drag_start)
        listbox.bind("<B1-Motion>", self.on_drag_motion)
        listbox.bind("<ButtonRelease-1>", self.on_drop)

    def add_task(self, event, column):
        """Adds a new task to the specified column"""
        task_title = event.widget.get()
        if task_title:
            new_task = {
                "title": task_title,
                "description": "",
                "priority": "Medium",
                "column": column,
            }
            self.kanban_data["tasks"].append(new_task)
            self.save_kanban_data()
            self.refresh_kanban_board()

    def create_column(self, column_name):
        """Creates a new column with tasks"""
        column_frame = Frame(self.columns_frame, borderwidth=2, relief="raised")
        column_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=5)
        label = Label(
            column_frame,
            text=f"{column_name} (Limit: {self.kanban_data['wip_limits'][column_name]})",
        )
        label.pack(pady=5)
        task_list = Listbox(column_frame, selectmode=SINGLE)
        task_list.pack(fill=BOTH, expand=True, padx=5, pady=5)
        for task in [t for t in self.kanban_data["tasks"] if t["column"] == column_name]:
            task_list.insert(END, task["title"])
        self.setup_drag_and_drop(task_list, column_name)
        entry = Entry(column_frame)
        entry.pack(fill=X, padx=5, pady=5)
        entry.bind("<Return>", lambda event, col=column_name: self.add_task(event, col))

    def refresh_kanban_board(self):
        """Refreshes the Kanban board by recreating all columns and tasks"""
        for widget in self.columns_frame.winfo_children():
            widget.destroy()
        for column in self.kanban_data["columns"]:
            self.create_column(column)
        for column_frame in self.columns_frame.winfo_children():
            entry_widget = column_frame.winfo_children()[-1]
            if isinstance(entry_widget, Entry):
                entry_widget.delete(0, END)
