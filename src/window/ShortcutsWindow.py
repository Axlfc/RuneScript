import tkinter as tk
import customtkinter as ctk
from src.ui.themed_window import ThemedWindow

class ShortcutsWindow(ThemedWindow):
    def __init__(self, parent=None):
        if parent is None:
            try:
                from src.views.tk_utils import root
                parent = root
            except ImportError:
                pass
        super().__init__(parent)
        self.title("Global Shortcuts Reference")
        self.geometry("800x800")

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.setup_tabs()

    def setup_tabs(self):
        systems = {
            "Windows": self.get_windows_shortcuts(),
            "macOS": self.get_mac_shortcuts(),
            "Linux": self.get_linux_shortcuts(),
            "Firefox": self.get_firefox_shortcuts(),
            "PowerToys": self.get_powertoys_shortcuts()
        }

        for name, categories in systems.items():
            self.tabview.add(name)
            self.populate_tab(self.tabview.tab(name), categories)

    def populate_tab(self, frame, categories):
        scroll = ctk.CTkScrollableFrame(frame)
        scroll.pack(fill="both", expand=True)

        for cat_name, shortcuts in categories.items():
            ctk.CTkLabel(scroll, text=cat_name, font=("Arial", 14, "bold"), text_color="#1f538d").pack(anchor="w", pady=(10, 5), padx=10)
            for action, shortcut in shortcuts:
                # Clean up any potential 'tk.' artifacts from strings
                clean_shortcut = shortcut.replace("tk.", "")

                row = ctk.CTkFrame(scroll, fg_color="transparent")
                row.pack(fill="x", pady=1)
                ctk.CTkLabel(row, text=f"{action}:", anchor="w", width=300).pack(side="left", padx=20)
                ctk.CTkLabel(row, text=clean_shortcut, anchor="e").pack(side="left")

    def get_windows_shortcuts(self):
        return {
            "Essential Shortcuts": [
                ("Select all", "Ctrl + A"), ("Copy text", "Ctrl + C"), ("Cut text", "Ctrl + X"),
                ("Paste text", "Ctrl + V"), ("Undo action", "Ctrl + Z"), ("Redo action", "Ctrl + Y"),
                ("Create new folder", "Ctrl + Shift + N"), ("Rename file", "F2"),
                ("Delete selected item", "Del"), ("Close active window", "Alt + F4")
            ],
            "System Controls": [
                ("Take screenshot", "Windows + Shift + S"), ("Open File Explorer", "Windows + E"),
                ("Task Manager", "Ctrl + Shift + Esc"), ("Search", "Windows + S"),
                ("Settings", "Windows + I")
            ]
        }

    def get_mac_shortcuts(self):
        return {
            "Essential": [
                ("Select all", "⌘ + A"), ("Copy", "⌘ + C"), ("Cut", "⌘ + X"), ("Paste", "⌘ + V"),
                ("Undo", "⌘ + Z"), ("Close window", "⌘ + W"), ("Quit app", "⌘ + Q")
            ]
        }

    def get_linux_shortcuts(self):
        return {
            "Essential": [
                ("Select all", "Ctrl + A"), ("Copy", "Ctrl + C"), ("Cut", "Ctrl + X"),
                ("Paste", "Ctrl + V"), ("Undo", "Ctrl + Z"), ("Terminal", "Ctrl + Alt + T")
            ]
        }

    def get_firefox_shortcuts(self):
        return {
            "Tabs": [
                ("New tab", "Ctrl + T"), ("Close tab", "Ctrl + W"), ("Reopen closed tab", "Ctrl + Shift + T")
            ]
        }

    def get_powertoys_shortcuts(self):
        return {
            "General": [
                ("Run", "Alt + Space"), ("Color Picker", "Shift + Win + C"), ("FancyZones", "Win + `")
            ]
        }
