import os
import threading
from tkinter import *
from tkinter.ttk import Separator
from src.views.tk_utils import my_font


class DiffTab(Frame):
    def __init__(self, parent, ui_controller=None):
        super().__init__(parent)
        self.parent = parent
        self.ui_controller = ui_controller
        self._controller_attached = bool(ui_controller)

        # Initialize all other instance variables
        self.current_diff_files = []
        self.selected_file = StringVar()
        self.diff_mode = StringVar(value="Working Directory")
        self.original_text = None
        self.unified_text = None
        self.modified_text = None
        self.h_scrollbar = None
        self.file_dropdown = None

        # Create placeholder
        self.placeholder = Label(self, text="Waiting for renderer to initialize...")
        self.placeholder.pack(expand=True)

        self._ui_initialized = False


        # If controller is already provided, set up immediately
        if ui_controller and hasattr(ui_controller, "ansi_renderer") and ui_controller.ansi_renderer is not None:
            self.setup_ui()
            self._ui_initialized = True
            self.setup_bindings()


    def attach_controller(self, ui_controller):
        """Called by TabManager if constructor injection fails"""
        self.ui_controller = ui_controller
        self._controller_attached = True
        # Try to set up UI if possible
        if hasattr(ui_controller, "ansi_renderer") and ui_controller.ansi_renderer is not None:
            self.setup_ui()
            self.setup_bindings()
        else:
            # Schedule a retry
            self.after(100, self.set_renderer)

    def set_renderer(self):
        """Check if renderer is ready and set up UI when it is"""
        if not self._controller_attached or not self.ui_controller:
            # No controller attached yet, try again later
            self.after(100, self.set_renderer)
            return

        if not hasattr(self.ui_controller, "ansi_renderer"):
            # Renderer not ready, try again later
            self.after(100, self.set_renderer)
            return

        # We have everything needed to set up the UI
        self.setup_ui()
        self.setup_bindings()

    def setup_ui(self):
        """Set up the UI components"""
        # Check if already initialized
        if self._ui_initialized:
            return

        print("DiffTab.setup_ui started")

        # Remove placeholder if it exists
        if hasattr(self, 'placeholder') and self.placeholder:
            self.placeholder.pack_forget()
            self.placeholder.destroy()
            self.placeholder = None

        # Create the control frame
        control_frame = Frame(self)
        control_frame.pack(fill=X, padx=5, pady=5)

        # Create file selection dropdown
        file_frame = Frame(control_frame)
        file_frame.pack(side=LEFT, fill=X, expand=True)

        Label(file_frame, text="File:").pack(side=LEFT, padx=(0, 5))
        self.file_dropdown = OptionMenu(file_frame, self.selected_file, "")
        self.file_dropdown.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))
        self.file_dropdown.configure(width=30)

        # Create diff mode selection
        mode_frame = Frame(control_frame)
        mode_frame.pack(side=RIGHT)

        Label(mode_frame, text="Compare:").pack(side=LEFT, padx=(0, 5))
        diff_modes = ["Working Directory", "Staged Changes", "Between Commits"]
        self.mode_dropdown = OptionMenu(mode_frame, self.diff_mode, *diff_modes,
                                        command=lambda *_: self.refresh_file_list())
        self.mode_dropdown.pack(side=LEFT, padx=(0, 10))

        # Create refresh button
        refresh_btn = Button(mode_frame, text="âŸ³", command=self.refresh_diff, width=3)
        refresh_btn.pack(side=LEFT)

        # Add tooltip if controller is available
        if self.ui_controller and hasattr(self.ui_controller, "create_tooltip"):
            self.ui_controller.create_tooltip(refresh_btn, "Refresh diff view")

        # Add separator
        Separator(self, orient=HORIZONTAL).pack(fill=X, pady=5)

        # Create diff panels
        self.diff_frame = Frame(self)
        self.diff_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)

        self.original_text = self._create_diff_panel(self.diff_frame, "Original")
        self.unified_text = self._create_diff_panel(self.diff_frame, "Unified Diff", padx=5)
        self.modified_text = self._create_diff_panel(self.diff_frame, "Modified")

        # Create horizontal scrollbar
        hscroll_frame = Frame(self)
        hscroll_frame.pack(fill=X)
        self.h_scrollbar = Scrollbar(hscroll_frame, orient=HORIZONTAL)
        self.h_scrollbar.pack(fill=X)

        # Configure text widgets
        for text_widget in [self.original_text, self.unified_text, self.modified_text]:
            text_widget.configure(xscrollcommand=self.h_scrollbar.set)
            text_widget.tag_configure("add", background="#e6ffed", foreground="#24292e")
            text_widget.tag_configure("remove", background="#ffdce0", foreground="#24292e")
            text_widget.tag_configure("header", background="#f1f8ff", foreground="#0366d6")
            text_widget.tag_configure("hunk", background="#f1f8ff", foreground="#0366d6")

            # Apply ANSI tags if renderer is available
            if self.ui_controller and hasattr(self.ui_controller, "ansi_renderer"):
                self.ui_controller.ansi_renderer.define_ansi_tags(text_widget)

        # Configure horizontal scrollbar
        self.h_scrollbar.configure(command=self.scroll_all_horizontal)

        # Mark UI as initialized
        self._ui_initialized = True
        print("DiffTab.setup_ui completed")

    def _create_diff_panel(self, parent, label, padx=0):
        """Create a text panel for diff display"""
        frame = Frame(parent, relief=SUNKEN, bd=1)
        frame.pack(side=LEFT, fill=BOTH, expand=True, padx=padx)
        Label(frame, text=label, bg="#e0e0e0", relief=SUNKEN, font=my_font).pack(fill=X)
        text_widget = Text(frame, width=40, height=20, font=my_font, wrap="none")
        text_widget.pack(side=LEFT, fill=BOTH, expand=True)
        vscroll = Scrollbar(frame, orient=VERTICAL, command=text_widget.yview)
        vscroll.pack(side=RIGHT, fill=Y)
        text_widget.configure(yscrollcommand=vscroll.set)
        return text_widget

    def setup_bindings(self):
        """Set up event bindings"""
        if not self._ui_initialized:
            return

        # Set up scroll synchronization
        for widget in [self.original_text, self.unified_text, self.modified_text]:
            if widget:  # Check if widget exists
                widget.bind("<MouseWheel>", self.sync_vertical_scroll)

        # Set up file selection callback
        self.selected_file.trace("w", lambda *args: self.show_diff())

    def refresh_file_list(self):
        """Refresh the list of files with differences"""
        # Check if UI is initialized
        if not self._ui_initialized or not self.file_dropdown:
            print("Cannot refresh file list - UI not initialized")
            return

        # Check if controller is attached
        if not self._controller_attached or not self.ui_controller:
            print("Cannot refresh file list - controller not attached")
            return

        try:
            menu = self.file_dropdown["menu"]
            menu.delete(0, "end")

            mode = self.diff_mode.get()

            # Get file list based on selected mode
            if mode == "Working Directory":
                output, _, _ = self.ui_controller.run_git("diff", "--name-only")
            elif mode == "Staged Changes":
                output, _, _ = self.ui_controller.run_git("diff", "--cached", "--name-only")
            elif mode == "Between Commits":
                output, _, _ = self.ui_controller.run_git("log", "-1", "--name-only", "--pretty=format:")
            else:
                output = ""

            # Parse file list
            self.current_diff_files = [f for f in output.strip().split("\n") if f.strip()]

            # Add files to dropdown menu
            for f in self.current_diff_files:
                menu.add_command(label=f, command=lambda file=f: self.selected_file.set(file))

            # Select first file or clear if no files
            if self.current_diff_files:
                self.selected_file.set(self.current_diff_files[0])
            else:
                self.selected_file.set("")
                self.clear_diff_views()

        except Exception as e:
            print(f"Error refreshing file list: {e}")
            # Clear file list on error
            self.current_diff_files = []
            self.selected_file.set("")
            self.clear_diff_views()

    def refresh_diff(self):
        """Refresh the diff view"""
        if not self._ui_initialized:
            return

        self.refresh_file_list()
        if self.selected_file.get():
            self.show_diff()

    def show_diff(self, file_path=None):
        """Show diff for the selected file"""
        if not self._ui_initialized:
            return

        file_path = file_path or self.selected_file.get()
        if not file_path:
            return

        # Check if text widgets exist
        if not all([self.original_text, self.unified_text, self.modified_text]):
            return

        # Check if controller is attached
        if not self._controller_attached or not self.ui_controller:
            return

        try:
            # Enable text widgets for editing
            for widget in [self.original_text, self.unified_text, self.modified_text]:
                widget.configure(state=NORMAL)
                widget.delete("1.0", END)

            mode = self.diff_mode.get()

            # Get diff content based on selected mode
            if mode == "Working Directory":
                original, _, _ = self.ui_controller.run_git("show", f"HEAD:{file_path}")
                try:
                    with open(os.path.join(self.ui_controller.git_service.repo_dir, file_path), "r", encoding="utf-8") as f:
                        modified = f.read()
                except Exception as e:
                    modified = f"[Error reading file: {e}]"
                unified, _, _ = self.ui_controller.run_git("diff", file_path)

            elif mode == "Staged Changes":
                original, _, _ = self.ui_controller.run_git("show", f"HEAD:{file_path}")
                modified, _, _ = self.ui_controller.run_git("show", f":0:{file_path}")
                unified, _, _ = self.ui_controller.run_git("diff", "--color", "--cached", file_path)

            elif mode == "Between Commits":
                original, _, _ = self.ui_controller.run_git("show", f"HEAD~1:{file_path}")
                modified, _, _ = self.ui_controller.run_git("show", f"HEAD:{file_path}")
                unified, _, _ = self.ui_controller.run_git("diff", "--color", "HEAD~1..HEAD", "--", file_path)

            # Display diff content
            self.original_text.insert(END, original)
            self.modified_text.insert(END, modified)

            # Insert unified diff with syntax highlighting
            for line in unified.splitlines():
                if line.startswith("+") and not line.startswith("+++"):
                    self.unified_text.insert(END, line + "\n", "add")
                elif line.startswith("-") and not line.startswith("---"):
                    self.unified_text.insert(END, line + "\n", "remove")
                elif line.startswith("@@"):
                    self.unified_text.insert(END, line + "\n", "hunk")
                elif line.startswith("diff") or line.startswith("---") or line.startswith("+++"):
                    self.unified_text.insert(END, line + "\n", "header")
                else:
                    self.unified_text.insert(END, line + "\n")

            # Highlight differences
            self.highlight_differences()

            # Disable text widgets after editing
            for widget in [self.original_text, self.unified_text, self.modified_text]:
                widget.configure(state=DISABLED)

        except Exception as e:
            print(f"Error showing diff: {e}")
            self.clear_diff_views()

    def highlight_differences(self):
        """Highlight differences between original and modified text"""
        if not self._ui_initialized:
            return

        try:
            orig_lines = self.original_text.get("1.0", END).splitlines()
            mod_lines = self.modified_text.get("1.0", END).splitlines()

            self.original_text.configure(state=NORMAL)
            self.modified_text.configure(state=NORMAL)

            for i, (orig, mod) in enumerate(zip(orig_lines, mod_lines)):
                if orig != mod:
                    line = f"{i + 1}.0"
                    self.original_text.tag_add("remove", line, f"{i + 1}.end")
                    self.modified_text.tag_add("add", line, f"{i + 1}.end")

            self.original_text.configure(state=DISABLED)
            self.modified_text.configure(state=DISABLED)

        except Exception as e:
            print(f"Error highlighting differences: {e}")

    def clear_diff_views(self):
        """Clear the content of all diff views"""
        if not self._ui_initialized:
            return

        for widget in [self.original_text, self.unified_text, self.modified_text]:
            if widget:  # Check if widget exists
                widget.configure(state=NORMAL)
                widget.delete("1.0", END)
                widget.configure(state=DISABLED)

    def sync_vertical_scroll(self, event):
        """Synchronize vertical scrolling across all text widgets"""
        if not self._ui_initialized:
            return "break"

        try:
            source = event.widget
            y = source.yview()
            for widget in [self.original_text, self.unified_text, self.modified_text]:
                if widget and widget != source:  # Check if widget exists and is not the source
                    widget.yview_moveto(y[0])
            return "break"
        except Exception as e:
            print(f"Error syncing vertical scroll: {e}")
            return "break"

    def scroll_all_horizontal(self, *args):
        """Synchronize horizontal scrolling across all text widgets"""
        if not self._ui_initialized:
            return

        try:
            for widget in [self.original_text, self.unified_text, self.modified_text]:
                if widget:  # Check if widget exists
                    widget.xview(*args)
        except Exception as e:
            print(f"Error syncing horizontal scroll: {e}")

    def on_focus(self):
        """Called when the tab gets focus"""
        # Try to refresh the file list if UI is ready
        if self._ui_initialized and self._controller_attached:
            try:
                self.refresh_file_list()
            except Exception as e:
                print(f"Error refreshing file list on focus: {e}")
