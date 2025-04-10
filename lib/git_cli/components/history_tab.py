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
        self.placeholder = Label(self, text="⏳ Loading history tab...")
        self.placeholder.pack(expand=True)

        if self._controller_attached:
            self.setup_history_tab()

    def attach_controller(self, ui_controller):
        self.ui_controller = ui_controller
        self._controller_attached = True

        if not self._ui_initialized:
            self.setup_history_tab()

    def refresh_branches(self):
        if not self._ui_initialized:
            print("[HistoryTab] Skipping refresh_branches because UI is not initialized yet")
            return

        if self.ui_controller:
            self.ui_controller.refresh_branches()
        else:
            print("[HistoryTab] Controller not set for refresh_branches")

    def load_commits(self, commits=None):
        print(f"[HistoryTab] Loading {len(commits)} commits")

        if not self._ui_initialized:
            print("[HistoryTab] Skipping load_commits because UI is not initialized")
            return

        self.commit_listbox.delete(0, END)
        if not commits:
            commits = self.ui_controller.get_commits_for_selected_branch()

        for c in commits:
            self.commit_listbox.insert(END, f"{c['hash']} - {c['message']}")

    def show_commit_details(self, event=None):
        if not self._ui_initialized or not hasattr(self, 'commit_listbox'):
            return

        selection = self.commit_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        commit_hash = self.commit_listbox.get(idx).split(" - ")[0]

        details = self.ui_controller.get_commit_details(commit_hash)
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", END)
        self.detail_text.insert("1.0", details)
        self.detail_text.config(state="disabled")

    def display_commit_details(self, commit_info: dict):
        if not hasattr(self, "detail_text"):
            print("Warning: detail_text widget not initialized.")
            return

        self.detail_text.config(state=NORMAL)
        self.detail_text.delete("1.0", END)

        message = commit_info.get("message", [])
        if isinstance(message, list):
            joined_message = "\n".join(message)
            self.ui_controller.ansi_renderer.apply_ansi_styles(self.detail_text, joined_message)
        else:
            self.detail_text.insert(END, "[Error: Invalid commit message format]")

        self.detail_text.config(state=DISABLED)

    def update_branch_list(self, branches):
        try:
            from lib.git_cli.core.repository import Repository
            repo = Repository(self.ui_controller.git_service.repo_dir)
            current_branch = repo.get_current_branch()
            print(f"[HistoryTab] Current branch: {current_branch}")
        except Exception as e:
            print(f"[HistoryTab] Error getting current branch: {e}")

    def setup_history_tab(self):
        if self._ui_initialized:
            return
        if not self._controller_attached or not self.ui_controller:
            print("[HistoryTab] Controller not attached, skipping setup.")
            return

        # Limpia placeholder
        if hasattr(self, 'placeholder'):
            self.placeholder.destroy()

        # === Sección de ramas ===
        branch_frame = LabelFrame(self, text="Branch")
        branch_frame.pack(fill="x", padx=10, pady=(10, 5))

        self.branch_dropdown = Listbox(branch_frame, height=5, exportselection=False)
        self.branch_dropdown.pack(side=LEFT, fill="x", expand=True, padx=5, pady=5)
        self.branch_dropdown.bind("<<ListboxSelect>>", self.on_branch_selected)

        Button(branch_frame, text="Refresh", command=self.refresh_branches).pack(side=LEFT, padx=5, pady=5)

        # === Sección de commits ===
        commit_frame = LabelFrame(self, text="Commits")
        commit_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.commit_listbox = Listbox(commit_frame, exportselection=False)
        self.commit_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        self.commit_listbox.bind("<Double-Button-1>", self.show_commit_details)

        scrollbar = Scrollbar(commit_frame, orient="vertical", command=self.commit_listbox.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.commit_listbox.config(yscrollcommand=scrollbar.set)

        # === Detalles ===
        detail_frame = LabelFrame(self, text="Details")
        detail_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.detail_text = Text(detail_frame, wrap="word", height=10, state="disabled")
        self.detail_text.pack(fill="both", expand=True)

        self._ui_initialized = True
        print("[HistoryTab] UI initialized")

    def on_branch_selected(self, event=None):
        if not self._ui_initialized:
            return

        selection = self.branch_dropdown.curselection()
        if not selection:
            return

        index = selection[0]
        branch_name = self.branch_dropdown.get(index)

        self.ui_controller.set_current_branch(branch_name)
        self.load_commits()