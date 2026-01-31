import tkinter as tk
import tkinter as tk
from tkinter import LEFT, RIGHT, messagebox
import customtkinter as ctk
from src.config.fonts import AppFonts
import pyperclip
import webbrowser

from src.views.tk_utils import localization_data
from src.ui.themed_window import ThemedWindow


class AboutWindow(ThemedWindow):
    def __init__(self, parent):
        """
        Initializes the AboutWindow.

        Args:
            parent (tk.Tk or tk.Toplevel): The parent window.
        """
        super().__init__(parent)
        self.title(localization_data["about_scripts_editor_about"])
        self.resizable(False, False)

        # Center the window on the screen
        self.center_window(500, 400)

        # Define fonts
        self.title_font = AppFonts.TITLE
        self.header_font = AppFonts.HEADER
        self.normal_font = AppFonts.NORMAL

        # Create and pack the main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Application Title
        ctk.CTkLabel(self.main_frame, text=localization_data["application_title"], font=self.title_font).pack(pady=(0, 10))

        # Application Information
        app_info = localization_data["application_info"]
        ctk.CTkLabel(self.main_frame, text=app_info, font=self.normal_font, justify='left', wraplength=460).pack(pady=(0, 20))

        # Close Button
        ctk.CTkButton(self.main_frame, text=localization_data["close"], command=self.destroy, width=100).pack(pady=(30, 0))

        # Make the window modal
        self.transient(parent)
        self.grab_set()

    def center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def add_donation_option(self, parent, crypto_name, address, explorer_url):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill='x', pady=5)

        ctk.CTkLabel(frame, text=f"{crypto_name}:", font=self.normal_font).pack(side=tk.LEFT, padx=5)

        address_label = ctk.CTkLabel(frame, text=address, font=self.normal_font, text_color="blue", cursor="hand2")
        address_label.pack(side=tk.LEFT, padx=(5, 0))
        address_label.bind("<Button-1>", lambda e: self.open_in_explorer(explorer_url))

        ctk.CTkButton(frame, text="Copy", command=lambda: self.copy_to_clipboard(address), width=60).pack(side=tk.RIGHT, padx=5)

    def copy_to_clipboard(self, address):
        try:
            pyperclip.copy(address)
            messagebox.showinfo("Copied", "Address copied to clipboard!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy address: {e}")

    def open_in_explorer(self, url):
        try:
            webbrowser.open(url)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open web browser: {e}")

