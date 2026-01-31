# TerminalWindow.py
import os
import subprocess
import tkinter as tk
import customtkinter as ctk
from src.ui.themed_window import ThemedWindow

class TerminalWindow(ThemedWindow):
    def __init__(self, parent=None):
        """Initialize the Terminal window."""
        if parent is None:
            try:
                from src.views.tk_utils import root
                parent = root
            except ImportError:
                pass
        super().__init__(parent)
        self.terminal_window = self # self is the window
        self.title("Terminal")
        self.geometry("600x450")

        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Output text area with scroll
        self.output_text = ctk.CTkTextbox(self.main_container, height=350)
        self.output_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Command history and pointer for navigation
        self.command_history = []
        self.history_pointer = [0]

        # Entry widget for command input
        self.entry = ctk.CTkEntry(self.main_container)
        self.entry.pack(side="bottom", fill="x", padx=5, pady=5)
        self.entry.focus()

        # Key bindings for command execution and history navigation
        self.entry.bind("<Return>", self.execute_command)
        self.entry.bind("<Up>", self.navigate_history)
        self.entry.bind("<Down>", self.navigate_history)

    def execute_command(self, event=None):
        """Execute the command entered in the terminal."""
        command = self.entry.get()
        if command.strip():
            # Add command to history and update history pointer
            self.command_history.append(command)
            self.history_pointer[0] = len(self.command_history)

            # Execute the command and capture output
            try:
                output = subprocess.check_output(
                    command,
                    stderr=subprocess.STDOUT,
                    shell=True,
                    text=True,
                    cwd=os.getcwd())
                # Insert command and its output into the text area
                self.output_text.insert(END, f"{command}\n{output}\n")
            except subprocess.CalledProcessError as e:
                self.output_text.insert(END, f"Error: {e.output}", "error")

            # Clear the entry widget and scroll output to the end
            self.entry.delete(0, END)
            self.output_text.see(END)

    def navigate_history(self, event):
        """Navigate through the command history using arrow keys."""
        if self.command_history:
            if event.keysym == "Up":
                self.history_pointer[0] = max(0, self.history_pointer[0] - 1)
            elif event.keysym == "Down":
                self.history_pointer[0] = min(len(self.command_history), self.history_pointer[0] + 1)

            # Retrieve command from history or clear entry if at end of history
            command = (
                self.command_history[self.history_pointer[0]]
                if self.history_pointer[0] < len(self.command_history)
                else ""
            )
            self.entry.delete(0, END)
            self.entry.insert(0, command)


