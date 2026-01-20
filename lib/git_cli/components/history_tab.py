from tkinter import LabelFrame, Button, Scrollbar, END, Toplevel, StringVar, Text, BOTH, NORMAL, DISABLED, Listbox, LEFT, Frame, Label, VERTICAL, RIGHT, Y
from tkinter.ttk import Combobox, Treeview

from lib.git_cli.components.commit_list import CommitListView
from lib.git_cli.core.repository import Repository

from src.views.tk_utils import my_font


class HistoryTab(Frame):
    def __init__(self, parent, ui_controller=None):
        super().__init__(parent)
        self.parent = parent
        self.ui_controller = ui_controller
        self._controller_attached = bool(ui_controller)
        self._ui_initialized = False

        # Placeholder inicial
        self.placeholder = Label(self, text="â³ Loading history tab...")
        self.placeholder.pack(expand=True)

        if self._controller_attached:
            self.setup_history_tab()

    def attach_controller(self, ui_controller):
        self.ui_controller = ui_controller
        self._controller_attached = True

        # If UI is not initialized, do it now
        if not self._ui_initialized:
            self.setup_history_tab()
        # If we already have a commit_list_view, update its controller reference
        elif hasattr(self, 'commit_list_view') and self.commit_list_view is not None:
            self.commit_list_view.controller = ui_controller

    def refresh_branches(self):
        if not self._ui_initialized:
            print("[HistoryTab] Skipping refresh_branches because UI is not initialized yet")
            return

        if self.ui_controller:
            self.ui_controller.refresh_branches()
        else:
            print("[HistoryTab] Controller not set for refresh_branches")

    def load_commits(self, commits=None):
        """Load commits into the commit listbox"""
        if not self._ui_initialized:
            print("[HistoryTab] Skipping load_commits because UI is not initialized")
            return

        self.commit_listbox.delete(0, END)

        # Get commits if not provided
        if commits is None and self.ui_controller and self.ui_controller.git_service:
            try:
                # Add debug to see what's happening
                print("[HistoryTab] Fetching commits for selected branch")

                # Use the current branch if available
                current_branch = getattr(self.ui_controller, 'current_branch', None)
                if current_branch:
                    print(f"[HistoryTab] Using current branch: {current_branch}")
                    commits = self.ui_controller.get_commits_for_selected_branch(current_branch)
                else:
                    print("[HistoryTab] No current branch set, falling back to default")
                    commits = self.ui_controller.get_commits_for_selected_branch()

                print(f"[HistoryTab] Fetched {len(commits) if commits else 0} commits")
            except Exception as e:
                print(f"[HistoryTab] Error getting commits: {e}")
                # Consider displaying this error to the user
                commits = []

        # Ensure commits is at least an empty list to avoid NoneType errors
        commits = commits or []

        print(f"[HistoryTab] Loading {len(commits)} commits")

        # Add commits to listbox
        for c in commits:
            if isinstance(c, dict):
                # Handle dict format
                commit_hash = c.get('hash', '')
                message = c.get('message', '')
                self.commit_listbox.insert(END, f"{commit_hash} - {message}")
            else:
                # Handle string format or other formats
                self.commit_listbox.insert(END, str(c))

    def show_commit_details(self, event=None):
        if not self._ui_initialized or not hasattr(self, 'commit_listbox'):
            return

        selection = self.commit_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        commit_hash = self.commit_listbox.get(idx).split(" - ")[0]

        details = self.ui_controller.get_commit_details(commit_hash)
        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", END)
        self.detail_text.insert("1.0", details)
        self.detail_text.configure(state="disabled")

    def display_commit_details(self, commit_info: dict):
        if not hasattr(self, "detail_text"):
            print("Warning: detail_text widget not initialized.")
            return

        self.detail_text.configure(state=NORMAL)
        self.detail_text.delete("1.0", END)

        message = commit_info.get("message", [])
        if isinstance(message, list):
            joined_message = "\n".join(message)
            self.ui_controller.ansi_renderer.apply_ansi_styles(self.detail_text, joined_message)
        else:
            self.detail_text.insert(END, "[Error: Invalid commit message format]")

        self.detail_text.configure(state=DISABLED)

    def update_branch_list(self, branches):
        """Update the branch dropdown with branches and select current one"""
        if not self._ui_initialized or not hasattr(self, 'branch_dropdown'):
            print("[HistoryTab] branch_dropdown not initialized yet")
            return

        print(f"[HistoryTab] Updating branch list with {len(branches)} branches")

        # Clear existing branches
        self.branch_dropdown.delete(0, END)

        # Get the current branch
        current_branch = None
        if self.ui_controller and hasattr(self.ui_controller, 'current_branch'):
            current_branch = self.ui_controller.current_branch

        # Add all branches to the list with * marking the current one
        for branch in branches:
            display_name = f"* {branch}" if branch == current_branch else f"  {branch}"
            self.branch_dropdown.insert(END, display_name)

        # Try to select the current branch in the list
        if current_branch:
            for i, branch in enumerate(branches):
                if branch == current_branch:
                    self.branch_dropdown.selection_set(i)
                    break

            # Load commits for the current branch
            self.ui_controller.set_current_branch(current_branch)
            self.load_commits()

    def setup_history_tab(self):
        if self._ui_initialized:
            return
        if not self._controller_attached or not self.ui_controller:
            print("[HistoryTab] Controller not attached, skipping setup.")
            return

        # Clear placeholder
        if hasattr(self, 'placeholder'):
            self.placeholder.destroy()

        # === Branch section ===
        branch_frame = LabelFrame(self, text="Branch")
        branch_frame.pack(fill="x", padx=10, pady=(10, 5))

        self.branch_dropdown = Listbox(branch_frame, height=5, exportselection=False)
        self.branch_dropdown.pack(side=LEFT, fill="x", expand=True, padx=5, pady=5)
        self.branch_dropdown.bind("<<ListboxSelect>>", self.on_branch_selected)

        Button(branch_frame, text="Refresh", command=self.refresh_branches).pack(side=LEFT, padx=5, pady=5)

        # === Commit section ===
        commit_frame = LabelFrame(self, text="Commits")
        commit_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Initialize the CommitListView
        try:
            # Create the commit_list_view
            self.commit_list_view = CommitListView(commit_frame, self.ui_controller)
            self.commit_list_view.pack(fill=BOTH, expand=True)

            # IMPORTANT: Store reference to this in the UIController
            if self.ui_controller:
                self.ui_controller.commit_list_view = self.commit_list_view

            # Use the commit_list_view as the listbox for compatibility with existing code
            self.commit_listbox = self.commit_list_view
        except Exception as e:
            print(f"[HistoryTab] Error initializing CommitListView: {e}")
            # Fallback to simple listbox
            self.commit_listbox = Listbox(commit_frame, exportselection=False)
            self.commit_listbox.pack(side=LEFT, fill=BOTH, expand=True)

            scrollbar = Scrollbar(commit_frame, orient="vertical", command=self.commit_listbox.yview)
            scrollbar.pack(side=RIGHT, fill=Y)
            self.commit_listbox.configure(yscrollcommand=scrollbar.set)

            # Bind events
            self.commit_listbox.bind("<Double-Button-1>", self.show_commit_details)
            self.commit_listbox.bind("<Button-3>", self.show_commit_context_menu)

        # === Details section ===
        detail_frame = LabelFrame(self, text="Details")
        detail_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.detail_text = Text(detail_frame, wrap="word", height=10, state="disabled")
        self.detail_text.pack(fill="both", expand=True)

        self._ui_initialized = True
        print("[HistoryTab] UI initialized")

        # Initial data load
        self.refresh_branches()

    def show_commit_context_menu(self, event):
        """Display context menu for commits on right-click"""
        if not hasattr(self.ui_controller, 'commit_list_view') or self.ui_controller.commit_list_view is None:
            return

        try:
            # Use the CommitListView's context menu method
            self.ui_controller.commit_list_view.commit_list_context_menu(event)
        except Exception as e:
            print(f"[HistoryTab] Error showing commit context menu: {e}")

    def on_branch_selected(self, event=None):
        """Handle branch selection from the branch list"""
        if not self._ui_initialized:
            return

        selection = self.branch_dropdown.curselection()
        if not selection:
            return

        index = selection[0]
        branch_display = self.branch_dropdown.get(index)
        # Remove the prefix (* or spaces) to get the actual branch name
        branch_name = branch_display.strip('* ')

        print(f"[HistoryTab] Selected branch: {branch_name}")

        # Update controller with the selected branch
        if self.ui_controller:
            self.ui_controller.set_current_branch(branch_name)

            # Load commits for the selected branch
            try:
                self.load_commits()
            except Exception as e:
                print(f"[HistoryTab] Error loading commits for branch {branch_name}: {e}")
