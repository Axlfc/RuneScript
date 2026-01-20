from tkinter import Frame, Menu, Label, Entry, END, BOTH, X, Text
from tkinter import scrolledtext
from src.views.tk_utils import my_font


class ConsoleTab(Frame):
    def __init__(self, parent, ui_controller=None):
        print("CONSOLETAB LAUNCH")
        super().__init__(parent)
        self.ui_controller = ui_controller
        self._controller_attached = bool(ui_controller)

        # Create frames first
        self.output_frame = Frame(self)
        self.output_frame.pack(fill=BOTH, expand=True)

        # Create output text widget in output_frame
        self.output_text = scrolledtext.ScrolledText(
            self.output_frame,
            height=20,
            width=80,
            font=my_font,
            background="#1E1E1E",
            foreground="#D4D4D4"
        )
        self.output_text.pack(fill=BOTH, expand=True)

        # Dedicated frame for commit list
        self.commit_frame = Frame(self)
        self.commit_frame.pack(fill=BOTH, expand=True)

        # Button frame separately
        self.button_frame = Frame(self)
        self.button_frame.pack(fill=X)

        # Initialize entry for later use
        self.entry = None
        self.context_menu = None
        self.status_formatter = None

        self._ui_initialized = False

    def attach_controller(self, ui_controller):
        if ui_controller is None:
            print("[ConsoleTab] Warning: ui_controller is None!")
            return

        self.ui_controller = ui_controller
        self._controller_attached = True

        if hasattr(self.ui_controller, "ansi_renderer") and self.ui_controller.ansi_renderer:
            self.ui_controller.ansi_renderer.define_ansi_tags(self.output_text)
        else:
            print("[ConsoleTab] Warning: ANSI renderer is not yet initialized!")

        # Set up the button frame and context menu with the controller
        self.setup_button_frame()
        self.setup_context_menu()

    @property
    def output(self):
        if self.output_text is None:
            raise RuntimeError("ConsoleTab.output_text is not initialized yet.")
        return self.output_text

    def setup_button_frame(self):
        # Clear existing widgets first
        for widget in self.button_frame.winfo_children():
            widget.destroy()

        # Command entry with prefix label
        command_frame = Frame(self.button_frame)
        command_frame.pack(side="left", fill="x", expand=True)
        Label(command_frame, text="git", font=("Arial", 10, "bold")).pack(side="left", padx=(0, 5))
        self.entry = Entry(
            command_frame,
            width=80,
            background="#1E1E1E",
            foreground="#D4D4D4"
        )
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.focus()
        self.entry.bind("<Return>", lambda event: self.ui_controller.execute_command(self.entry.get()))

    def setup_context_menu(self):
        self.context_menu = Menu(self.output_text, tearoff=0)
        self.output_text.bind(
            "<Button-3>",
            lambda event: self.context_menu.tk_popup(event.x_root, event.y_root)
        )

        if self.ui_controller is not None:
            self.context_menu.add_command(label="Git Status",
                                          command=lambda: self.status_formatter.format_status(self.output_text))
            self.context_menu.add_separator()
            self.context_menu.add_command(label="Copy", command=self.ui_controller.copy_selected_text)
            self.context_menu.add_command(label="Clear Console", command=self.ui_controller.clear_console)
        else:
            self.context_menu.add_command(label="Copy", command=self._copy_text)
            self.context_menu.add_command(label="Clear Console", command=self._clear_console)

    def _copy_text(self):
        """Fallback copy method if ui_controller is not available"""
        try:
            selected_text = self.output_text.get("sel.first", "sel.last")
            self.output_text.clipboard_clear()
            self.output_text.clipboard_append(selected_text)
        except:
            pass

    def _clear_console(self):
        """Fallback clear method if ui_controller is not available"""
        self.output_text.delete("1.0", END)

    def set_dependencies(self, status_formatter):
        self.status_formatter = status_formatter
