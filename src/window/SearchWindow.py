import tkinter as tk
import customtkinter as ctk
from src.ui.themed_window import ThemedWindow

class SearchWindow(ThemedWindow):
    def __init__(self, parent=None):
        if parent is None:
            try:
                from src.views.tk_utils import root
                parent = root
            except ImportError:
                pass
        super().__init__(parent)
        self.title("Find Text")
        self.resizable(False, False)

        # Access script_text from parent or global
        try:
            from src.views.tk_utils import script_text
            self.script_text = script_text
        except ImportError:
            self.script_text = None

        self.geometry("350x120")
        self.setup_ui()

    def setup_ui(self):
        ctk.CTkLabel(self, text="Find All:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.search_entry_widget = ctk.CTkEntry(self, width=150)
        self.search_entry_widget.grid(row=0, column=1, padx=10, pady=10, sticky="we")
        self.search_entry_widget.focus_set()

        ctk.CTkButton(self, text="Find", width=60, command=self.find_text).grid(row=0, column=2, padx=10, pady=10)

        ctk.CTkButton(self, text="Cancel", command=self.cancel).grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="e")

    def find_text(self):
        if not self.script_text: return
        value = self.search_entry_widget.get()
        self.script_text._textbox.tag_remove("found", "1.0", "end")
        if value:
            self.script_text._textbox.tag_config("found", background="yellow", foreground="black")
            idx = "1.0"
            while idx:
                idx = self.script_text._textbox.search(value, idx, nocase=1, stopindex="end")
                if idx:
                    lastidx = f"{idx}+{len(value)}c"
                    self.script_text._textbox.tag_add("found", idx, lastidx)
                    idx = lastidx

    def cancel(self):
        if self.script_text:
            self.script_text._textbox.tag_remove("found", "1.0", "end")
        self.destroy()
