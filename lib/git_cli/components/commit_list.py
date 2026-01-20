
import subprocess
from tkinter import Frame, Listbox, Scrollbar, Menu, Toplevel, END, LEFT, RIGHT, BOTH, Y, Label, DISABLED, scrolledtext, \
    SINGLE, VERTICAL


class CommitListView(Frame):
    def __init__(self, parent, ui_controller=None):
        super().__init__(parent)
        self.ui_controller = ui_controller
        self.parent = parent

        # Create scrollable listbox
        self.listbox = Listbox(self, selectmode=SINGLE, exportselection=False)
        scrollbar = Scrollbar(self, orient=VERTICAL, command=self.listbox.yview)

        # Pack widgets
        self.listbox.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.listbox.configure(yscrollcommand=scrollbar.set)

        # Bind events
        self.listbox.bind("<Double-Button-1>", self.on_double_click)
        self.listbox.bind("<Button-3>", self.commit_list_context_menu)

    def is_current_commit(self, line_hash, current_short_hash):
        return line_hash == current_short_hash

    def update_commit_list(self, commits=None):
        """Update the commit list with commits from the UI controller"""
        try:
            # Clear the listbox
            self.listbox.delete(0, END)

            # If no commits provided, get them from controller
            if commits is None and self.ui_controller:
                branch = getattr(self.ui_controller, 'current_branch', None)
                commits = self.ui_controller.get_commits_for_selected_branch(branch)

            # Add commits to listbox
            if commits:
                for commit in commits:
                    if isinstance(commit, dict):
                        commit_hash = commit.get('hash', '')
                        message = commit.get('message', '')
                        self.listbox.insert(END, f"{commit_hash} - {message}")
                    else:
                        self.listbox.insert(END, str(commit))

            print(f"[CommitListView] Loaded {self.listbox.size()} commits")

        except Exception as e:
            print(f"[CommitListView] Exception updating commit list: {e}")

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
        if not self.ui_controller:
            return

        selection = self.listbox.curselection()
        if selection:
            idx = selection[0]
            commit_line = self.listbox.get(idx)
            if commit_line:
                commit_hash = commit_line.split(" - ")[0]
                details = self.ui_controller.get_commit_details(commit_hash)
                if details:
                    self.ui_controller.show_commit_details(commit_hash)

    def get_current_checkout_commit(self):
        try:
            result = self.ui_controller.run_git("rev-parse", "HEAD")
            return result.strip()
        except Exception as e:
            self.ui_controller.ansi_renderer.insert_ansi_text(f"Could not get current commit: {e}\n", "error")
            return ""

    def commit_list_context_menu(self, event):
        """Show context menu for commit list items"""
        try:
            idx = self.listbox.nearest(event.y)
            if idx < 0:
                return

            # Select the item under the mouse
            self.listbox.selection_clear(0, END)
            self.listbox.selection_set(idx)

            commit_line = self.listbox.get(idx)
            if not commit_line:
                return

            commit_hash = commit_line.split(" - ")[0]

            # Create context menu
            menu = Menu(self, tearoff=0)
            menu.add_command(label="View Details",
                             command=lambda: self.ui_controller.show_commit_details(commit_hash))
            menu.add_command(label="Copy Hash",
                             command=lambda: self.copy_to_clipboard(commit_hash))
            menu.add_command(label="Checkout This Commit",
                             command=lambda: self.ui_controller.checkout_branch(commit_hash))

            # Display the menu
            menu.post(event.x_root, event.y_root)

        except Exception as e:
            print(f"[CommitListView] Context menu error: {e}")

    def copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        if self.ui_controller and self.ui_controller.main_window:
            self.ui_controller.main_window.clipboard_clear()
            self.ui_controller.main_window.clipboard_append(text)

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
            text_widget.configure(state=DISABLED)
            text_widget.pack(fill="both", expand=True)
        except subprocess.CalledProcessError as e:
            error_window = Toplevel()
            error_window.title("Error")
            Label(
                error_window, text=f"Failed to fetch commit details: {e.output}"
            ).pack(pady=20, padx=20)

    def create_branch_at_commit(self, commit_hash):
        from tkinter import simpledialog
        branch_name = simpledialog.askstring("Create Branch", "Enter new branch name:")
        if branch_name:
            self.ui_controller.execute_command(f"branch {branch_name} {commit_hash}")
            if hasattr(self.ui_controller, 'branch_menu_manager'):
                self.ui_controller.branch_menu_manager.populate_branch_menu()

    @property
    def yview(self):
        return self.listbox.yview

    def config(self, **kwargs):
        self.listbox.configure(**kwargs)

    def bind(self, sequence=None, func=None, add=None):
        self.listbox.bind(sequence, func, add=add)

    def get(self, index):
        return self.listbox.get(index)

    def delete(self, first, last=None):
        return self.listbox.delete(first, last)

    def insert(self, index, element):
        return self.listbox.insert(index, element)

    def size(self):
        return self.listbox.size()

    def curselection(self):
        return self.listbox.curselection()

    def selection_set(self, first, last=None):
        return self.listbox.selection_set(first, last)

    def selection_clear(self, first, last=None):
        return self.listbox.selection_clear(first, last)

    def see(self, index):
        return self.listbox.see(index)

    def itemconfig(self, index, cnf=None, **kw):
        return self.listbox.itemconfig(index, cnf, **kw)

    def nearest(self, y):
        return self.listbox.nearest(y)
