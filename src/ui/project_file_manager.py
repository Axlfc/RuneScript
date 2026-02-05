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
        """
        No longer manages the tree widget directly as FileTreeView handles it.
        We just keep the current_project_files map in sync by walking the filesystem.
        """
        if not self.current_project:
            return

        try:
            self.current_project_files.clear()
            for root, dirs, files in os.walk(self.current_project):
                if any(x in root for x in ['.git', '.nia', '.venv', '__pycache__']): continue
                for file in files:
                    file_path = os.path.join(root, file)
                    # Use the path as ID for the map since we don't have the node IDs here
                    self.current_project_files[file_path] = file_path
        except Exception as e:
            logging.error(f"Error syncing project files map: {e}")

    def on_file_select(self, event):
        try:
            if not self.tree.winfo_exists(): return
            selected_item = self.tree.selection()
            if not selected_item:
                return

            item_data = self.tree.item(selected_item[0])
            if not item_data or 'values' not in item_data or not item_data['values']:
                return

            file_path = item_data['values'][0]
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
        except Exception as e:
            logging.error(f"Error in on_file_select: {e}")

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

