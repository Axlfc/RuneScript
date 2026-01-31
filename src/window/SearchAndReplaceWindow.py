import tkinter as tk
import customtkinter as ctk
from src.ui.themed_window import ThemedWindow

class SearchAndReplaceWindow(ThemedWindow):
    def __init__(self, parent=None):
        if parent is None:
            try:
                from src.views.tk_utils import root
                parent = root
            except ImportError:
                pass
        super().__init__(parent)
        self.title("Search and Replace")
        self.resizable(False, False)

        try:
            from src.views.tk_utils import script_text
            self.script_text = script_text
        except ImportError:
            self.script_text = None

        self.geometry("400x180")
        self.setup_ui()

    def setup_ui(self):
        ctk.CTkLabel(self, text="Find:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.search_entry_widget = ctk.CTkEntry(self, width=200)
        self.search_entry_widget.grid(row=0, column=1, padx=10, pady=10, sticky="we")

        ctk.CTkLabel(self, text="Replace:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.replace_entry_widget = ctk.CTkEntry(self, width=200)
        self.replace_entry_widget.grid(row=1, column=1, padx=10, pady=10, sticky="we")

        ctk.CTkButton(self, text="Replace All", command=self.search_and_replace).grid(row=2, column=1, padx=10, pady=10, sticky="we")
        ctk.CTkButton(self, text="Cancel", fg_color="gray", command=self.destroy).grid(row=3, column=1, padx=10, pady=5, sticky="e")

    def search_and_replace(self):
        if not self.script_text: return
        search_text = self.search_entry_widget.get()
        replace_text = self.replace_entry_widget.get()
        if search_text:
            start_index = "1.0"
            while True:
                start_index = self.script_text._textbox.search(search_text, start_index, nocase=1, stopindex="end")
                if not start_index:
                    break
                end_index = f"{start_index}+{len(search_text)}c"
                self.script_text.delete(start_index, end_index)
                self.script_text.insert(start_index, replace_text)
                start_index = f"{start_index}+{len(replace_text)}c"
