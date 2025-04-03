from tkinter import Toplevel, Label, Frame, LEFT


class MnemonicsWindow:
    def __init__(self):
        """Initialize the Mnemonics Window with keyboard shortcut details for main menu options."""
        self.mnemonics_window = Toplevel()
        self.mnemonics_window.title("Mnemonics")
        self.mnemonics_window.resizable(False, False)
        self.center_window(300, 300)
        self.setup_ui()

    def center_window(self, width, height):
        """Center the window on the screen."""
        x = (self.mnemonics_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.mnemonics_window.winfo_screenheight() // 2) - (height // 2)
        self.mnemonics_window.geometry(f"{width}x{height}+{x}+{y}")

    def setup_ui(self):
        """Set up the UI with mnemonic information."""
        Label(self.mnemonics_window, text="Mnemonics", font=("Arial", 14, "bold")).pack(pady=10)

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
            row_frame = Frame(self.mnemonics_window)
            row_frame.pack(fill="x", pady=5)
            Label(row_frame, text=f"{menu}:", font=("Arial", 10, "bold"), anchor="w", width=10).pack(side=LEFT, padx=10)
            Label(row_frame, text=shortcut, font=("Arial", 10), anchor="e").pack(side=LEFT)
