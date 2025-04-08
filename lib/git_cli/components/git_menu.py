from tkinter import Menu


class GitMenuManager:
    def __init__(self, menubar, git_window):
        self.menubar = menubar
        self.git_window = git_window
        self.setup_git_menu()

    def setup_git_menu(self):
        self.git_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Git", menu=self.git_menu)
        git_icons = {
            "status": "📊",
            "add": "➕",
            "commit": "💾",
            "push": "⬆️",
            "pull": "⬇️",
            "fetch": "🔄",
            "merge": "🔀",
            "branch": "🌿",
            "checkout": "✨",
            "reset": "⏮️",
            "stash": "📦",
        }
        for command, icon in git_icons.items():
            self.git_menu.add_command(
                label=f"{icon} {command.capitalize()}",
                command=lambda c=command: self.git_window.execute_command(c)
            )

    def set_user_name(self):
        """Dialog to set Git user name."""
        from tkinter import simpledialog
        name = simpledialog.askstring("Git Config", "Enter your name:")
        if name:
            self.git_window.execute_command(f'config user.name "{name}"')

    def set_user_email(self):
        """Dialog to set Git user email."""
        from tkinter import simpledialog
        email = simpledialog.askstring("Git Config", "Enter your email:")
        if email:
            self.git_window.execute_command(f'config user.email "{email}"')