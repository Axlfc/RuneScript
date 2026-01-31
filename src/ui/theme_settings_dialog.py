import customtkinter as ctk
import tkinter as tk
from src.ui.theme_manager import ThemeManager
from src.ui.themed_window import ThemedWindow

class ThemeSettingsDialog(ThemedWindow):
    """Dialog for theme settings."""

    def __init__(self, parent=None):
        if parent is None:
            try:
                from src.views.tk_utils import root
                parent = root
            except ImportError:
                pass
        super().__init__(parent)

        self.title("Theme Settings")
        self.geometry("300x250")
        self.resizable(False, False)

        # Theme manager
        self._theme_manager = ThemeManager.get_instance()

        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # UI
        label = ctk.CTkLabel(self.main_container, text="Select Appearance Mode:", font=("Segoe UI", 12, "bold"))
        label.pack(pady=10)

        # Radio buttons for theme
        self.theme_var = tk.StringVar(value=self._theme_manager.get_current_theme())

        modes = [("Dark", "Dark"), ("Light", "Light"), ("System", "System")]

        for text, mode in modes:
            rb = ctk.CTkRadioButton(
                self.main_container,
                text=text,
                variable=self.theme_var,
                value=mode,
                command=self._on_theme_select
            )
            rb.pack(pady=5, padx=20, anchor="w")

        # Close button
        close_btn = ctk.CTkButton(
            self.main_container,
            text="Close",
            command=self.destroy
        )
        close_btn.pack(pady=20)

        # Make modal
        self.transient(parent)
        self.grab_set()

    def _on_theme_select(self):
        """Handle theme selection."""
        selected = self.theme_var.get()
        self._theme_manager.set_theme(selected)
