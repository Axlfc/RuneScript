# TerminalWindow.py
import os
import subprocess
import threading
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
        self.geometry("800x600")

        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Output text area with scroll
        self.output_text = ctk.CTkTextbox(self.main_container, height=500)
        self.output_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Command history and pointer for navigation
        self.command_history = []
        self.history_pointer = 0

        # Entry widget for command input
        self.entry = ctk.CTkEntry(self.main_container, placeholder_text="Enter command here...")
        self.entry.pack(side="bottom", fill="x", padx=5, pady=5)
        self.entry.focus()

        # Key bindings for command execution and history navigation
        self.entry.bind("<Return>", self.execute_command)
        self.entry.bind("<Up>", self.navigate_history)
        self.entry.bind("<Down>", self.navigate_history)

    def execute_command(self, event=None):
        """Execute the command entered in the terminal."""
        command = self.entry.get().strip()
        if command:
            # Add command to history and update history pointer
            self.command_history.append(command)
            self.history_pointer = len(self.command_history)

            self.output_text.insert(tk.END, f"\n> {command}\n")
            self.entry.delete(0, tk.END)
            self.entry.configure(state=tk.DISABLED)

            # Execute in a thread to avoid blocking UI
            threading.Thread(target=self._run_command_thread, args=(command,), daemon=True).start()

    def _run_command_thread(self, command):
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=True,
                text=True,
                cwd=os.getcwd()
            )

            output, _ = process.communicate()

            def update_ui():
                if self.winfo_exists():
                    self.output_text.insert(tk.END, output)
                    self.output_text.see(tk.END)
                    self.entry.configure(state=tk.NORMAL)
                    self.entry.focus()

            self.after(0, update_ui)

        except Exception as e:
            def update_ui_error():
                if self.winfo_exists():
                    self.output_text.insert(tk.END, f"Error: {str(e)}\n")
                    self.entry.configure(state=tk.NORMAL)
            self.after(0, update_ui_error)

    def navigate_history(self, event):
        """Navigate through the command history using arrow keys."""
        if self.command_history:
            if event.keysym == "Up":
                self.history_pointer = max(0, self.history_pointer - 1)
            elif event.keysym == "Down":
                self.history_pointer = min(len(self.command_history), self.history_pointer + 1)

            # Retrieve command from history or clear entry if at end of history
            command = (
                self.command_history[self.history_pointer]
                if self.history_pointer < len(self.command_history)
                else ""
            )
            self.entry.delete(0, tk.END)
            self.entry.insert(0, command)
