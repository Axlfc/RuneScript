# latest version
import os

import threading
from pathlib import Path
from tkinter import *
from tkinter import scrolledtext, Menu, Frame, Button, Entry, Label, Toplevel, Listbox, Text, SUNKEN, END, W
from tkinter.ttk import Notebook

from lib.git_cli.app import Application
from lib.git_cli.components.ansi_renderer import AnsiRenderer
from lib.git_cli.components.commit_tab import CommitTab
from lib.git_cli.components.git_menu import GitMenuManager
from lib.git_cli.components.branch_menu import BranchMenuManager
from lib.git_cli.components.command_entry import CommandEntryView
from lib.git_cli.components.commit_list import CommitListView
from lib.git_cli.components.console_tab import ConsoleTab
from lib.git_cli.components.staging_tab import StagingTab
from lib.git_cli.components.history_tab import HistoryTab
from lib.git_cli.components.diff_tab import DiffTab
from lib.git_cli.ui.tab_manager import TabManager
from src.views.tk_utils import my_font


class GitWindow:
    """
    Main application window that manages the UI components.
    Delegates business logic to the Application and UIController classes.
    """

    def __init__(self, repo_dir=None):
        self.app = Application(repo_dir=repo_dir)
        self.create_window()
        self.setup_ui()

        self.tab_manager = TabManager(self.notebook)

        # Fase 1: Crear solo el ConsoleTab (sin controller)
        self.console_tab = self.tab_manager.add_tab(ConsoleTab, name="Console")

        # Fase 2: Inicializar app con output_text (esto crea el UIController)
        self.app.initialize_with_ui(self.terminal_window, self.console_tab.output_text)

        # Fase 3: Crear el resto de tabs PASÁNDOLE el ui_controller
        self.diff_tab = self.tab_manager.add_tab(DiffTab, self.app.ui_controller, name="Diff")
        self.staging_tab = self.tab_manager.add_tab(StagingTab, self.app.ui_controller, name="Staging")
        self.commit_tab = self.tab_manager.add_tab(CommitTab, self.app.ui_controller, name="Commit")
        self.history_tab = self.tab_manager.add_tab(HistoryTab, self.app.ui_controller, name="History")

        # Adjuntar controller a los tabs manualmente
        self.history_tab.attach_controller(self.app.ui_controller)
        self.staging_tab.attach_controller(self.app.ui_controller)
        self.commit_tab.attach_controller(self.app.ui_controller)

        # Fase 4: Asociar componentes
        self.app.ui_controller.set_ui_components(
            console_tab=self.console_tab,
            diff_tab=self.diff_tab,
            staging_tab=self.staging_tab,
            commit_tab=self.commit_tab,
            history_tab=self.history_tab,
            status_bar=self.status_bar,
            notebook=self.notebook
        )

        # Fase 5: Adjuntar controlador a console_tab (de nuevo por seguridad)
        self.console_tab.attach_controller(self.app.ui_controller)

        # Fase 6: Configurar componentes
        self.setup_components()

        # ✅ Fase 7: Hacer refresh SOLO AHORA (cuando los componentes ya existen)
        self.app.ui_controller.refresh_commit_history()
        self.app.git_service.refresh_staging_view()

        # Fase 8: Comandos iniciales diferidos hasta render completo
        self.terminal_window.after_idle(self.run_initial_commands)

    def run_initial_commands(self):
        """Run initial Git commands after the UI is fully initialized"""
        if hasattr(self.app, "ui_controller"):
            self.app.ui_controller.diagnostics()

        try:
            self.app.git_service.execute_command("status --porcelain -u", self.console_tab.output_text)
        except Exception as e:
            print(f"[GitWindow] Error running initial Git status: {e}")

        try:
            if hasattr(self.staging_tab, "staged_files"):
                self.app.git_service.refresh_staging_view()
            else:
                print("[GitWindow] Warning: staging_tab not fully initialized.")
        except Exception as e:
            print(f"[GitWindow] Error refreshing staging view: {e}")

        try:
            if hasattr(self.history_tab, "load_commits") and getattr(self.history_tab, "_ui_initialized", False):
                self.history_tab.load_commits()
        except Exception as e:
            print(f"[GitWindow] Error loading commits in history tab: {e}")

    def create_window(self):
        """Create the main application window"""
        self.terminal_window = Toplevel()
        self.terminal_window.title("Git Console")
        self.terminal_window.geometry("600x512")

        # Setup menubar
        self.menubar = Menu(self.terminal_window)
        self.terminal_window.config(menu=self.menubar)

    def setup_ui(self):
        """Only setup frame containers, not tabs or tabs that require controller"""
        self.notebook = Notebook(self.terminal_window)
        self.notebook.pack(fill="both", expand=True)

        # Correct single creation of status_bar here:
        self.status_bar = Label(self.terminal_window, text="Loading...", bd=1, relief=SUNKEN, anchor=W)
        self.status_bar.pack(side="bottom", fill="x")

    def setup_components(self):
        """Set up UI components that need services"""
        # Step 0: Ensure the ANSI renderer is created *before* anything tries to use it
        if not getattr(self.app.ui_controller, "ansi_renderer", None):
            if getattr(self.console_tab, "output_text", None):
                renderer = AnsiRenderer(self.console_tab.output_text)
                self.app.ui_controller.ansi_renderer = renderer
                renderer.define_ansi_tags(self.console_tab.output_text)
                print("[GitWindow] Created and attached ANSI renderer to UI controller")
            else:
                print("[GitWindow] ERROR: No output_text available to bind ANSI renderer")

        # Step 0.5: Reattach controller to console_tab to ensure ANSI rendering is bound
        if hasattr(self.console_tab, "attach_controller") and self.app.ui_controller:
            self.console_tab.attach_controller(self.app.ui_controller)
            print("[GitWindow] Re-attached UI controller to console tab")

        # Step 1: Set the renderer for the diff tab
        try:
            if hasattr(self.diff_tab, 'set_renderer') and callable(self.diff_tab.set_renderer):
                self.diff_tab.set_renderer()

            if hasattr(self.diff_tab, 'refresh_file_list') and callable(self.diff_tab.refresh_file_list):
                self.diff_tab.refresh_file_list()
        except Exception as e:
            print(f"[GitWindow] Error setting up diff tab: {e}")

        # Step 2: Set up command entry view
        try:
            if hasattr(self.console_tab, 'button_frame') and self.console_tab.button_frame.winfo_exists():
                self.command_entry_view = CommandEntryView(self.console_tab.button_frame, self)
                self.app.ui_controller.command_entry_view = self.command_entry_view

                self._bind_event_handlers()
            else:
                print("[GitWindow] Invalid button_frame for CommandEntryView")
        except Exception as e:
            print(f"[GitWindow] Error creating command entry view: {e}")

        # Step 3: Initialize history tab branches
        try:
            if hasattr(self.history_tab, 'refresh_branches') and callable(self.history_tab.refresh_branches):
                self.history_tab.refresh_branches()
        except Exception as e:
            print(f"[GitWindow] Error refreshing branches in history tab: {e}")

    def _bind_event_handlers(self):
        """Bind event handlers for UI components"""
        # Bind command history navigation
        self.command_entry_view.entry.bind("<Up>", self.command_entry_view.navigate_history)
        self.command_entry_view.entry.bind("<Down>", self.command_entry_view.navigate_history)

    # Delegate methods to the UI controller

    def execute_command(self, command):
        """Execute a Git command"""
        self.app.ui_controller.execute_command(command)

    def refresh_staging_view(self):
        """Refresh the staging view"""
        if hasattr(self.staging_tab, "update_staging_data"):
            self.app.git_service.refresh_staging_view()
        else:
            print("[GitWindow] StagingTab not fully initialized.")

    def stage_selected_file(self, event=None):
        """Stage the selected file"""
        self.app.ui_controller.stage_selected_file(event)

    def unstage_selected_file(self, event=None):
        """Unstage the selected file"""
        self.app.ui_controller.unstage_selected_file(event)

    def stage_all_files(self):
        """Stage all files"""
        self.app.ui_controller.stage_all_files()

    def unstage_all_files(self):
        """Unstage all files"""
        self.app.ui_controller.unstage_all_files()

    def discard_selected_changes(self):
        """Discard selected changes"""
        self.app.ui_controller.discard_selected_changes()

    def commit_changes(self):
        """Commit changes"""
        self.app.ui_controller.commit_changes()

    def commit_and_push(self):
        """Commit and push changes"""
        self.app.ui_controller.commit_and_push()

    def amend_last_commit(self):
        """Amend the last commit"""
        self.app.ui_controller.amend_last_commit()

    def on_branch_selected(self, event=None):
        """Handle branch selection"""
        self.history_tab.on_branch_selected(event)

    def refresh_branches(self):
        """Refresh branches"""
        self.app.ui_controller.refresh_branches()

    def create_new_branch(self):
        """Create a new branch"""
        self.app.ui_controller.create_new_branch()

    def show_commit_details(self, event=None):
        """Show commit details"""
        self.history_tab.show_commit_details(event)

    def debounced_refresh_staging_view(self, delay=200):
        """Avoid excessive staging view updates by delaying them"""
        if hasattr(self, "_refresh_staging_job"):
            self.terminal_window.after_cancel(self._refresh_staging_job)
        self._refresh_staging_job = self.terminal_window.after(delay, self.refresh_staging_view)

    def view_file_diff(self, file_path, mode="Working Directory"):
        """Switch to the Diff tab and display the diff for the selected file"""
        self.app.ui_controller.view_file_diff(file_path, mode)

    def clear_console(self):
        """Clear the console output"""
        self.console_tab.output_text.delete("1.0", END)

    def create_tooltip(self, widget, text):
        """Attach a tooltip to a widget"""
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
    repo_path = "/path/to/your/git/repository"  # Replace this
    if os.path.exists(repo_path):
        GitWindow(repo_path)
    else:
        print(f"Repository not found at: {repo_path}")
