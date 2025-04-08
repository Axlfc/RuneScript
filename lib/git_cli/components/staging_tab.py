from tkinter import Listbox, Button, LabelFrame, END
from tkinter.ttk import PanedWindow
from src.views.tk_utils import *


class StagingTab:
    def __init__(self, parent, git_window):
        self.parent = parent
        self.git_window = git_window
        self.setup_staging_tab()
        self.setup_context_menus()

    def setup_staging_tab(self):
        # Split view for unstaged and staged changes
        self.staging_paned = PanedWindow(self.parent, orient="vertical")
        self.staging_paned.pack(fill="both", expand=True, padx=5, pady=5)

        # Unstaged changes frame
        self.unstaged_frame = LabelFrame(self.staging_paned, text="Unstaged Changes")
        self.staging_paned.add(self.unstaged_frame, weight=1)

        # Unstaged files list
        self.unstaged_files = Listbox(
            self.unstaged_frame,
            selectmode="extended",
            background="#1E1E1E",
            foreground="#D4D4D4",
            selectbackground="#264F78",
            selectforeground="#FFFFFF"
        )
        self.unstaged_files.pack(fill="both", expand=True, padx=5, pady=5)
        self.unstaged_files.bind("<Double-1>", self.git_window.stage_selected_file)

        # Unstaged buttons
        unstaged_buttons = Frame(self.unstaged_frame)
        unstaged_buttons.pack(fill="x", expand=False, padx=5, pady=5)
        Button(unstaged_buttons, text="Stage Selected", command=self.git_window.stage_selected_file).pack(side="left", padx=2)
        Button(unstaged_buttons, text="Stage All", command=self.git_window.stage_all_files).pack(side="left", padx=2)
        Button(unstaged_buttons, text="Discard Selected", command=self.git_window.discard_selected_changes).pack(side="left", padx=2)

        # Staged changes frame
        self.staged_frame = LabelFrame(self.staging_paned, text="Staged Changes")
        self.staging_paned.add(self.staged_frame, weight=1)

        # Staged files list
        self.staged_files = Listbox(
            self.staged_frame,
            selectmode="extended",
            background="#1E1E1E",
            foreground="#D4D4D4",
            selectbackground="#264F78",
            selectforeground="#FFFFFF"
        )
        self.staged_files.pack(fill="both", expand=True, padx=5, pady=5)
        self.staged_files.bind("<Double-1>", self.git_window.unstage_selected_file)

        # Staged buttons
        staged_buttons = Frame(self.staged_frame)
        staged_buttons.pack(fill="x", expand=False, padx=5, pady=5)
        Button(staged_buttons, text="Unstage Selected", command=self.git_window.unstage_selected_file).pack(side="left", padx=2)
        Button(staged_buttons, text="Unstage All", command=self.git_window.unstage_all_files).pack(side="left", padx=2)

    def setup_context_menus(self):
        # Create context menu for unstaged files
        self.unstaged_context_menu = Menu(self.unstaged_files, tearoff=0)
        self.unstaged_context_menu.add_command(label="Stage Selected",
                                               command=self.stage_selected_file)
        self.unstaged_context_menu.add_command(label="View Diff",
                                               command=self.view_selected_diff)
        self.unstaged_context_menu.add_separator()
        self.unstaged_context_menu.add_command(label="Discard Changes",
                                               command=self.discard_selected_changes)

        # Create context menu for staged files
        self.staged_context_menu = Menu(self.staged_files, tearoff=0)
        self.staged_context_menu.add_command(label="Unstage Selected",
                                             command=self.unstage_selected_file)
        self.staged_context_menu.add_command(label="View Diff",
                                             command=self.view_selected_diff)

        # Bind context menu to right-click
        self.unstaged_files.bind("<Button-3>", self.show_unstaged_context_menu)
        self.staged_files.bind("<Button-3>", self.show_staged_context_menu)

    def show_unstaged_context_menu(self, event):
        """Display the context menu for unstaged files on right-click."""
        try:
            # Select the item under the cursor
            index = self.unstaged_files.nearest(event.y)
            if index >= 0:
                self.unstaged_files.selection_clear(0, END)
                self.unstaged_files.selection_set(index)
                self.unstaged_files.activate(index)

            # Show the context menu
            self.unstaged_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            # Make sure to release the grab
            self.unstaged_context_menu.grab_release()

    def show_staged_context_menu(self, event):
        """Display the context menu for staged files on right-click."""
        try:
            # Select the item under the cursor
            index = self.staged_files.nearest(event.y)
            if index >= 0:
                self.staged_files.selection_clear(0, END)
                self.staged_files.selection_set(index)
                self.staged_files.activate(index)

            # Show the context menu
            self.staged_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            # Make sure to release the grab
            self.staged_context_menu.grab_release()

    def stage_selected_file(self, event=None):
        """Stage all selected files from the unstaged list."""
        selected_indices = self.unstaged_files.curselection()
        if not selected_indices:
            return

        # Use a copy of the selected items
        selected_files = [self.unstaged_files.get(i) for i in selected_indices]

        for file_path in selected_files:
            self.git_window.execute_command(f"add {file_path}")

        self.git_window.refresh_staging_view()

    def unstage_selected_file(self, event=None):
        """Unstage all selected files from the staged list."""
        selected_indices = self.staged_files.curselection()
        if not selected_indices:
            return

        # Use a copy of the selected items
        selected_files = [self.staged_files.get(i) for i in selected_indices]

        for file_path in selected_files:
            self.git_window.execute_command(f"reset -- {file_path}")

        self.git_window.refresh_staging_view()

    def stage_all_files(self):
        """Stage all files in the unstaged list."""
        all_files = self.unstaged_files.get(0, END)
        for file_path in all_files:
            self.git_window.execute_command(f"add {file_path}")

        self.git_window.refresh_staging_view()

    def unstage_all_files(self):
        """Unstage all files in the staged list."""
        all_files = self.staged_files.get(0, END)
        for file_path in all_files:
            self.git_window.execute_command(f"reset -- {file_path}")

        self.git_window.refresh_staging_view()

    def discard_selected_changes(self):
        """Discard changes for selected files in the unstaged list."""
        selected_indices = self.unstaged_files.curselection()
        if not selected_indices:
            return

        # Use a copy of the selected items
        selected_files = [self.unstaged_files.get(i) for i in selected_indices]

        for file_path in selected_files:
            self.git_window.execute_command(f"checkout -- {file_path}")

        self.git_window.refresh_staging_view()

    def commit_changes(self):
        """Commit staged changes."""
        commit_message = self.git_window.commit_tab.get_commit_message()
        if not commit_message.strip():
            messagebox.showwarning("Commit Error", "Commit message cannot be empty.")
            return False

        self.git_window.execute_command(f'commit -m "{commit_message}"')
        self.git_window.refresh_staging_view()
        return True

    def commit_and_push(self):
        """Commit staged changes and push to the remote repository."""
        if self.commit_changes():
            self.git_window.execute_command("push")

    def amend_last_commit(self):
        """Amend the last commit with staged changes."""
        commit_message = self.git_window.commit_tab.get_commit_message()
        if not commit_message.strip():
            messagebox.showwarning("Commit Error", "Commit message cannot be empty.")
            return

        self.git_window.execute_command(f'commit --amend -m "{commit_message}"')
        self.git_window.refresh_staging_view()

    def view_selected_diff(self):
        selected = self.unstaged_files.curselection()
        if selected:
            file = self.unstaged_files.get(selected[0])
            self.git_window.view_file_diff(file, mode="Working Directory")
        else:
            selected = self.staged_files.curselection()
            if selected:
                file = self.staged_files.get(selected[0])
                self.git_window.view_file_diff(file, mode="Staged Changes")