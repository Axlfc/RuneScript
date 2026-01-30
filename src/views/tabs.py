import os
import json
import customtkinter
import tkinter as tk
from tkinter import messagebox, END
from src.controllers.parameters import read_config_parameter, write_config_parameter

class EditorTab:
    def __init__(self, file_path=None, content="", is_modified=False, original_content=""):
        self.file_path = file_path
        self.is_modified = is_modified
        self.original_content = original_content
        self.content = content # This is used when the tab is not active
        self.textbox = None # The CTkTextbox widget if we decide to have one per tab

    def get_display_name(self):
        if not self.file_path:
            name = "Untitled"
        else:
            name = os.path.basename(self.file_path)

        if self.is_modified:
            return f"*{name}"
        return name

class TabManager:
    def __init__(self, root, container, on_tab_change_callback):
        self.root = root
        self.container = container # The frame where tabs are placed
        self.on_tab_change_callback = on_tab_change_callback
        self.tabs = []
        self.active_tab_index = -1

        # UI Components
        self.tab_bar_frame = customtkinter.CTkFrame(container, height=40)
        # We don't pack/grid here, let the caller handle it for better layout control

        self.right_arrow = customtkinter.CTkButton(self.tab_bar_frame, text=">", width=25, command=self.scroll_right)
        self.right_arrow.pack(side="right", padx=2)

        self.left_arrow = customtkinter.CTkButton(self.tab_bar_frame, text="<", width=25, command=self.scroll_left)
        self.left_arrow.pack(side="right", padx=2)

        # Scrollable container for tabs
        self.scroll_canvas = tk.Canvas(self.tab_bar_frame, height=35, highlightthickness=0)
        self.scroll_canvas.pack(side="left", fill="both", expand=True)

        self.tabs_container = customtkinter.CTkFrame(self.scroll_canvas, height=30)
        self.scroll_canvas.create_window((0, 0), window=self.tabs_container, anchor="nw")

        self.tabs_container.bind("<Configure>", lambda e: self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all")))

        self.session_file = os.path.join("data", "session.json")
        self.tab_buttons = []

    def scroll_left(self):
        self.scroll_canvas.xview_scroll(-1, "units")

    def scroll_right(self):
        self.scroll_canvas.xview_scroll(1, "units")

    def add_tab(self, file_path=None, content="", is_modified=False, original_content="", switch=True):
        # Check if already open
        if file_path:
            for i, tab in enumerate(self.tabs):
                if tab.file_path == file_path:
                    if switch:
                        self.switch_to_tab(i)
                    return tab

        from src.views.tk_utils import editor_state
        normalized_original = editor_state.normalize(original_content)
        new_tab = EditorTab(file_path, content, is_modified, normalized_original)
        self.tabs.append(new_tab)

        tab_idx = len(self.tabs) - 1

        if switch:
            self.switch_to_tab(tab_idx)
        else:
            self.refresh_tab_bar()

        return new_tab

    def create_tab_button(self):
        btn_frame = customtkinter.CTkFrame(self.tabs_container, corner_radius=4)

        # Use a button for the tab itself for better interaction
        tab_btn = customtkinter.CTkButton(btn_frame, text="", width=100, height=25,
                                          fg_color="transparent", text_color="white",
                                          anchor="w", corner_radius=4)
        tab_btn.pack(side="left", padx=(5, 0))
        tab_btn.bind("<Double-1>", lambda e: self.rename_tab())

        close_btn = customtkinter.CTkButton(btn_frame, text="x", width=20, height=20,
                                            fg_color="transparent", hover_color="#aa0000",
                                            text_color="white", corner_radius=10)
        close_btn.pack(side="left", padx=2)

        self.tab_buttons.append((btn_frame, tab_btn, close_btn))

    def refresh_colors(self):
        """Update colors of the tab bar components based on current theme."""
        is_dark = customtkinter.get_appearance_mode().lower() == "dark"
        theme = customtkinter.ThemeManager.theme

        # Get frame color for background
        bg_color = theme["CTkFrame"]["fg_color"][1 if is_dark else 0]
        self.scroll_canvas.configure(bg=bg_color)

        # Update each tab button colors
        for i, (btn_frame, tab_btn, close_btn) in enumerate(self.tab_buttons):
            if i < len(self.tabs):
                if i == self.active_tab_index:
                    # Active tab colors
                    active_color = theme["CTkButton"]["fg_color"][1 if is_dark else 0]
                    border_color = theme["CTkButton"]["border_color"][1 if is_dark else 0]
                    btn_frame.configure(fg_color=active_color, border_width=1, border_color=border_color)
                    tab_btn.configure(text_color=theme["CTkButton"]["text_color"][1 if is_dark else 0])
                    close_btn.configure(text_color=theme["CTkButton"]["text_color"][1 if is_dark else 0])
                else:
                    # Inactive tab colors
                    btn_frame.configure(fg_color="transparent", border_width=0)
                    tab_btn.configure(text_color=theme["CTkLabel"]["text_color"][1 if is_dark else 0])
                    close_btn.configure(text_color=theme["CTkLabel"]["text_color"][1 if is_dark else 0])

    def refresh_tab_bar(self):
        # Ensure we have enough buttons
        while len(self.tab_buttons) < len(self.tabs):
            self.create_tab_button()

        # Hide extra buttons
        for i in range(len(self.tabs), len(self.tab_buttons)):
            self.tab_buttons[i][0].pack_forget()

        # Update colors based on theme
        self.refresh_colors()

        # Update and show relevant buttons
        for i, tab in enumerate(self.tabs):
            btn_frame, tab_btn, close_btn = self.tab_buttons[i]
            btn_frame.pack(side="left", padx=2, pady=2)

            name = tab.get_display_name()
            tab_btn.configure(text=name, command=lambda i=i: self.switch_to_tab(i))
            close_btn.configure(command=lambda i=i: self.close_tab(i))

            # Update font weight
            if i == self.active_tab_index:
                tab_btn.configure(font=customtkinter.CTkFont(weight="bold"))
            else:
                tab_btn.configure(font=customtkinter.CTkFont(weight="normal"))

    def save_current_tab_state(self):
        if self.active_tab_index != -1 and self.active_tab_index < len(self.tabs):
            from src.views.tk_utils import script_text, editor_state
            current_tab = self.tabs[self.active_tab_index]
            current_tab.content = script_text.get("1.0", "end-1c")
            current_tab.is_modified = editor_state.is_modified
            current_tab.file_path = editor_state.file_name
            current_tab.original_content = editor_state.last_saved_content

    def switch_to_tab(self, index, save_current=True):
        if index < 0 or index >= len(self.tabs):
            return

        # Save current tab state before switching
        if save_current:
            self.save_current_tab_state()

        self.active_tab_index = index
        tab = self.tabs[index]

        # Notify application to update UI with new tab content
        self.on_tab_change_callback(tab)
        self.refresh_tab_bar()

    def close_tab(self, index):
        tab = self.tabs[index]

        # Save state if it's the active tab BEFORE any modifications to the list
        if index == self.active_tab_index:
            self.save_current_tab_state()

        if tab.is_modified:
            name = os.path.basename(tab.file_path) if tab.file_path else "Untitled"
            response = messagebox.askyesnocancel("Save Changes", f"Save changes to {name}?")
            if response is True:
                # Save and then close
                if index != self.active_tab_index:
                    self.switch_to_tab(index)
                from src.controllers.file_operations import save
                if not save():
                    return # Don't close if save failed
            elif response is None:
                return # Cancel close

        # Now it's safe to remove
        closed_tab = self.tabs.pop(index)
        if closed_tab.textbox:
            closed_tab.textbox.destroy()

        if not self.tabs:
            self.active_tab_index = -1
            self.add_tab() # Add a new empty tab
        else:
            # Adjust active_tab_index
            if self.active_tab_index > index:
                self.active_tab_index -= 1
            elif self.active_tab_index == index:
                # We closed the active tab
                if self.active_tab_index >= len(self.tabs):
                    self.active_tab_index = len(self.tabs) - 1

            # Switch to the (new) active tab WITHOUT saving the now-stale current content
            # into whatever tab happened to take the active slot
            self.switch_to_tab(self.active_tab_index, save_current=False)

        self.refresh_tab_bar()

    def rename_tab(self):
        from src.controllers.file_operations import prompt_rename_file
        prompt_rename_file()
        # After renaming, the active tab state should have been updated by file_operations
        self.refresh_tab_bar()

    def save_session(self):
        # Sync active tab content first
        if self.active_tab_index != -1:
            from src.views.tk_utils import script_text, editor_state
            current_tab = self.tabs[self.active_tab_index]
            current_tab.content = script_text.get("1.0", "end-1c")
            current_tab.is_modified = editor_state.is_modified
            current_tab.file_path = editor_state.file_name
            current_tab.original_content = editor_state.last_saved_content

        session_data = {
            "active_tab_index": self.active_tab_index,
            "tabs": []
        }
        for tab in self.tabs:
            session_data["tabs"].append({
                "file_path": tab.file_path,
                "is_modified": tab.is_modified,
                "content": tab.content if tab.is_modified else "",
                "original_content": tab.original_content
            })

        try:
            with open(self.session_file, "w") as f:
                json.dump(session_data, f, indent=4)
        except Exception as e:
            print(f"Error saving session: {e}")

    def load_session(self):
        if not os.path.exists(self.session_file):
            self.add_tab()
            return

        try:
            with open(self.session_file, "r") as f:
                session_data = json.load(f)

            tabs_data = session_data.get("tabs", [])
            if not tabs_data:
                self.add_tab()
                return

            for tab_data in tabs_data:
                file_path = tab_data.get("file_path")
                is_modified = tab_data.get("is_modified", False)
                content = tab_data.get("content", "")
                original_content = tab_data.get("original_content", "")

                # If it wasn't modified, we should reload from disk if path exists
                if not is_modified and file_path and os.path.exists(file_path):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            original_content = content
                    except:
                        pass

                self.add_tab(file_path, content, is_modified, original_content, switch=False)

            active_idx = session_data.get("active_tab_index", 0)
            if active_idx < 0 or active_idx >= len(self.tabs):
                active_idx = 0

            self.switch_to_tab(active_idx)

        except Exception as e:
            print(f"Error loading session: {e}")
            if not self.tabs:
                self.add_tab()
