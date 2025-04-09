
import subprocess
from tkinter import Frame, Listbox, Scrollbar, Menu, Toplevel, END, LEFT, RIGHT, BOTH, Y, Label, DISABLED, scrolledtext

class CommitListView:
    def __init__(self, listbox_widget, ui_controller):
        if not hasattr(listbox_widget, "insert"):
            raise TypeError("Expected a tkinter Listbox for CommitListView")

        self.listbox = listbox_widget
        self.ui_controller = ui_controller

    def is_current_commit(self, line_hash, current_short_hash):
        return line_hash == current_short_hash

    def update_commit_list(self, commits=None):
        try:
            self.listbox.delete(0, "end")
            for commit in (commits or []):
                self.listbox.insert("end", commit)
        except Exception as e:
            print(f"Exception in update_commit_list: {e}, listbox type: {type(self.listbox)}")

    def apply_visual_styles(self, short_hash_number_commit):
        for i in range(self.listbox.size()):
            item = self.listbox.get(i)
            if short_hash_number_commit in item:
                self.listbox.itemconfig(i, {"bg": "yellow"})
            elif item.startswith("*"):
                self.listbox.itemconfig(i, {"fg": "green"})
            else:
                self.listbox.itemconfig(i, {"fg": "gray"})

    def on_double_click(self, event):
        try:
            idx = self.listbox.nearest(event.y)
            if idx >= 0:
                commit_line = self.listbox.get(idx).strip()
                if not commit_line:
                    return

                parts = commit_line.split(" ")
                if not parts:
                    return

                if commit_line.startswith("*") and len(parts) >= 2:
                    commit_hash = parts[1]
                elif len(parts) >= 1:
                    commit_hash = parts[0]
                else:
                    return

                self.view_commit_details(commit_hash)
        except Exception as e:
            self.ui_controller.ansi_renderer.insert_ansi_text(f"Double-click error: {e}\n", "error")

    def get_current_checkout_commit(self):
        try:
            result = self.ui_controller.run_git("rev-parse", "HEAD")
            return result.strip()
        except Exception as e:
            self.ui_controller.ansi_renderer.insert_ansi_text(f"Could not get current commit: {e}\n", "error")
            return ""

    def commit_list_context_menu(self, event):
        try:
            idx = self.listbox.nearest(event.y)
            if idx < 0:
                return

            commit_line = self.listbox.get(idx).strip()
            if commit_line.startswith("*"):
                commit_line = commit_line[2:]

            commit_hash = commit_line.split(" ")[0]

            menu = Menu(self.listbox, tearoff=0)
            menu.add_command(label="Checkout", command=lambda: self.checkout_commit(commit_hash))
            menu.add_command(label="View Details", command=lambda: self.view_commit_details(commit_hash))
            menu.add_command(label="Copy Hash", command=lambda: self.copy_to_clipboard(commit_hash))
            menu.add_command(label="Create Branch Here", command=lambda: self.create_branch_at_commit(commit_hash))
            menu.post(event.x_root, event.y_root)
        except Exception as e:
            self.ui_controller.ansi_renderer.insert_ansi_text(f"Context menu error: {e}\n", "error")

    def checkout_commit(self, commit_info):
        commit_hash = commit_info.split(" ")[0]
        try:
            self.ui_controller.execute_command(f"checkout {commit_hash}")
            self.ui_controller.update_status(commit_hash)
            self.update_commit_list()
        except subprocess.CalledProcessError as e:
            self.ui_controller.ansi_renderer.insert_ansi_text(
                f"Error checking out commit: {e.output}\n", "error"
            )
        short_hash = commit_hash[:7]
        self.apply_visual_styles(short_hash)

    def view_commit_details(self, commit_hash):
        try:
            commit_hash_number = commit_hash[:7]
            output = subprocess.check_output(
                ["git", "show", "--color=always", commit_hash_number],
                text=True,
                encoding="utf-8",
                errors='replace'
            )
            details_window = Toplevel()
            details_window.title(f"{commit_hash}")
            text_widget = scrolledtext.ScrolledText(details_window)
            self.ui_controller.ansi_renderer.define_ansi_tags(text_widget)
            self.ui_controller.ansi_renderer.apply_ansi_styles(text_widget, output)
            text_widget.config(state=DISABLED)
            text_widget.pack(fill="both", expand=True)
        except subprocess.CalledProcessError as e:
            error_window = Toplevel()
            error_window.title("Error")
            Label(
                error_window, text=f"Failed to fetch commit details: {e.output}"
            ).pack(pady=20, padx=20)

    def copy_to_clipboard(self, text):
        window = self.ui_controller.terminal_window
        window.clipboard_clear()
        window.clipboard_append(text)

    def create_branch_at_commit(self, commit_hash):
        from tkinter import simpledialog
        branch_name = simpledialog.askstring("Create Branch", "Enter new branch name:")
        if branch_name:
            self.ui_controller.execute_command(f"branch {branch_name} {commit_hash}")
            if hasattr(self.ui_controller, 'branch_menu_manager'):
                self.ui_controller.branch_menu_manager.populate_branch_menu()
