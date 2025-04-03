from tkinter import Toplevel, Label, Entry, Button, END
from src.views.tk_utils import script_text


class SearchAndReplaceWindow:
    def __init__(self):
        """Initialize the Search and Replace window."""
        self.script_text = script_text

        # Create the Toplevel window
        self.replace_toplevel = Toplevel()
        self.replace_toplevel.title("Search and Replace")
        self.replace_toplevel.resizable(False, False)
        self.replace_toplevel.transient()

        # Center window on screen
        self.center_window(350, 150)

        # Set up UI components
        self.setup_ui()

    def setup_ui(self):
        Label(self.replace_toplevel, text="Find:").grid(row=0, column=0, sticky="e")
        self.search_entry_widget = Entry(self.replace_toplevel, width=25)
        self.search_entry_widget.grid(row=0, column=1, padx=2, pady=2, sticky="we")

        Label(self.replace_toplevel, text="Replace:").grid(row=1, column=0, sticky="e")
        self.replace_entry_widget = Entry(self.replace_toplevel, width=25)
        self.replace_entry_widget.grid(row=1, column=1, padx=2, pady=2, sticky="we")

        Button(
            self.replace_toplevel,
            text="Replace All",
            command=self.search_and_replace
        ).grid(row=2, column=1, padx=2, pady=5, sticky="e" + "w")

        Button(
            self.replace_toplevel,
            text="Cancel",
            command=self.cancel
        ).grid(row=3, column=1, sticky="e" + "w", padx=2, pady=2)

    def center_window(self, width, height):
        x = (self.replace_toplevel.winfo_screenwidth() // 2) - (width // 2)
        y = (self.replace_toplevel.winfo_screenheight() // 2) - (height // 2)
        self.replace_toplevel.geometry(f"{width}x{height}+{x}+{y}")

    def search_and_replace(self):
        search_text = self.search_entry_widget.get()
        replace_text = self.replace_entry_widget.get()
        if search_text:
            start_index = "1.0"
            while True:
                start_index = self.script_text.search(search_text, start_index, nocase=1, stopindex=END)
                if not start_index:
                    break
                end_index = f"{start_index}+{len(search_text)}c"
                self.script_text.delete(start_index, end_index)
                self.script_text.insert(start_index, replace_text)
                start_index = end_index

    def cancel(self):
        self.replace_toplevel.destroy()

