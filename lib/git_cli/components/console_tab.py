from tkinter import Button

from src.views.tk_utils import *


class ConsoleTab:
    def __init__(self, parent, git_window):
        self.parent = parent
        self.git_window = git_window
        self.setup_console_tab()

    def setup_console_tab(self):
        # Output text area with scrollbar
        self.output_text = scrolledtext.ScrolledText(
            self.parent,
            height=20,
            width=80,
            font=my_font,
            background="#1E1E1E",
            foreground="#D4D4D4",
            insertbackground="#FFFFFF"
        )
        self.output_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Button frame below output
        self.button_frame = Frame(self.parent)
        self.button_frame.pack(fill="x", expand=False, padx=5, pady=5)

        # Create button frame contents
        self.setup_button_frame()

        # Context menu for output text
        self.setup_context_menu()

        # Commit frame is used by the commit list view
        self.commit_frame = Frame(self.parent)
        self.commit_frame.pack(fill="both", expand=True)

    def setup_button_frame(self):
        # Command entry with prefix label
        command_frame = Frame(self.button_frame)
        command_frame.pack(side="left", fill="x", expand=True)
        Label(command_frame, text="git", font=("Arial", 10, "bold")).pack(side="left", padx=(0, 5))
        self.entry = Entry(
            command_frame,
            width=80,
            background="#1E1E1E",
            foreground="#D4D4D4",
            insertbackground="#FFFFFF"
        )
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.focus()
        self.entry.bind("<Return>", lambda event: self.git_window.execute_command(self.entry.get()))

        # Common command buttons with better styling
        common_commands = [
            {"text": "💾 Commit", "command": "commit", "tooltip": "Commit staged changes"},
            {"text": "⬆️ Push", "command": "push", "tooltip": "Push commits to remote"},
            {"text": "⬇️ Pull", "command": "pull", "tooltip": "Pull changes from remote"},
            {"text": "🔄 Fetch", "command": "fetch", "tooltip": "Fetch from remote"},
            {"text": "📊 Status", "command": "status", "tooltip": "Show repository status"}
        ]
        buttons_frame = Frame(self.button_frame)
        buttons_frame.pack(side="right")
        for cmd in common_commands:
            button = Button(
                buttons_frame,
                text=cmd["text"],
                command=lambda c=cmd["command"]: self.git_window.execute_command(c),
                relief="flat",
                bg="#2D2D30",
                fg="#FFFFFF",
                activebackground="#3E3E42",
                activeforeground="#FFFFFF",
                padx=8,
                pady=4
            )
            button.pack(side="left", padx=2)
            self.git_window.create_tooltip(button, cmd["tooltip"])

    def setup_context_menu(self):
        self.context_menu = Menu(self.output_text, tearoff=0)
        self.output_text.bind(
            "<Button-3>",
            lambda event: self.context_menu.tk_popup(event.x_root, event.y_root)
        )
        self.context_menu.add_command(label="Git Add", command=self.git_window.add_selected_text_to_git_staging)
        self.context_menu.add_command(label="Git Unstage", command=self.git_window.unstage_selected_text)
        self.context_menu.add_command(label="Git Status", command=lambda: self.git_window.status_formatter.format_status(self.output_text))
        self.context_menu.add_command(label="Git Diff", command=self.git_window.show_git_diff)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Copy", command=self.git_window.copy_selected_text)
        self.context_menu.add_command(label="Clear Console", command=self.git_window.clear_console)

    def set_dependencies(self, status_formatter):
        self.status_formatter = status_formatter