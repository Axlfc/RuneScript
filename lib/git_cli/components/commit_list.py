import subprocess
from tkinter import Frame, Listbox, Scrollbar, Menu, Toplevel, END, LEFT, RIGHT, BOTH, Y, Label, DISABLED, scrolledtext


class CommitListView:
    """
    Component that manages the commit list functionality.
    """

    def __init__(self, parent, git_window):
        self.git_window = git_window
        self.frame = Frame(parent)
        self.frame.pack(fill="both", expand=True)

        self.scrollbar = Scrollbar(self.frame)
        self.scrollbar.pack(side=RIGHT, fill=Y)

        self.listbox = Listbox(self.frame, yscrollcommand=self.scrollbar.set)
        self.listbox.pack(side=LEFT, fill=BOTH, expand=True)

        self.scrollbar.config(command=self.listbox.yview)

        # Add context menu binding
        self.listbox.bind("<Button-3>", self.commit_list_context_menu)
        self.listbox.bind("<Double-Button-1>", self.on_double_click)

        # Update the commit list initially
        self.update_commit_list()

    def is_current_commit(self, line_hash, current_short_hash):
        return line_hash == current_short_hash

    def update_commit_list(self):
        command = 'git log --no-merges --color --graph --pretty=format:"%h %d %s - <%an (%cr)>" --abbrev-commit --branches'
        output = subprocess.check_output(command, shell=True, text=True)
        self.listbox.delete(0, END)
        self.apply_visual_styles()
        current_commit = self.get_current_checkout_commit()
        short_hash_number_commit = current_commit[:7]
        for line in output.split("\n"):
            # Se ignoran los dos primeros caracteres (pueden ser parte del grafo)
            line = line[2:]
            if short_hash_number_commit in line:
                self.listbox.insert(END, f"* {line}")
            else:
                self.listbox.insert(END, line)
        self.apply_visual_styles()

    def apply_visual_styles(self):
        current_commit = self.get_current_checkout_commit()
        for i in range(self.listbox.size()):
            item = self.listbox.get(i)
            if current_commit in item:
                self.listbox.itemconfig(i, {"bg": "yellow"})
            elif item.startswith("*"):
                self.listbox.itemconfig(i, {"fg": "green"})
            else:
                self.listbox.itemconfig(i, {"fg": "gray"})

    def on_double_click(self, event):
        """Handle double-click on a commit to view details."""
        try:
            idx = self.listbox.nearest(event.y)
            if idx >= 0:
                commit_line = self.listbox.get(idx)
                if commit_line.startswith('*'):
                    commit_hash = commit_line.split(" ", 2)[1]
                else:
                    commit_hash = commit_line.split(" ", 1)[0]
                self.view_commit_details(commit_hash)
        except Exception as e:
            self.git_window.ansi_renderer.insert_ansi_text(f"Double-click error: {e}\n", "error")

    def get_current_checkout_commit(self):
        """Get the hash of the currently checked out commit."""
        try:
            result = self.git_window.dispatcher.dispatch_line("rev-parse HEAD")
            return result.get("stdout", "").strip()
        except Exception as e:
            self.git_window.ansi_renderer.insert_ansi_text(f"Could not get current commit: {e}\n", "error")
            return ""

    def commit_list_context_menu(self, event):
        try:
            idx = self.listbox.nearest(event.y)
            if idx < 0:
                return

            commit_line = self.listbox.get(idx).strip()
            if commit_line.startswith("*"):
                commit_line = commit_line[2:]  # Remove '* ' prefix

            commit_hash = commit_line.split(" ")[0]  # Extract the short hash

            menu = Menu(self.listbox, tearoff=0)
            menu.add_command(label="Checkout", command=lambda: self.checkout_commit(commit_hash))
            menu.add_command(label="View Details", command=lambda: self.view_commit_details(commit_hash))
            menu.add_command(label="Copy Hash", command=lambda: self.copy_to_clipboard(commit_hash))
            menu.add_command(label="Create Branch Here", command=lambda: self.create_branch_at_commit(commit_hash))
            menu.post(event.x_root, event.y_root)
        except Exception as e:
            self.git_window.ansi_renderer.insert_ansi_text(f"Context menu error: {e}\n", "error")

    def checkout_commit(self, commit_info):
        commit_hash = commit_info.split(" ")[0]
        try:
            self.git_window.execute_command(f"checkout {commit_hash}")
            self.git_window.update_status(commit_hash)
            self.update_commit_list(self.git_window.commit_list)
        except subprocess.CalledProcessError as e:
            self.git_window.ansi_renderer.insert_ansi_text(
                self.git_window.output_text, f"Error checking out commit: {e.output}\n", "error"
            )
        self.apply_visual_styles(self.git_window.commit_list)

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
            self.git_window.ansi_renderer.define_ansi_tags(text_widget)
            self.git_window.ansi_renderer.apply_ansi_styles(text_widget, output)
            text_widget.config(state=DISABLED)
            text_widget.pack(fill="both", expand=True)
        except subprocess.CalledProcessError as e:
            error_window = Toplevel()
            error_window.title("Error")
            Label(
                error_window, text=f"Failed to fetch commit details: {e.output}"
            ).pack(pady=20, padx=20)

    def copy_to_clipboard(self, text):
        """Copy text to clipboard."""
        window = self.git_window.terminal_window
        window.clipboard_clear()
        window.clipboard_append(text)

    def create_branch_at_commit(self, commit_hash):
        """Create a new branch at the specified commit."""
        from tkinter import simpledialog
        branch_name = simpledialog.askstring("Create Branch", "Enter new branch name:")
        if branch_name:
            self.git_window.execute_command(f"branch {branch_name} {commit_hash}")
            if hasattr(self.git_window, 'branch_menu_manager'):
                self.git_window.branch_menu_manager.populate_branch_menu()
