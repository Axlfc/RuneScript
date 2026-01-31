import tkinter as tk
import os
import json
import re
from tkinter import messagebox, simpledialog, TclError
import customtkinter as ctk
from src.ui.themed_window import ThemedWindow

# Constants
ALIAS_PATTERN = r'^[a-z][a-z0-9_]*[a-z0-9]$'
ALIAS_MIN_LENGTH = 3
ALIAS_MAX_LENGTH = 50
DEFAULT_CATEGORY_FILE = "data/prompt_categories.json"

class EditDialog(ctk.CTkToplevel):
    def __init__(self, parent, data=None, fields=None, title="Edit Dialog"):
        super().__init__(parent)
        self.title(title)
        self.data = data or {}
        self.fields = fields or []
        self.result = None
        self.entries = {}
        self.setup_ui()
        self.grab_set()

    def setup_ui(self):
        for i, (label_text, key, default) in enumerate(self.fields):
            ctk.CTkLabel(self, text=label_text).grid(row=i, column=0, padx=10, pady=5, sticky="e")
            entry = ctk.CTkEntry(self)
            entry.insert(0, str(self.data.get(key, default)))
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="we")
            self.entries[key] = entry

        btn_frame = ctk.CTkFrame(self)
        btn_frame.grid(row=len(self.fields), column=0, columnspan=2, pady=10)
        ctk.CTkButton(btn_frame, text="Save", command=self.save).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", command=self.destroy).pack(side="left", padx=5)

    def save(self):
        self.result = {key: entry.get() for key, entry in self.entries.items()}
        self.destroy()

class VariableEditDialog(EditDialog):
    def __init__(self, parent, data=None):
        fields = [
            ("Name", "name", ""),
            ("Description", "description", ""),
            ("Type", "type", "text"),
            ("Default", "default", "")
        ]
        super().__init__(parent, data, fields, "Edit Variable")

class ArgumentEditDialog(EditDialog):
    def __init__(self, parent, data=None):
        fields = [
            ("Name", "name", ""),
            ("Description", "description", ""),
            ("Default", "default", "")
        ]
        super().__init__(parent, data, fields, "Edit Argument")

class PromptEnhancementWindow(ThemedWindow):
    def __init__(self, parent=None):
        if parent is None:
            try:
                from src.views.tk_utils import root
                parent = root
            except ImportError:
                pass
        super().__init__(parent)
        self.title("Prompt Enhancement & Management")
        self.geometry("1200x800")

        self.prompt_folder = "prompts"
        os.makedirs(self.prompt_folder, exist_ok=True)
        self.prompt_data = {}
        self.categories = self.load_categories()
        self.arguments = []
        self.variables = []

        self.setup_ui()
        self.populate_treeview()

    def load_categories(self):
        if os.path.exists(DEFAULT_CATEGORY_FILE):
            try:
                with open(DEFAULT_CATEGORY_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_categories(self):
        os.makedirs(os.path.dirname(DEFAULT_CATEGORY_FILE), exist_ok=True)
        with open(DEFAULT_CATEGORY_FILE, "w") as f:
            json.dump(self.categories, f, indent=4)

    def setup_ui(self):
        self.paned = ctk.CTkFrame(self)
        self.paned.pack(fill="both", expand=True)

        # Sidebar for categories
        self.sidebar = ctk.CTkFrame(self.paned, width=250)
        self.sidebar.pack(side="left", fill="y", padx=5, pady=5)

        ctk.CTkLabel(self.sidebar, text="Categories", font=("Arial", 14, "bold")).pack(pady=10)

        from tkinter import ttk
        self.category_tree = ttk.Treeview(self.sidebar)
        self.category_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.category_tree.bind("<<TreeviewSelect>>", self.on_treeview_select)

        # Main editor area
        self.main_area = ctk.CTkScrollableFrame(self.paned)
        self.main_area.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # Title & Meta
        meta_frame = ctk.CTkFrame(self.main_area)
        meta_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(meta_frame, text="Title:").grid(row=0, column=0, padx=5, pady=5)
        self.title_entry = ctk.CTkEntry(meta_frame)
        self.title_entry.grid(row=0, column=1, sticky="we", padx=5, pady=5)

        ctk.CTkLabel(meta_frame, text="Category:").grid(row=1, column=0, padx=5, pady=5)
        self.category_entry = ctk.CTkEntry(meta_frame)
        self.category_entry.grid(row=1, column=1, sticky="we", padx=5, pady=5)

        ctk.CTkLabel(meta_frame, text="Alias:").grid(row=2, column=0, padx=5, pady=5)
        self.alias_entry = ctk.CTkEntry(meta_frame)
        self.alias_entry.grid(row=2, column=1, sticky="we", padx=5, pady=5)
        meta_frame.columnconfigure(1, weight=1)

        # Prompt content
        ctk.CTkLabel(self.main_area, text="Prompt Template:", font=("Arial", 12, "bold")).pack(pady=(10, 0))
        self.prompt_text = ctk.CTkTextbox(self.main_area, height=200)
        self.prompt_text.pack(fill="x", padx=10, pady=5)

        # Arguments and Variables
        tabs = ctk.CTkTabview(self.main_area, height=300)
        tabs.pack(fill="x", padx=10, pady=10)
        tabs.add("Arguments")
        tabs.add("Variables")

        self.setup_arguments_tab(tabs.tab("Arguments"))
        self.setup_variables_tab(tabs.tab("Variables"))

        # Buttons
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", side="bottom", pady=10)

        ctk.CTkButton(btn_frame, text="New", command=self.new_prompt).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Save", command=self.save_prompt).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Test", command=self.test_prompt).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Export", command=self.export_prompt).pack(side="left", padx=10)

    def setup_arguments_tab(self, frame):
        from tkinter import ttk
        self.arg_tree = ttk.Treeview(frame, columns=("name", "description", "default"), show="headings")
        self.arg_tree.heading("name", text="Name")
        self.arg_tree.heading("description", text="Description")
        self.arg_tree.heading("default", text="Default")
        self.arg_tree.pack(side="left", fill="both", expand=True)

        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(side="right", fill="y", padx=5)
        ctk.CTkButton(btn_frame, text="Add", width=60, command=self.add_argument).pack(pady=2)
        ctk.CTkButton(btn_frame, text="Edit", width=60, command=self.edit_argument).pack(pady=2)
        ctk.CTkButton(btn_frame, text="Del", width=60, command=self.delete_argument).pack(pady=2)

    def setup_variables_tab(self, frame):
        from tkinter import ttk
        self.var_tree = ttk.Treeview(frame, columns=("name", "description", "type", "default"), show="headings")
        self.var_tree.heading("name", text="Name")
        self.var_tree.heading("description", text="Description")
        self.var_tree.heading("type", text="Type")
        self.var_tree.heading("default", text="Default")
        self.var_tree.pack(side="left", fill="both", expand=True)

        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(side="right", fill="y", padx=5)
        ctk.CTkButton(btn_frame, text="Add", width=60, command=self.add_variable).pack(pady=2)
        ctk.CTkButton(btn_frame, text="Edit", width=60, command=self.edit_variable).pack(pady=2)
        ctk.CTkButton(btn_frame, text="Del", width=60, command=self.delete_variable).pack(pady=2)

    # ... Placeholder for other methods to keep functionality ...
    def on_treeview_select(self, event):
        selected = self.category_tree.selection()
        if selected:
            item = self.category_tree.item(selected[0])
            if item["values"] and item["values"][0] == "prompt":
                self.load_prompt_by_title(item["text"])

    def load_prompt_by_title(self, title):
        path = os.path.join(self.prompt_folder, f"{title}.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
                self.title_entry.delete(0, "end")
                self.title_entry.insert(0, data.get("title", ""))
                self.category_entry.delete(0, "end")
                self.category_entry.insert(0, data.get("category", ""))
                self.alias_entry.delete(0, "end")
                self.alias_entry.insert(0, data.get("alias", ""))
                self.prompt_text.delete("1.0", "end")
                self.prompt_text.insert("1.0", data.get("content", ""))
                self.arguments = data.get("arguments", [])
                self.variables = data.get("variables", [])
                self.load_arguments_into_tree()
                self.load_variables_into_tree()

    def load_arguments_into_tree(self):
        self.arg_tree.delete(*self.arg_tree.get_children())
        for arg in self.arguments:
            self.arg_tree.insert("", "end", values=(arg["name"], arg["description"], arg.get("default", "")))

    def load_variables_into_tree(self):
        self.var_tree.delete(*self.var_tree.get_children())
        for var in self.variables:
            self.var_tree.insert("", "end", values=(var["name"], var["description"], var["type"], var.get("default", "")))

    def add_argument(self):
        dialog = ArgumentEditDialog(self)
        if dialog.result:
            self.arguments.append(dialog.result)
            self.load_arguments_into_tree()

    def edit_argument(self):
        selected = self.arg_tree.selection()
        if selected:
            idx = self.arg_tree.index(selected[0])
            dialog = ArgumentEditDialog(self, self.arguments[idx])
            if dialog.result:
                self.arguments[idx] = dialog.result
                self.load_arguments_into_tree()

    def delete_argument(self):
        selected = self.arg_tree.selection()
        if selected:
            idx = self.arg_tree.index(selected[0])
            self.arguments.pop(idx)
            self.load_arguments_into_tree()

    def add_variable(self):
        dialog = VariableEditDialog(self)
        if dialog.result:
            self.variables.append(dialog.result)
            self.load_variables_into_tree()

    def edit_variable(self):
        selected = self.var_tree.selection()
        if selected:
            idx = self.var_tree.index(selected[0])
            dialog = VariableEditDialog(self, self.variables[idx])
            if dialog.result:
                self.variables[idx] = dialog.result
                self.load_variables_into_tree()

    def delete_variable(self):
        selected = self.var_tree.selection()
        if selected:
            idx = self.var_tree.index(selected[0])
            self.variables.pop(idx)
            self.load_variables_into_tree()

    def save_prompt(self):
        title = self.title_entry.get().strip()
        category = self.category_entry.get().strip()
        content = self.prompt_text.get("1.0", "end").strip()
        alias = self.alias_entry.get().strip()

        if not title or not content or not category:
            messagebox.showerror("Error", "Title, category, and content are required.")
            return

        data = {
            "title": title,
            "category": category,
            "content": content,
            "alias": alias,
            "arguments": self.arguments,
            "variables": self.variables
        }

        with open(os.path.join(self.prompt_folder, f"{title}.json"), "w") as f:
            json.dump(data, f, indent=4)

        self.populate_treeview()
        messagebox.showinfo("Success", "Prompt saved.")

    def new_prompt(self):
        self.title_entry.delete(0, "end")
        self.category_entry.delete(0, "end")
        self.alias_entry.delete(0, "end")
        self.prompt_text.delete("1.0", "end")
        self.arguments = []
        self.variables = []
        self.load_arguments_into_tree()
        self.load_variables_into_tree()

    def test_prompt(self):
        content = self.prompt_text.get("1.0", "end").strip()
        for var in self.variables:
            content = content.replace(f"{{{{{var['name']}}}}}", var.get("default", ""))
        messagebox.showinfo("Test Prompt", content)

    def export_prompt(self):
        title = self.title_entry.get().strip()
        content = self.prompt_text.get("1.0", "end").strip()
        if title and content:
            with open(os.path.join(self.prompt_folder, f"{title}.txt"), "w") as f:
                f.write(content)
            messagebox.showinfo("Export", f"Exported to {title}.txt")

    def populate_treeview(self):
        self.category_tree.delete(*self.category_tree.get_children())
        # Simplistic population for now
        prompts = [f.replace(".json", "") for f in os.listdir(self.prompt_folder) if f.endswith(".json")]
        for p in prompts:
            self.category_tree.insert("", "end", text=p, values=("prompt",))
