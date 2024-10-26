from tkinter import Toplevel, Label, Entry, Button, END
from src.views.tk_utils import script_text


class SearchWindow:
    def __init__(self):
        """Initialize the Find Text window."""
        self.script_text = script_text

        # Create the Toplevel window
        self.search_toplevel = Toplevel()
        self.search_toplevel.title("Find Text")
        self.search_toplevel.resizable(False, False)
        self.search_toplevel.transient()

        # Center window on screen
        self.center_window(300, 100)

        # Set up UI components
        self.setup_ui()

    def setup_ui(self):
        Label(self.search_toplevel, text="Find All:").grid(row=0, column=0, sticky="e")
        self.search_entry_widget = Entry(self.search_toplevel, width=25)
        self.search_entry_widget.grid(row=0, column=1, padx=2, pady=2, sticky="we")
        self.search_entry_widget.focus_set()

        Button(
            self.search_toplevel,
            text="Ok",
            command=self.find_text
        ).grid(row=0, column=2, padx=2, pady=5)

        Button(
            self.search_toplevel,
            text="Cancel",
            command=self.cancel
        ).grid(row=1, column=1, columnspan=2, sticky="e" + "w", padx=2, pady=2)

    def center_window(self, width, height):
        x = (self.search_toplevel.winfo_screenwidth() // 2) - (width // 2)
        y = (self.search_toplevel.winfo_screenheight() // 2) - (height // 2)
        self.search_toplevel.geometry(f"{width}x{height}+{x}+{y}")

    def find_text(self):
        value = self.search_entry_widget.get()
        self.script_text.tag_remove("found", "1.0", END)
        if value:
            self.script_text.tag_config("found", background="yellow")
            idx = "1.0"
            while idx:
                idx = self.script_text.search(value, idx, nocase=1, stopindex=END)
                if idx:
                    lastidx = f"{idx}+{len(value)}c"
                    self.script_text.tag_add("found", idx, lastidx)
                    idx = lastidx

    def cancel(self):
        self.script_text.tag_remove("found", "1.0", END)
        self.search_toplevel.destroy()

