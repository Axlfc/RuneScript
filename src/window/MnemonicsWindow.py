import tkinter as tk
import customtkinter as ctk
from src.ui.themed_window import ThemedWindow

class MnemonicsWindow(ThemedWindow):
    def __init__(self, parent=None):
        """Initialize the Mnemonics Window with keyboard shortcut details for main menu options."""
        if parent is None:
            try:
                from src.views.tk_utils import root
                parent = root
            except ImportError:
                pass
        super().__init__(parent)
        self.title("Mnemonics")
        self.resizable(False, False)
        self.center_window(300, 300)
        self.setup_ui()

    def center_window(self, width, height):
        """Center the window on the screen."""
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def setup_ui(self):
        """Set up the UI with mnemonic information."""
        ctk.CTkLabel(self, text="Mnemonics", font=("Arial", 14, "bold")).pack(pady=10)

        mnemonics = [
            ("File", "Alt + F"),
            ("Edit", "Alt + E"),
            ("View", "Alt + V"),
            ("System", "Alt + S"),
            ("Jobs", "Alt + J"),
            ("Help", "Alt + H")
        ]

        # Display each mnemonic as a row
        for menu, shortcut in mnemonics:
            row_frame = ctk.CTkFrame(self, fg_color="transparent")
            row_frame.pack(fill="x", pady=5)
            ctk.CTkLabel(row_frame, text=f"{menu}:", font=("Arial", 10, "bold"), anchor="w", width=100).pack(side="left", padx=10)
            ctk.CTkLabel(row_frame, text=shortcut, font=("Arial", 10), anchor="e").pack(side="left")
