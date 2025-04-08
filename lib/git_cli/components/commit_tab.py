from tkinter import Text, Button, LabelFrame, Frame, END
from src.views.tk_utils import *


class CommitTab:
    def __init__(self, parent, git_window):
        """
        Initialize the CommitTab.

        Args:
            parent (tk.Widget): The parent widget (e.g., a notebook tab).
            git_window (GitWindow): Reference to the main GitWindow instance.
        """
        self.parent = parent
        self.git_window = git_window
        self.setup_commit_tab()

    def get_commit_message(self):
        return self.commit_message.get("1.0", END).strip()

    def setup_commit_tab(self):
        """
        Set up the UI components for the CommitTab.
        """
        # Main frame for the commit tab
        commit_frame = LabelFrame(self.parent, text="Commit")
        commit_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Commit message entry
        Label(commit_frame, text="Commit Message:", anchor="w").pack(fill="x", padx=5, pady=2)
        self.commit_message = Text(
            commit_frame,
            height=3,
            width=50,
            background="#1E1E1E",
            foreground="#D4D4D4",
            insertbackground="#FFFFFF"
        )
        self.commit_message.pack(fill="x", expand=False, padx=5, pady=5)

        # Commit buttons
        commit_buttons = Frame(commit_frame)
        commit_buttons.pack(fill="x", expand=False, padx=5, pady=5)

        # Buttons for commit actions
        Button(commit_buttons, text="Commit", command=self.git_window.commit_changes).pack(side="left", padx=2)
        Button(commit_buttons, text="Commit & Push", command=self.git_window.commit_and_push).pack(side="left", padx=2)
        Button(commit_buttons, text="Amend Last Commit", command=self.git_window.amend_last_commit).pack(side="left", padx=2)