from tkinter import (
    Button,
    HORIZONTAL,
    LEFT,
    BOTH,
    RIGHT,
    X,
    Y,
    BOTTOM,
    W)
from src.controllers.menu_functions import open_search_window, open_search_replace_window
from src.models.file_operations import prompt_rename_file
from src.controllers.parameters import read_config_parameter

from src.controllers.menu_functions import (
    create_menu,
    run_icon,
    redo_icon,
    undo_icon,
    save_new_icon,
    save_icon,
    open_icon,
    open_script,
    save_script,
    save_as_new_script,
    cut,
    copy,
    paste)
from src.models.script_operations import (
    run_script_once,
    run_script_crontab,
    get_operative_system)
from src.views.edit_operations import undo, redo
from src.views.tree_functions import (
    item_opened,
    update_tree,
    on_item_select,
    on_double_click, show_context_menu)
from src.views.ui_elements import Tooltip, LineNumberCanvas
import customtkinter
from src.views.tk_utils import *
from src.controllers.file_operations import on_text_change


def create_app():
    print("app_layers: CREATE MENU TRIGGERED")
    create_menu()
    print("app_layers: CREATE CONTENT FILE WINDOW TRIGGERED")
    create_content_file_window()
    print("app_layers: CREATE CONTENT FILE WINDOW")
    create_filesystem_window()


def create_filesystem_window():
    tree_frame.grid_rowconfigure(0, weight=1)
    tree_frame.grid_columnconfigure(0, weight=1)
    vsb = customtkinter.CTkScrollbar(tree_frame, orientation="vertical", command=tree.yview)
    vsb.grid(row=0, column=1, sticky="ns")
    hsb = customtkinter.CTkScrollbar(tree_frame, orientation="horizontal", command=tree.xview)
    hsb.grid(row=1, column=0, sticky="ew")
    tree.grid(row=0, column=0, sticky="nsew")
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tree.heading("#0", text="", anchor=W)
    tree.column("#0", width=300, minwidth=200)
    tree.bind("<<TreeviewOpen>>", item_opened)
    tree.bind("<<TreeviewSelect>>", on_item_select)
    tree.bind("<Double-1>", on_double_click)
    tree.bind("<Button-3>", show_context_menu)
    print("CREATING FILESYSTEM VIEW")
    current_directory = read_config_parameter(
        "options.file_management.current_working_directory"
    )
    update_tree(current_directory)
    return filesystem_frm, update_tree


def create_content_file_window():
    global is_modified, line_numbers

    # Create the line numbers canvas
    line_numbers = LineNumberCanvas(script_text, width=30)
    line_numbers.grid(row=2, column=0, padx=0, pady=0, sticky="nsw")

    # Debug mouse wheel events
    # Handle mouse wheel events
    def on_mousewheel(event):
        # Calculate scroll direction
        if hasattr(event, 'delta'):
            # Windows style
            delta = -1 if event.delta > 0 else 1
        elif event.num == 4:
            # Linux scroll up
            delta = -1
        elif event.num == 5:
            # Linux scroll down
            delta = 1
        else:
            return

        # Scroll the text widget
        script_text.yview_scroll(delta, "units")
        # Update line numbers after scrolling
        # Redraw immediately for better responsiveness, then again after a short delay
        line_numbers.redraw()
        root.after(10, line_numbers.redraw)

        # Allow event to continue for proper scrollbar update
        return

    # Determine the actual text widget to bind events to (internal _textbox for CTkTextbox)
    target_widget = getattr(script_text, "_textbox", script_text)

    # Bind mouse wheel events
    target_widget.bind("<MouseWheel>", on_mousewheel)  # Windows
    target_widget.bind("<Button-4>", on_mousewheel)  # Linux up
    target_widget.bind("<Button-5>", on_mousewheel)  # Linux down

    # Handle keyboard navigation that may affect scrolling
    def on_key_scroll(event):
        # Schedule line numbers update after key navigation
        line_numbers.redraw()
        root.after(10, line_numbers.redraw)

    # Bind key navigation events
    for key in ("<Key-Up>", "<Key-Down>", "<Key-Prior>", "<Key-Next>", "<Key-Home>", "<Key-End>"):
        target_widget.bind(key, on_key_scroll, add="+")

    # Handle text widget resize
    def on_text_configure(event):
        root.after(10, line_numbers.redraw)

    target_widget.bind("<Configure>", on_text_configure, add="+")

    def show_context_menu(event):
        context_menu = Menu(root, tearoff=0)
        context_menu.add_command(
            label=localization_data["undo"], command=undo, accelerator="Ctrl+Z"
        )
        context_menu.add_command(
            label=localization_data["redo"], command=redo, accelerator="Ctrl+Y"
        )
        context_menu.add_separator()
        context_menu.add_command(
            label=localization_data["paste"], command=paste, accelerator="Ctrl+V"
        )
        context_menu.add_command(
            label=localization_data["copy"], command=copy, accelerator="Ctrl+C"
        )
        context_menu.add_command(
            label=localization_data["cut"], command=cut, accelerator="Ctrl+X"
        )
        context_menu.add_separator()
        find_submenu = Menu(menu, tearoff=0)
        context_menu.add_cascade(label="Find", menu=find_submenu)
        find_submenu.add_command(
            label="Find", command=open_search_window, compound="left", accelerator="Ctrl+F"
        )
        find_submenu.add_command(
            label="Find and Replace",
            command=open_search_replace_window,
            compound="left",
            accelerator="Ctrl+R")
        """git_submenu.add_command(label="Unstash Changes...", command=duplicate, compound='left',
                                accelerator='Ctrl+Alt+A')"""
        context_menu.post(event.x_root, event.y_root)
        context_menu.focus_set()

        def destroy_menu():
            """ ""\"
            destroy_menu

                    Args:
                        None

                    Returns:
                        None: Description of return value.
            ""\" """
            context_menu.unpost()

        context_menu.bind("<Leave>", lambda e: destroy_menu())
        context_menu.bind("<FocusOut>", lambda e: destroy_menu())

    def scroll_lines_up(event):
        script_text.yview_scroll(-5, "units")  # Scroll up 5 lines
        root.after(10, lambda: line_numbers.redraw())
        return "break"

    def scroll_lines_down(event):
        script_text.yview_scroll(5, "units")  # Scroll down 5 lines
        root.after(10, lambda: line_numbers.redraw())
        return "break"

    # Bind the scroll_lines functions
    target_widget.bind("<Control-Up>", scroll_lines_up)
    target_widget.bind("<Control-Down>", scroll_lines_down)

    # Show changes in text zone when line numbers width changes
    def show_changes_in_text_zone(event=None):
        offset = line_numbers.winfo_width() + 8
        script_text.grid(row=2, column=0, padx=(offset, 0), pady=0, sticky="nsew")

    line_numbers.bind("<Configure>", show_changes_in_text_zone)

    script_text.configure(fg_color="#1f1f1f", text_color="white")

    script_text.configure()

    target_widget.bind("<Button-3>", show_context_menu)
    target_widget.bind("<Key>", on_text_change)

    # Additional debugging for manual scrolling
    def scroll_lines_up(event):
        script_text.yview_scroll(-5, "units")
        # Update line numbers and scroll position
        root.after(10, line_numbers.redraw)
        return "break"

    def scroll_lines_down(event):
        script_text.yview_scroll(5, "units")
        # Update line numbers and scroll position
        root.after(10, line_numbers.redraw)
        return "break"

    # Bind the debug scroll functions
    target_widget.bind("<Control-Up>", scroll_lines_up)
    target_widget.bind("<Control-Down>", scroll_lines_down)

    # Ensure the line numbers are drawn initially
    root.after(100, line_numbers.redraw)

    # Start the synchronization loop
    root.after(1000, ensure_scroll_sync)

def scroll_lines_up(event):
    script_text.yview_scroll(-5, "units")  # Scroll up 5 lines
    root.after(10, lambda: line_numbers.redraw())
    return "break"


def scroll_lines_down(event):
    script_text.yview_scroll(5, "units")  # Scroll down 5 lines
    root.after(10, lambda: line_numbers.redraw())
    return "break"


def create_horizontal_scrollbar_lines():
    scrollbar_frm.grid(row=3, column=0, pady=0, sticky="ew")
    scrollbar = Scrollbar(root, orient=HORIZONTAL, command=script_text.xview)
    scrollbar.grid(row=3, column=0, sticky="ew")

    # Modified version that updates line numbers when horizontal scrolling happens
    def on_scroll(*args):
        script_text.xview(*args)
        update_line_numbers()
        return "break"

    scrollbar.configure(command=on_scroll)
    script_text.configure(xscrollcommand=scrollbar.set)


def update_line_numbers():
    """Direct update of line numbers"""
    global line_numbers
    if line_numbers:
        # Use after_idle to prevent update loops
        root.after_idle(line_numbers.redraw)


def ensure_scroll_sync():
    """Make sure text widget, scrollbar and line numbers stay in sync"""
    # This function can be called periodically to ensure synchronization
    global line_numbers
    if line_numbers:
        # Get current text widget view
        first, last = script_text.yview()
        # Update line numbers
        line_numbers.redraw()

    # Schedule next check
    root.after(500, ensure_scroll_sync)


