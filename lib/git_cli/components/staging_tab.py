from tkinter import Listbox, Button, LabelFrame, END, Menu, Frame, messagebox
from tkinter.ttk import PanedWindow


class StagingTab(Frame):
    """
    Tab for managing git staging area (unstaged and staged changes).
    Allows users to stage, unstage, and commit changes.
    """

    def __init__(self, parent, ui_controller=None):
        super().__init__(parent)
        self.parent = parent
        self.ui_controller = ui_controller
        self._controller_attached = False
        self._ui_initialized = False
        self.git_window = None  # si es necesario puedes recibirlo también como parámetro

        self.setup_staging_tab()
        self.setup_context_menus()

    def attach_controller(self, controller):
        # The StagingTab subscribes to "git.staging.updated" but the handler is named differently
        controller.event_bus.subscribe("git.staging.updated", self._handle_staging_update)

        self.ui_controller = controller
        self._controller_attached = True

    def _handle_staging_update(self, data):
        """Handle updates to the staging area"""
        if not self._ui_initialized:
            return

        # Clear the lists first
        self.staged_files.delete(0, END)
        self.unstaged_files.delete(0, END)

        # Update with the data from GitService
        for file in data.get("staged_files", []):
            self.staged_files.insert(END, file)

        for file in data.get("unstaged_files", []):
            self.unstaged_files.insert(END, file)

    def get_selected_unstaged_files(self):
        return [self.unstaged_files.get(i) for i in self.unstaged_files.curselection()]

    def get_selected_staged_files(self):
        return [self.staged_files.get(i) for i in self.staged_files.curselection()]

    def setup_staging_tab(self):
        """Create the split view for unstaged and staged changes"""
        # Split view for unstaged and staged changes
        self.staging_paned = PanedWindow(self.parent, orient="vertical")
        self.staging_paned.pack(fill="both", expand=True, padx=5, pady=5)

        # Unstaged changes frame
        self.unstaged_frame = LabelFrame(self.staging_paned, text="Unstaged Changes")
        self.staging_paned.add(self.unstaged_frame, weight=1)

        # Unstaged files list
        self.unstaged_files = Listbox(
            self.unstaged_frame,
            selectmode="extended",
            background="#1E1E1E",
            foreground="#D4D4D4",
            selectbackground="#264F78",
            selectforeground="#FFFFFF"
        )
        self.unstaged_files.pack(fill="both", expand=True, padx=5, pady=5)
        self.unstaged_files.bind("<Double-1>", self.stage_selected_file)

        # Unstaged buttons
        unstaged_buttons = Frame(self.unstaged_frame)
        unstaged_buttons.pack(fill="x", expand=False, padx=5, pady=5)

        # Button to stage selected files
        self.stage_selected_btn = Button(
            unstaged_buttons,
            text="Stage Selected",
            command=self.stage_selected_file
        )
        self.stage_selected_btn.pack(side="left", padx=2)

        # Button to stage all files
        self.stage_all_btn = Button(
            unstaged_buttons,
            text="Stage All",
            command=self.stage_all_files
        )
        self.stage_all_btn.pack(side="left", padx=2)

        # Button to discard selected changes
        self.discard_btn = Button(
            unstaged_buttons,
            text="Discard Selected",
            command=self.discard_selected_changes
        )
        self.discard_btn.pack(side="left", padx=2)

        # Button to edit .gitignore
        self.gitignore_btn = Button(
            unstaged_buttons,
            text="Edit .gitignore",
            command=self.edit_gitignore
        )
        self.gitignore_btn.pack(side="left", padx=2)

        # Staged changes frame
        self.staged_frame = LabelFrame(self.staging_paned, text="Staged Changes")
        self.staging_paned.add(self.staged_frame, weight=1)

        # Staged files list
        self.staged_files = Listbox(
            self.staged_frame,
            selectmode="extended",
            background="#1E1E1E",
            foreground="#D4D4D4",
            selectbackground="#264F78",
            selectforeground="#FFFFFF"
        )
        self.staged_files.pack(fill="both", expand=True, padx=5, pady=5)
        self.staged_files.bind("<Double-1>", self.unstage_selected_file)

        # Staged buttons
        staged_buttons = Frame(self.staged_frame)
        staged_buttons.pack(fill="x", expand=False, padx=5, pady=5)

        # Button to unstage selected files
        self.unstage_selected_btn = Button(
            staged_buttons,
            text="Unstage Selected",
            command=self.unstage_selected_file
        )
        self.unstage_selected_btn.pack(side="left", padx=2)

        # Button to unstage all files
        self.unstage_all_btn = Button(
            staged_buttons,
            text="Unstage All",
            command=self.unstage_all_files
        )
        self.unstage_all_btn.pack(side="left", padx=2)

        self._ui_initialized = True

    def setup_context_menus(self):
        """Set up right-click context menus for both lists"""
        # Create context menu for unstaged files
        self.unstaged_context_menu = Menu(self.unstaged_files, tearoff=0)
        self.unstaged_context_menu.add_command(
            label="Stage Selected",
            command=self.stage_selected_file
        )
        self.unstaged_context_menu.add_command(
            label="View Diff",
            command=self.view_unstaged_diff
        )
        self.unstaged_context_menu.add_separator()
        self.unstaged_context_menu.add_command(
            label="Discard Changes",
            command=self.discard_selected_changes
        )
        self.unstaged_context_menu.add_command(
            label="Add to .gitignore",
            command=self.add_to_gitignore
        )

        # Create context menu for staged files
        self.staged_context_menu = Menu(self.staged_files, tearoff=0)
        self.staged_context_menu.add_command(
            label="Unstage Selected",
            command=self.unstage_selected_file
        )
        self.staged_context_menu.add_command(
            label="View Diff",
            command=self.view_staged_diff
        )

        # Bind context menu to right-click
        self.unstaged_files.bind("<Button-3>", self.show_unstaged_context_menu)
        self.staged_files.bind("<Button-3>", self.show_staged_context_menu)

    def show_unstaged_context_menu(self, event):
        """Display the context menu for unstaged files on right-click."""
        try:
            # Select the item under the cursor
            index = self.unstaged_files.nearest(event.y)
            if index >= 0:
                self.unstaged_files.selection_clear(0, END)
                self.unstaged_files.selection_set(index)
                self.unstaged_files.activate(index)

            # Show the context menu
            self.unstaged_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            # Make sure to release the grab
            self.unstaged_context_menu.grab_release()

    def show_staged_context_menu(self, event):
        """Display the context menu for staged files on right-click."""
        try:
            # Select the item under the cursor
            index = self.staged_files.nearest(event.y)
            if index >= 0:
                self.staged_files.selection_clear(0, END)
                self.staged_files.selection_set(index)
                self.staged_files.activate(index)

            # Show the context menu
            self.staged_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            # Make sure to release the grab
            self.staged_context_menu.grab_release()

    def stage_selected_file(self, event=None):
        """Stage all selected files from the unstaged list."""
        selected_indices = self.unstaged_files.curselection()
        if not selected_indices:
            return

        # Use a copy of the selected items
        selected_files = [self.unstaged_files.get(i) for i in selected_indices]

        # Use the controller's direct method instead of execute_command
        if hasattr(self.ui_controller, 'stage_files'):
            self.ui_controller.stage_files(selected_files)
        else:
            # Fallback to command execution
            for file_path in selected_files:
                self.ui_controller.execute_command(f"add {file_path}")
            # Explicitly request a refresh
            self.ui_controller.refresh_staging_view()

    def unstage_selected_file(self, event=None):
        """Unstage all selected files from the staged list."""
        selected_indices = self.staged_files.curselection()
        if not selected_indices:
            return

        # Use a copy of the selected items
        selected_files = [self.staged_files.get(i) for i in selected_indices]

        # Use the controller's direct method
        if hasattr(self.ui_controller, 'unstage_files'):
            self.ui_controller.unstage_files(selected_files)
        else:
            # Fallback to command execution
            for file_path in selected_files:
                self.ui_controller.execute_command(f"reset -- {file_path}")
            # Explicitly request a refresh
            self.ui_controller.refresh_staging_view()

        

    def stage_all_files(self):
        """Stage all files in the unstaged list."""
        all_files = self.unstaged_files.get(0, END)
        if not all_files:
            return

        self.ui_controller.execute_command("add .")
        

    def unstage_all_files(self):
        """Unstage all files in the staged list."""
        all_files = self.staged_files.get(0, END)
        if not all_files:
            return

        self.ui_controller.execute_command("reset")
        

    def discard_selected_changes(self):
        """Discard changes for selected files in the unstaged list."""
        selected_indices = self.unstaged_files.curselection()
        if not selected_indices:
            return

        # Confirm discard action
        if not messagebox.askyesno("Discard Changes",
                                   "Are you sure you want to discard changes? This cannot be undone."):
            return

        # Use a copy of the selected items
        selected_files = [self.unstaged_files.get(i) for i in selected_indices]

        for file_path in selected_files:
            self.ui_controller.execute_command(f"checkout -- {file_path}")

        

    def view_unstaged_diff(self):
        """View diff for selected unstaged file"""
        selected = self.unstaged_files.curselection()
        if selected:
            file_path = self.unstaged_files.get(selected[0])
            self.ui_controller.view_file_diff(file_path, mode="Working Directory")

    def view_staged_diff(self):
        """View diff for selected staged file"""
        selected = self.staged_files.curselection()
        if selected:
            file_path = self.staged_files.get(selected[0])
            self.ui_controller.view_file_diff(file_path, mode="Staged Changes")

    def update_file_lists(self, unstaged_files=None, staged_files=None):
        """Update the file lists with new data"""
        if unstaged_files is not None:
            self.unstaged_files.delete(0, END)
            for file in unstaged_files:
                self.unstaged_files.insert(END, file)

        if staged_files is not None:
            self.staged_files.delete(0, END)
            for file in staged_files:
                self.staged_files.insert(END, file)

    def edit_gitignore(self):
        """Open the .gitignore file for editing"""
        self.ui_controller.edit_gitignore()

    def add_to_gitignore(self):
        """Add selected files to .gitignore"""
        selected_indices = self.unstaged_files.curselection()
        if not selected_indices:
            return

        selected_files = [self.unstaged_files.get(i) for i in selected_indices]
        self.ui_controller.add_to_gitignore(selected_files)