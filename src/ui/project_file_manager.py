import os
import logging
from tkinter import END


class ProjectFileManager:
    def __init__(self, tree_widget, file_editor, log_fn):
        self.tree = tree_widget
        self.editor = file_editor
        self.log_fn = log_fn

        self.current_project = None
        self.current_project_files = {}
        self.current_file_path = None

    def set_project_path(self, path: str):
        self.current_project = path

    def populate_tree_view(self):
        if not self.current_project:
            self.log_fn("No project loaded.")
            return

        try:
            self.tree.delete(*self.tree.get_children())
            self.current_project_files.clear()

            for root, dirs, files in os.walk(self.current_project):
                parent = self.tree.insert('', 'end', text=os.path.basename(root), values=(root,))
                for file in files:
                    file_path = os.path.join(root, file)
                    file_id = self.tree.insert(parent, 'end', text=file, values=(file_path,))
                    self.current_project_files[file_id] = file_path
        except Exception as e:
            logging.error(f"Error populating tree view: {e}")
            self.log_fn(f"Error loading project tree: {e}")

    def on_file_select(self, event):
        selected_item = self.tree.selection()
        if not selected_item:
            return

        file_path = self.tree.item(selected_item[0])['values'][0]
        if os.path.isfile(file_path):
            self.current_file_path = file_path
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.editor.delete('1.0', END)
                    self.editor.insert('1.0', content)
                    self.editor.edit_modified(False)
            except Exception as e:
                self.log_fn(f"Error reading file: {e}")
                logging.error(f"Error reading file: {e}")

    def on_file_modified(self, event=None):
        # We'll wire this later with save logic if needed
        pass

    def open_file(self, relative_path: str):
        """
        Opens a file in the editor by relative path from project root.
        """
        if not self.current_project:
            self.log_fn("No project is currently loaded.")
            return

        full_path = os.path.join(self.current_project, relative_path)
        if not os.path.isfile(full_path):
            self.log_fn(f"File not found: {relative_path}")
            return

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.editor.delete('1.0', END)
            self.editor.insert('1.0', content)
            self.editor.edit_modified(False)
            self.current_file_path = full_path
            self.log_fn(f"Opened file: {relative_path}")
        except Exception as e:
            logging.error(f"Failed to open file {relative_path}: {e}")
            self.log_fn(f"Failed to open file: {e}")
