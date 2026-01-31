import tkinter as tk
import customtkinter as ctk
from src.ui.themed_window import ThemedWindow

class HelpWindow(ThemedWindow):
    def __init__(self, parent=None):
        """Initialize the Help Window to display detailed keyboard shortcuts."""
        if parent is None:
            try:
                from src.views.tk_utils import root
                parent = root
            except ImportError:
                pass
        super().__init__(parent)
        self.title("Help - Keyboard Shortcuts")
        self.geometry("700x700")
        self.setup_ui()

    def setup_ui(self):
        """Set up the UI with categorized shortcut information."""
        ctk.CTkLabel(self, text="Keyboard Shortcuts", font=("Arial", 16, "bold")).pack(pady=10)

        # Use CTkScrollableFrame for automatic scrollbar handling
        scroll_frame = ctk.CTkScrollableFrame(self)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Categories and shortcuts data
        categories = {
            "File Operations": [
                ("New File", "Ctrl + N"),
                ("Open File", "Ctrl + O"),
                ("Close File", "Ctrl + W"),
                ("Save File", "Ctrl + S"),
                ("Save As...", "Ctrl + Shift + S"),
                ("Move/Rename File", "F2"),
                ("Print Document", "Ctrl + P"),
            ],
            "Edit Operations": [
                ("Undo", "Ctrl + Z"),
                ("Redo", "Ctrl + Y"),
                ("Cut", "Ctrl + X"),
                ("Copy", "Ctrl + C"),
                ("Paste", "Ctrl + V"),
                ("Duplicate", "Ctrl + D"),
                ("Find", "Ctrl + F"),
                ("Find And Replace", "Ctrl + R"),
                ("Find In Files", "Ctrl + H")
            ],
            "View Controls": [
                ("Toggle Directory Pane", "Ctrl + Shift + D"),
                ("Toggle File Pane", "Ctrl + Shift + F"),
                ("Script Arguments Dialog", "Ctrl + Shift + A"),
                ("Run Script", "Ctrl + Shift + R"),
                ("Set Timeout", "Ctrl + Shift + T"),
                ("Toggle Interactive Mode", "Ctrl + Shift + I"),
                ("Open Filesystem Explorer", "Ctrl + Shift + E"),
            ],
            "Tools and Utilities": [
                ("AI Assistant", "Ctrl + Alt + A"),
                ("Calculator", "Ctrl + Alt + C"),
                ("Translator", "F3"),
                ("Prompt Enhancement", "Ctrl + Alt + P"),
                ("Kanban Board", "Ctrl + Alt + K"),
                ("LaTeX/Markdown Editor", "Ctrl + Alt + L"),
                ("Git Console", "Ctrl + Alt + G"),
                ("System Shell", "Ctrl + Alt + B"),
                ("Python Shell", "Ctrl + Alt + Y"),
                ("Notebooks", "Ctrl + Alt + N"),
                ("Options/Settings", "Ctrl + ,"),
            ],
            "System Commands": [
                ("Open Winget Window", "Ctrl + Alt + W"),
                ("System Info", "Ctrl + Alt + I"),
            ],
            "Help and Support": [
                ("Help Contents", "F1"),
                ("Shortcuts", "F4"),
                ("Mnemonics", "F10"),
                ("About", "Ctrl + Alt + H"),
            ]
        }

        # Populate categories and shortcuts in the frame
        for category, shortcuts in categories.items():
            ctk.CTkLabel(scroll_frame, text=category, font=("Arial", 13, "bold"), text_color="#1f538d").pack(anchor="w", pady=(10, 5), padx=10)
            for action, shortcut in shortcuts:
                row_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
                row_frame.pack(fill="x", pady=1)
                ctk.CTkLabel(row_frame, text=f"{action}:", anchor="w", width=250).pack(side="left", padx=20)
                ctk.CTkLabel(row_frame, text=shortcut, anchor="e").pack(side="left")
