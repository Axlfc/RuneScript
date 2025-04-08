import os
import threading
from tkinter import *
from tkinter import scrolledtext, Menu, Frame, Button, Entry, Label, Toplevel, Listbox, Text, SUNKEN, END, W
from tkinter.ttk import Notebook

from lib.git_cli.components.commit_tab import CommitTab
from lib.git_cli.components.git_menu import GitMenuManager
from src.views.tk_utils import my_font

from lib.git_cli.components.ansi_renderer import AnsiRenderer
from lib.git_cli.commands.dispatcher import CommandDispatcher
from lib.git_cli.components.commit_list import CommitListView
from lib.git_cli.components.branch_menu import BranchMenuManager
from lib.git_cli.components.command_entry import CommandEntryView

from lib.git_cli.infra.git_command_runner import GitCommandRunner
from lib.git_cli.infra.git_status_formatter import GitStatusFormatter

from lib.git_cli.components.console_tab import ConsoleTab
from lib.git_cli.components.staging_tab import StagingTab
from lib.git_cli.components.history_tab import HistoryTab
from lib.git_cli.components.diff_tab import DiffTab
from lib.git_cli.ui.tab_manager import TabManager

from lib.git_cli.core.repository import Repository


from pathlib import Path


class GitWindow:
    def __init__(self, repo_dir=None):
        self.repo_dir = Path(repo_dir or os.getcwd())
        self.dispatcher = CommandDispatcher(repo_dir=str(self.repo_dir))
        self.command_history = []
        self.history_pointer = [0]

        self.create_window()

        self.command_runner = GitCommandRunner(self.dispatcher, None, self.repo_dir)
        self.status_formatter = GitStatusFormatter(None, self.repo_dir)

        self.setup_ui()

        # Retrieve tab instances from the tab manager immediately after setup_ui()
        self.console_tab = self.tab_manager.get_tab(ConsoleTab)
        self.diff_tab = self.tab_manager.get_tab(DiffTab)
        self.staging_tab = self.tab_manager.get_tab(StagingTab)
        self.commit_tab = self.tab_manager.get_tab(CommitTab)
        self.history_tab = self.tab_manager.get_tab(HistoryTab)

        # Initialize the ANSI renderer using the output_text widget from ConsoleTab
        self.ansi_renderer = AnsiRenderer(self.console_tab.output_text)
        self.ansi_renderer.define_ansi_tags(self.console_tab.output_text)

        # Set the renderer for other components
        self.command_runner.ansi_renderer = self.ansi_renderer
        self.status_formatter.ansi_renderer = self.ansi_renderer

        # Now, call set_renderer() on the diff tab now that ansi_renderer is available
        # Now, call set_renderer() on the diff tab now that ansi_renderer is available
        self.diff_tab.set_renderer()
        # Refresh the diff tab file list so that the file dropdown is populated
        self.diff_tab.refresh_file_list()

        self.commit_list_view = CommitListView(self.console_tab.commit_frame, self)
        self.command_entry_view = CommandEntryView(self.console_tab.button_frame, self)
        self.git_menu_manager = GitMenuManager(self.menubar, self)
        self.branch_menu_manager = BranchMenuManager(self.menubar, self)

        self.console_tab.setup_context_menu()
        self.console_tab.set_dependencies(self.status_formatter)

        self.console_tab.entry.bind("<Up>", self.command_entry_view.navigate_history)
        self.console_tab.entry.bind("<Down>", self.command_entry_view.navigate_history)

        self.execute_command("status --porcelain -u")
        self.refresh_staging_view()

    def create_window(self):
        self.terminal_window = Toplevel()
        self.terminal_window.title("Git Console")
        self.terminal_window.geometry("600x512")

        # Setup menubar
        self.menubar = Menu(self.terminal_window)
        self.terminal_window.config(menu=self.menubar)

    def setup_ui(self):
        self.notebook = Notebook(self.terminal_window)
        self.notebook.pack(fill="both", expand=True)

        self.tab_manager = TabManager(self.notebook)
        self.tab_manager.add_tab(ConsoleTab, self, name="Console")
        self.tab_manager.add_tab(DiffTab, self, name="Diff")
        self.tab_manager.add_tab(StagingTab, self, name="Staging")
        self.tab_manager.add_tab(CommitTab, self, name="Commit")
        self.tab_manager.add_tab(HistoryTab, self, name="History")

        # Fix assignments here
        self.console_tab = self.tab_manager.get_tab(ConsoleTab)
        self.diff_tab = self.tab_manager.get_tab(DiffTab)
        self.staging_tab = self.tab_manager.get_tab(StagingTab)
        self.commit_tab = self.tab_manager.get_tab(CommitTab)
        self.history_tab = self.tab_manager.get_tab(HistoryTab)

        self.status_bar = Label(self.terminal_window, text="Loading...", bd=1, relief=SUNKEN, anchor=W)
        self.status_bar.pack(side="bottom", fill="x")

    def execute_command(self, command):
        if not command.strip():
            return
        self.command_history.append(command)
        self.history_pointer[0] = len(self.command_history)

        if command == "status --porcelain -u":
            self.status_formatter.format_status(self.console_tab.output_text)
        else:
            threading.Thread(target=self.command_runner.run, args=(command, self.console_tab.output_text), daemon=True).start()

        self.console_tab.entry.delete(0, END)
        self.console_tab.output_text.see(END)

    def run_git(self, *args):
        return self.command_runner.git_executor.run_git(*args, repo_dir=self.repo_dir)

    def add_selected_text_to_git_staging(self):
        selected_text = self.console_tab.output_text.get("sel.first", "sel.last")
        if selected_text:
            self.execute_command(f"add -f {selected_text}")

    def unstage_selected_text(self):
        selected_text = self.console_tab.output_text.get("sel.first", "sel.last")
        if selected_text:
            self.execute_command(f"reset -- {selected_text}")

    def refresh_staging_view(self):
        output, _, _ = self.command_runner.git_executor.run_git("status", "--porcelain", repo_dir=self.repo_dir)
        unstaged = []
        staged = []

        for line in output.splitlines():
            status_code = line[:2]
            file_path = line[3:]

            staged_code = status_code[0]
            unstaged_code = status_code[1]

            if staged_code != ' ' and unstaged_code == ' ':
                # Staged only
                staged.append(file_path)
            elif staged_code == ' ' and unstaged_code != ' ':
                # Unstaged only
                unstaged.append(file_path)
            else:
                # Both staged and unstaged — treat as unstaged for simplicity
                unstaged.append(file_path)

        self.staging_tab.staged_files.delete(0, END)
        self.staging_tab.unstaged_files.delete(0, END)

        for f in staged:
            self.staging_tab.staged_files.insert(END, f)

        for f in unstaged:
            self.staging_tab.unstaged_files.insert(END, f)

    def show_git_diff(self):
        diff_window = Toplevel(self.terminal_window)
        diff_window.title("Git Diff")
        diff_window.geometry("800x600")
        diff_text = Text(diff_window, height=20, width=80, font=my_font)
        diff_text.pack(fill="both", expand=True)
        self.ansi_renderer.define_ansi_tags(diff_text)
        threading.Thread(
            target=self.command_runner.run,
            args=("diff --color", diff_text),
            daemon=True
        ).start()
        diff_text.config(state="disabled")

    def get_output_widget(self):
        return self.console_tab.output_text

    def update_status(self, commit_hash="HEAD"):
        repo = Repository(self.repo_dir)
        branch = repo.get_current_branch()
        if branch:
            self.status_bar.config(text=f"Current branch: {branch}")
        else:
            # fallback to commit hash if detached
            from lib.git_cli.executor import GitExecutor
            short_hash, _, _ = GitExecutor.run_git("rev-parse", "--short", commit_hash, repo_dir=self.repo_dir)
            if short_hash.strip():
                self.status_bar.config(text=f"Current commit: {short_hash.strip()}")
            else:
                self.status_bar.config(text="Error: Invalid identifier")

    def copy_selected_text(self):
        try:
            selected_text = self.console_tab.output_text.get("sel.first", "sel.last")
            self.terminal_window.clipboard_clear()
            self.terminal_window.clipboard_append(selected_text)
        except TclError:
            pass  # No text selected

    def stage_selected_file(self, event=None):
        self.staging_tab.stage_selected_file(event)
        self.debounced_refresh_staging_view()

    def unstage_selected_file(self, event=None):
        self.staging_tab.unstage_selected_file(event)
        self.debounced_refresh_staging_view()

    def stage_all_files(self):
        self.staging_tab.stage_all_files()
        self.debounced_refresh_staging_view()

    def unstage_all_files(self):
        self.staging_tab.unstage_all_files()
        self.debounced_refresh_staging_view()

    def discard_selected_changes(self):
        self.staging_tab.discard_selected_changes()
        self.debounced_refresh_staging_view()

    def commit_changes(self):
        self.staging_tab.commit_changes()
        self.debounced_refresh_staging_view()

    def commit_and_push(self):
        self.staging_tab.commit_and_push()
        self.debounced_refresh_staging_view()

    def amend_last_commit(self):
        self.staging_tab.amend_last_commit()
        self.debounced_refresh_staging_view()

    def on_branch_selected(self, event=None):
        self.history_tab.on_branch_selected(event)

    def refresh_branches(self):
        self.history_tab.refresh_branches()

    def create_new_branch(self):
        self.history_tab.create_new_branch()

    def show_commit_details(self, event=None):
        self.history_tab.show_commit_details(event)

    def debounced_refresh_staging_view(self, delay=200):
        """Evita múltiples actualizaciones consecutivas del staging tab."""
        if hasattr(self, "_refresh_staging_job"):
            self.terminal_window.after_cancel(self._refresh_staging_job)
        self._refresh_staging_job = self.terminal_window.after(delay, self.refresh_staging_view)

    def refresh_diff_view(self):
        if hasattr(self, 'diff_tab'):
            self.diff_tab.refresh_diff()

    def view_file_diff(self, file_path, mode="Working Directory"):
        diff_tab = self.tab_manager.get_tab(DiffTab)
        if diff_tab:
            # Select the diff tab in the notebook
            for i, tab_frame in enumerate(self.tab_manager.tab_frames.values()):
                if tab_frame == self.tab_manager.tab_frames[DiffTab]:
                    self.notebook.select(i)
                    break

            # Set the diff mode and selected file, then refresh diff view
            diff_tab.diff_mode.set(mode)
            diff_tab.selected_file.set(file_path)
            diff_tab.refresh_diff()

    def clear_console(self):
        self.console_tab.output_text.delete("1.0", END)

    def create_tooltip(self, widget, text):
        tooltip = None

        def on_enter(event):
            nonlocal tooltip
            tooltip = Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            label = Label(tooltip, text=text, background="#ffffe0", relief="solid", borderwidth=1)
            label.pack(ipadx=1)

        def on_leave(event):
            nonlocal tooltip
            if tooltip:
                tooltip.destroy()
                tooltip = None

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)


if __name__ == "__main__":
    # Example usage:
    repo_path = "/path/to/your/git/repository"  # Replace with your repository path
    if os.path.exists(repo_path):
        app = GitWindow(repo_path)
    else:
        print(f"Repository not found at: {repo_path}")