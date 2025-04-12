from tkinter import TclError, END

from lib.git_cli.components.commit_list import CommitListView


class UIController:
    """
    UI Controller that manages UI state and handles user interactions.
    Acts as a bridge between the UI components and the services.
    """

    def __init__(self, git_service, main_window, output_text, event_bus):
        self.main_window = main_window
        self.git_service = git_service
        self.event_bus = event_bus

        # UI component references - will be set by GitWindow
        self.current_branch = None
        self.console_tab = None
        self.diff_tab = None
        self.staging_tab = None
        self.commit_tab = None
        self.history_tab = None
        self.status_bar = None
        self.notebook = None
        self.ansi_renderer = None
        self.commit_list_view = None

        # Register event handlers
        self._register_event_handlers()

    def diagnostics(self):
        print("\n[Diagnostics] Running UI initialization health check...")

        components = {
            "console_tab": self.console_tab,
            "diff_tab": self.diff_tab,
            "staging_tab": self.staging_tab,
            "commit_tab": self.commit_tab,
            "history_tab": self.history_tab,
            "status_bar": self.status_bar,
            "notebook": self.notebook,
            "ansi_renderer": self.ansi_renderer,
        }

        for name, component in components.items():
            if component is None:
                print(f"❌ {name} is NOT initialized")
            else:
                print(f"✅ {name} is OK")

        if self.staging_tab and not getattr(self.staging_tab, "_ui_initialized", False):
            print("⚠️  staging_tab exists but is NOT fully initialized")

        if self.history_tab and not getattr(self.history_tab, "_ui_initialized", False):
            print("⚠️  history_tab exists but is NOT fully initialized")

        if hasattr(self, "commit_list_view") and not isinstance(self.commit_list_view, CommitListView):
            print(f"⚠️  commit_list_view is misconfigured (type: {type(self.commit_list_view)})")

        if not self.current_branch:
            print("⚠️  current_branch not set")
        else:
            print(f"📌 Current branch: {self.current_branch}")

        print("[Diagnostics] Done.\n")

    def run_git(self, *args):
        return self.git_service.command_runner.git_executor.run_git(*args, repo_dir=self.git_service.repo_dir)

    def run_git_stdout(self, *args):
        stdout, _, _ = self.run_git(*args)
        return stdout

    def set_ui_components(self, **components):
        """Set references to UI components with type validation"""
        for name, component in components.items():
            if name == "commit_list_view" and not isinstance(component, CommitListView):
                print(f"Warning: commit_list_view expected CommitListView type, got {type(component)}")
                # You could either skip this assignment or handle it differently
                continue
            setattr(self, name, component)

    def add_selected_text_to_git_staging(self):
        """Add selected files from console text to staging"""
        try:
            selected_text = self.console_tab.output_text.get("sel.first", "sel.last")
            if selected_text:
                # Parse the selected text to identify files
                files = [line.strip() for line in selected_text.split('\n') if line.strip()]
                self.git_service.stage_files(files)
        except TclError:
            pass  # No text selected

    def unstage_selected_text(self):
        """Unstage selected files from console text"""
        try:
            selected_text = self.console_tab.output_text.get("sel.first", "sel.last")
            if selected_text:
                # Parse the selected text to identify files
                files = [line.strip() for line in selected_text.split('\n') if line.strip()]
                self.git_service.unstage_files(files)
        except TclError:
            pass  # No text selected

    def show_git_diff(self):
        """Show git diff for selected files in console"""
        try:
            selected_text = self.console_tab.output_text.get("sel.first", "sel.last")
            if selected_text:
                # Parse the selected text to identify files
                files = [line.strip() for line in selected_text.split('\n') if line.strip()]
                if files:
                    self.view_file_diff(files[0])
        except TclError:
            pass  # No text selected

    def _register_event_handlers(self):
        self.event_bus.subscribe("git.status.updated", self._update_status_bar)
        self.event_bus.subscribe("git.staging.updated", self._update_staging_view)
        self.event_bus.subscribe("git.command.executed", self._on_command_executed)
        self.event_bus.subscribe("git.commit.created", self.refresh_commit_history)
        self.event_bus.subscribe("git.branch.changed", self.refresh_commit_history)
        self.event_bus.subscribe("git.status.changed", self.refresh_staging_view)

    def _refresh_commit_list(self, data=None):
        """Refresh the commit list if available and valid"""
        if not hasattr(self, "commit_list_view") or self.commit_list_view is None:
            print("Warning: commit_list_view attribute not found")
            return

        try:
            self.commit_list_view.update_commit_list()
        except Exception as e:
            print(f"Error updating commit list: {e}")

    def _update_status_bar(self, data):
        """Update the status bar with the given message"""
        if self.status_bar and "message" in data:
            self.status_bar.config(text=data["message"])

    def refresh_commit_history(self, *args):
        """Refresh both the commit list view and history tab"""
        # Update commit list if available
        if hasattr(self, "commit_list_view") and self.commit_list_view is not None:
            try:
                self.commit_list_view.update_commit_list()
            except Exception as e:
                print(f"Error updating commit list: {e}")

        # Update history tab if available
        if self.history_tab and hasattr(self.history_tab, 'load_commits'):
            try:
                self.history_tab.load_commits()
            except Exception as e:
                print(f"Error loading commits in history tab: {e}")

    def set_current_branch(self, branch):
        self.current_branch = branch

    def get_commits_for_selected_branch(self, branch_name=None):
        if branch_name is None:
            branch_name = self.current_branch

        #print("[DEBUG] Running raw git log...")
        #out = self.run_git_stdout("log", "--oneline", "redgreenrefactor")
        #print(out)

        print(f"[UIController] Getting commits for branch: {branch_name}")
        result = self.git_service.get_commits_for_branch(branch_name)
        print(f"[UIController] Retrieved {len(result)} commits")
        return result

    def refresh_staging_view(self, *_):
        self.git_service.refresh_staging_view()

    def _update_staging_view(self, data=None):
        if not self.staging_tab or not getattr(self.staging_tab, "_ui_initialized", False):
            print("[UIController] StagingTab not initialized yet")
            return
        elif not self.staging_tab:
            print("[UIController] ERROR: staging_tab is None during publish")
        if not hasattr(self.staging_tab, "staged_files"):
            print("[UIController] staged_files Listbox missing")
            return


        # Clear the lists first
        self.staging_tab.staged_files.delete(0, END)
        self.staging_tab.unstaged_files.delete(0, END)

        print(
            f"Updating staging tab with {len(data.get('staged_files', []))} staged and {len(data.get('unstaged_files', []))} unstaged files.")


        # Update with the data from GitService
        for file in data.get("staged_files", []):
            self.staging_tab.staged_files.insert(END, file)

        for file in data.get("unstaged_files", []):
            self.staging_tab.unstaged_files.insert(END, file)

    def _on_command_executed(self, data):
        """Handle command execution events"""
        # For now, just making sure the output text widget is scrolled to the end
        if self.console_tab and self.console_tab.output_text:
            self.console_tab.output_text.see(END)

    # Command handling methods
    def execute_command(self, command):
        """Execute a Git command"""
        if self.console_tab and self.console_tab.output_text:
            self.git_service.execute_command(command, self.console_tab.output_text)

            # Clear the command entry
            if hasattr(self, 'command_entry_view') and self.command_entry_view.entry:
                self.command_entry_view.entry.delete(0, END)

            # If this is a staging-related command, refresh the staging view
            if any(cmd in command for cmd in ["add", "reset", "checkout --", "rm"]):
                self.refresh_staging_view()

    # File operations
    def stage_selected_file(self, event=None):
        """Stage the selected file in the staging tab"""
        if not self.staging_tab:
            return

        selection = self.staging_tab.get_selected_unstaged_files()
        if selection:
            self.git_service.stage_files(selection)

    def unstage_selected_file(self, event=None):
        """Unstage the selected file in the staging tab"""
        if not self.staging_tab:
            return

        selection = self.staging_tab.get_selected_staged_files()
        if selection:
            self.git_service.unstage_files(selection)

    def stage_all_files(self):
        """Stage all changed files"""
        self.git_service.stage_all_files()

    def unstage_all_files(self):
        """Unstage all files"""
        self.git_service.unstage_all_files()

    def discard_selected_changes(self):
        """Discard changes in the selected files"""
        if not self.staging_tab:
            return

        selection = self.staging_tab.get_selected_unstaged_files()
        if selection:
            self.git_service.discard_changes(selection)

    def commit_changes(self, message=None):
        """Commit staged changes"""
        if not self.commit_tab:
            return

        if message is None:
            message = self.commit_tab.get_commit_message()

        if message:
            success = self.git_service.commit(message)
            if success:
                self.commit_tab.clear_commit_message()

    def commit_and_push(self):
        """Commit staged changes and push to remote"""
        message = self.commit_tab.get_commit_message() if self.commit_tab else None
        if message:
            success = self.git_service.commit(message)
            if success:
                self.commit_tab.clear_commit_message()
                self.git_service.push()

    def amend_last_commit(self):
        """Amend the last commit"""
        message = self.commit_tab.get_commit_message() if self.commit_tab else None
        if message:
            success = self.git_service.commit(message, amend=True)
            if success:
                self.commit_tab.clear_commit_message()

    # Diff and history methods
    def view_file_diff(self, file_path, mode="Working Directory"):
        """Show the diff for a file in the diff tab"""
        if not self.diff_tab or not self.notebook:
            return

        # Select the diff tab
        for i, tab_frame in enumerate(self.notebook.tabs()):
            if tab_frame == self.diff_tab.frame:
                self.notebook.select(i)
                break

        # Update the diff tab with the selected file
        self.diff_tab.selected_file.set(file_path)
        self.diff_tab.diff_mode.set(mode)
        self.diff_tab.refresh_diff()

    def refresh_branches(self):
        """Refresh the branch list in the history tab"""
        if self.history_tab:
            branches = self.git_service.get_branches()
            if branches:
                self.history_tab.update_branch_list(branches)
                # Make sure a branch is selected
                if not self.current_branch and self.git_service.current_branch:
                    self.set_current_branch(self.git_service.current_branch)

    def create_new_branch(self, name=None):
        """Create a new branch"""
        if not name and self.history_tab:
            name = self.history_tab.get_new_branch_name()

        if name:
            self.git_service.create_branch(name)
            self.refresh_branches()

    def checkout_branch(self, name):
        """Checkout a branch"""
        if name:
            self.git_service.checkout_branch(name)

    def get_commit_details(self, commit_hash):
        return self.git_service.get_commit_details(commit_hash)

    def show_commit_details(self, commit_hash):
        """Show details for a specific commit"""
        if commit_hash and self.history_tab:
            details = self.get_commit_details(commit_hash)
            if details:
                self.history_tab.display_commit_details(details)

    # Clipboard operations
    def copy_selected_text(self):
        """Copy selected text to clipboard"""
        if not self.console_tab or not self.main_window:
            return

        try:
            selected_text = self.console_tab.output_text.get("sel.first", "sel.last")
            self.main_window.clipboard_clear()
            self.main_window.clipboard_append(selected_text)
        except TclError:
            pass  # No text selected

    def clear_console(self):
        """Clear the console output"""
        if self.console_tab and self.console_tab.output_text:
            self.console_tab.output_text.delete("1.0", END)