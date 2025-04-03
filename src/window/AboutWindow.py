import tkinter as tk
from tkinter import Toplevel, Label, Button, Frame, LEFT, RIGHT, messagebox
import tkinter.font as font
import pyperclip
import webbrowser

from src.views.tk_utils import localization_data


class AboutWindow:
    def __init__(self, parent):
        """
        Initializes the AboutWindow.

        Args:
            parent (tk.Tk or tk.Toplevel): The parent window.
        """
        self.parent = parent
        self.about_window = Toplevel()
        self.about_window.title(localization_data["about_scripts_editor_about"])
        self.about_window.resizable(False, False)

        # Center the window on the screen
        self.center_window(500, 400)

        # Define fonts
        self.title_font = font.Font(family="Arial", size=18, weight="bold")
        self.header_font = font.Font(family="Arial", size=14, weight="bold")
        self.normal_font = font.Font(family="Arial", size=12)

        # Create and pack the main frame
        self.main_frame = Frame(self.about_window, padx=20, pady=20)
        self.main_frame.pack(fill='both', expand=True)

        # Application Title
        Label(self.main_frame, text=localization_data["application_title"], font=self.title_font).pack(pady=(0, 10))

        # Application Information
        app_info = localization_data["application_info"]
        Label(self.main_frame, text=app_info, font=self.normal_font, justify='left', wraplength=460).pack(pady=(0, 20))

        # Close Button
        Button(self.main_frame, text=localization_data["close"], command=self.about_window.destroy, width=10).pack(pady=(30, 0))

        # Make the window modal
        self.about_window.transient(self.parent)
        self.about_window.grab_set()
        self.parent.wait_window(self.about_window)

    def center_window(self, width, height):
        screen_width = self.about_window.winfo_screenwidth()
        screen_height = self.about_window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.about_window.geometry(f"{width}x{height}+{x}+{y}")

    def add_donation_option(self, parent, crypto_name, address, explorer_url):
        frame = Frame(parent)
        frame.pack(fill='x', pady=5)

        Label(frame, text=f"{crypto_name}:", font=self.normal_font).pack(side=LEFT)

        address_label = Label(frame, text=address, font=self.normal_font, fg="blue", cursor="hand2")
        address_label.pack(side=LEFT, padx=(5, 0))
        address_label.bind("<Button-1>", lambda e: self.open_in_explorer(explorer_url))

        Button(frame, text="Copy", command=lambda: self.copy_to_clipboard(address)).pack(side=RIGHT)

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
