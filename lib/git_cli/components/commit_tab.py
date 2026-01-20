from tkinter import Frame, Label, Button, Text, LabelFrame, Listbox, END, WORD, Scrollbar, LEFT, RIGHT, Y, BOTH


class CommitTab(Frame):
    """
    Tab for committing changes to the repository.
    Shows a list of changed files and allows entering a commit message.
    """

    def __init__(self, parent, ui_controller=None):
        super().__init__(parent)
        self.parent = parent
        self.ui_controller = ui_controller
        self._controller_attached = False
        self._ui_initialized = False
        self.git_window = None  # si es necesario puedes recibirlo tambiÃ©n como parÃ¡metro
        self.setup_commit_tab()

    def attach_controller(self, ui_controller):
        self.ui_controller = ui_controller
        self._controller_attached = True
        if not getattr(self, "_ui_initialized", False):
            self.setup_commit_tab()

    def setup_commit_tab(self):
        """Set up the commit tab UI components"""
        # Main container frame
        container = Frame(self.parent)
        container.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # Changed files section
        self.changed_files_frame = LabelFrame(container, text="Changed Files")
        self.changed_files_frame.pack(fill=BOTH, expand=False, padx=5, pady=5)

        # Changed files list with scrollbar
        changed_files_container = Frame(self.changed_files_frame)
        changed_files_container.pack(fill=BOTH, expand=True, padx=5, pady=5)

        scrollbar = Scrollbar(changed_files_container)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.changed_files = Listbox(
            changed_files_container,
            selectmode="extended",
            background="#1E1E1E",
            foreground="#D4D4D4",
            selectforeground="#FFFFFF",
            height=5,
            yscrollcommand=scrollbar.set
        )
        self.changed_files.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.configure(command=self.changed_files.yview)

        # Commit message section
        self.commit_message_frame = LabelFrame(container, text="Commit Message")
        self.commit_message_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # Commit message text entry
        self.commit_message = Text(
            self.commit_message_frame,
            wrap=WORD,
            background="#1E1E1E",
            foreground="#D4D4D4",
            height=10
        )
        self.commit_message.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # Add placeholder text
        self.commit_message.insert("1.0", "Enter commit message here...")
        self.commit_message.bind("<FocusIn>", self._clear_placeholder)
        self.commit_message.bind("<FocusOut>", self._add_placeholder_if_empty)

        # Commit buttons
        buttons_frame = Frame(container)
        buttons_frame.pack(fill=BOTH, expand=False, padx=5, pady=5)

        # Button to commit changes
        self.commit_button = Button(
            buttons_frame,
            text="Commit",
            command=self.ui_controller.commit_changes
        )
        self.commit_button.pack(side=LEFT, padx=2)

        # Button to commit and push
        self.commit_push_button = Button(
            buttons_frame,
            text="Commit & Push",
            command=self.ui_controller.commit_and_push
        )
        self.commit_push_button.pack(side=LEFT, padx=2)

        # Button to amend last commit
        self.amend_button = Button(
            buttons_frame,
            text="Amend Last Commit",
            command=self.ui_controller.amend_last_commit
        )
        self.amend_button.pack(side=LEFT, padx=2)

        self._ui_initialized = True

    def _clear_placeholder(self, event):
        """Clear placeholder text when the commit message field is focused"""
        if self.commit_message.get("1.0", END).strip() == "Enter commit message here...":
            self.commit_message.delete("1.0", END)

    def _add_placeholder_if_empty(self, event):
        """Add placeholder text when the commit message field is empty and loses focus"""
        if not self.commit_message.get("1.0", END).strip():
            self.commit_message.delete("1.0", END)
            self.commit_message.insert("1.0", "Enter commit message here...")

    def get_commit_message(self):
        """
        Get the current commit message.

        Returns:
            str: The commit message text
        """
        message = self.commit_message.get("1.0", END).strip()

        # Don't return the placeholder text
        if message == "Enter commit message here...":
            return ""

        return message

    def clear_commit_message(self):
        """Clear the commit message field and reset to placeholder"""
        self.commit_message.delete("1.0", END)
        self.commit_message.insert("1.0", "Enter commit message here...")

    def update_changed_files(self, files):
        """
        Update the list of changed files.

        Args:
            files: List of changed file paths
        """
        self.changed_files.delete(0, END)
        for file in files:
            self.changed_files.insert(END, file)
