from tkinter import LabelFrame, Button, Scrollbar, END, Toplevel
from tkinter.ttk import Combobox, Treeview

from lib.git_cli.core.repository import Repository
from src.views.tk_utils import *


class HistoryTab:
    def __init__(self, parent, git_window):
        self.parent = parent
        self.git_window = git_window
        self.setup_history_tab()

    def refresh_branches(self):
        repo = Repository(self.git_window.repo_dir)
        branches = repo.get_branches()
        self.branch_dropdown['values'] = branches

        current_branch = repo.get_current_branch()
        if current_branch and current_branch in branches:
            self.branch_var.set(current_branch)
        elif branches:
            self.branch_var.set(branches[0])
        self.load_commits()

    def load_commits(self):
        print("Loading commits...")  # Debug
        output, _, _ = self.git_window.run_git("log", "--pretty=format:%h%x09%an%x09%ad%x09%s", "--date=short")
        # print(f"Raw git log output:\n{output}")  # Debug

        self.commits_tree.delete(*self.commits_tree.get_children())

        for line in output.splitlines():
            parts = line.split("\t")
            if len(parts) == 4:
                self.commits_tree.insert("", END, values=parts)
            else:
                print(f"Malformed line skipped: {line}")  # Debug

    def show_commit_details(self, event=None):
        selected = self.commits_tree.focus()
        if not selected:
            return

        values = self.commits_tree.item(selected, "values")
        if not values:
            return

        commit_hash = values[0]
        output, _, _ = self.git_window.run_git("show", "--color", commit_hash)

        detail_window = Toplevel(self.parent)
        detail_window.title(f"Details for commit {commit_hash}")
        detail_window.geometry("800x600")

        text_widget = Text(detail_window, wrap="word", font=my_font)
        text_widget.pack(fill="both", expand=True)

        self.git_window.ansi_renderer.define_ansi_tags(text_widget)
        self.git_window.ansi_renderer.apply_ansi_styles(text_widget, output)

        text_widget.config(state="disabled")

    def setup_history_tab(self):
        # Branch selection frame
        branch_frame = LabelFrame(self.parent, text="Branch")
        branch_frame.pack(fill="x", expand=False, padx=5, pady=5)

        # Branch selection dropdown
        self.branch_var = StringVar()
        self.branch_dropdown = Combobox(branch_frame, textvariable=self.branch_var)
        self.branch_dropdown.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.branch_dropdown.bind("<<ComboboxSelected>>", self.git_window.on_branch_selected)
        Button(branch_frame, text="Refresh", command=self.git_window.refresh_branches).pack(side="left", padx=5, pady=5)
        Button(branch_frame, text="New Branch", command=self.git_window.create_new_branch).pack(side="left", padx=5, pady=5)

        # Commit history view
        history_content = LabelFrame(self.parent, text="Commit History")
        history_content.pack(fill="both", expand=True, padx=5, pady=5)

        # Commits list with columns
        columns = ("hash", "author", "date", "message")
        self.commits_tree = Treeview(
            history_content, 
            columns=columns, 
            show="headings", 
            selectmode="browse"
        )

        # Configure columns
        self.commits_tree.heading("hash", text="Commit")
        self.commits_tree.heading("author", text="Author")
        self.commits_tree.heading("date", text="Date")
        self.commits_tree.heading("message", text="Message")
        self.commits_tree.column("hash", width=80)
        self.commits_tree.column("author", width=120)
        self.commits_tree.column("date", width=120)
        self.commits_tree.column("message", width=400)

        # Add scrollbars
        history_scrollbar_y = Scrollbar(history_content, orient="vertical", command=self.commits_tree.yview)
        self.commits_tree.configure(yscrollcommand=history_scrollbar_y.set)
        history_scrollbar_x = Scrollbar(history_content, orient="horizontal", command=self.commits_tree.xview)
        self.commits_tree.configure(xscrollcommand=history_scrollbar_x.set)

        # Arrange tree and scrollbars
        self.commits_tree.pack(side="left", fill="both", expand=True)
        history_scrollbar_y.pack(side="right", fill="y")
        history_scrollbar_x.pack(side="bottom", fill="x")

        # Bind event for displaying commit details
        self.commits_tree.bind("<Double-1>", self.git_window.show_commit_details)
        self.load_commits()
