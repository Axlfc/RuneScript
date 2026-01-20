from tkinter import Frame, Button, Entry, END


class CommandEntryView:
    """
    Component that manages the command entry and common git buttons.
    """

    def __init__(self, parent, git_window):
        self.git_window = git_window
        self.parent = parent

        # Container for buttons + entry
        self.frame = Frame(self.parent)
        self.frame.pack(fill="x", expand=False)

        # Git command buttons
        button_defs = [
            ("ðŸ’¾ Commit", "commit"),
            ("â¬†ï¸ Push", "push"),
            ("â¬‡ï¸ Pull", "pull"),
            ("ðŸ”„ Fetch", "fetch"),
        ]

        # Common button styling
        button_style = {
            "bg": "#f0f0f0",
            "fg": "#000000",
            "relief": "raised",
            "padx": 10,
            "pady": 5,
            "borderwidth": 2
        }

        for label, command in button_defs:
            btn = Button(
                self.frame,
                text=label,
                command=lambda c=command: self.git_window.execute_command(c),
                **button_style
            )
            btn.pack(side="left", padx=2, pady=2)

        # Entry widget
        self.entry = Entry(self.frame, width=80)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.focus()

        self.entry.bind("<Return>", self.run_command)
        self.entry.bind("<Up>", self.navigate_history)
        self.entry.bind("<Down>", self.navigate_history)

    def run_command(self, event=None):
        cmd = self.entry.get().strip()
        if cmd:
            self.git_window.execute_command(cmd)
        return "break"

    def clear_entry(self):
        """Clear the command entry field."""
        self.entry.delete(0, END)
        # Give focus back to the entry
        self.entry.focus_set()

    def navigate_history(self, event):
        if self.git_window.command_history:
            if event.keysym == "Up":
                self.git_window.history_pointer[0] = max(0, self.git_window.history_pointer[0] - 1)
            elif event.keysym == "Down":
                self.git_window.history_pointer[0] = min(len(self.git_window.command_history), self.git_window.history_pointer[0] + 1)
            command = (
                self.git_window.command_history[self.git_window.history_pointer[0]]
                if self.git_window.history_pointer[0] < len(self.git_window.command_history)
                else ""
            )
            self.entry.delete(0, END)
            self.entry.insert(0, command)
