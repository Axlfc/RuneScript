from tkinter import (
    Button,
    Scrollbar,
    HORIZONTAL,
    LEFT,
    BOTH,
    RIGHT,
    X,
    Y,
    BOTTOM,
    W,
)
from src.controllers.menu_functions import open_search_window, open_search_replace_window
from src.models.file_operations import prompt_rename_file
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
    paste,
)
from src.models.script_operations import (
    run_script_once,
    run_script_crontab,
    get_operative_system,
)
from src.views.edit_operations import undo, redo
from src.views.tree_functions import (
    item_opened,
    update_tree,
    on_item_select,
    on_double_click, show_context_menu,
)
from src.views.ui_elements import Tooltip, LineNumberCanvas
from src.views.tk_utils import *
from src.controllers.file_operations import on_text_change, update_line_numbers


def create_app():
    create_menu()
    create_content_file_window()
    create_filesystem_window()


def create_filesystem_window():
    vsb = Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    vsb.pack(side=RIGHT, fill=Y)
    hsb = Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
    hsb.pack(side=BOTTOM, fill=X)
    tree.pack(side=LEFT, fill=BOTH, expand=True)
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
    original_text = script_text.get("1.0", "end-1c")

    # Create the line numbers canvas
    line_numbers = LineNumberCanvas(script_text, width=30)
    line_numbers.grid(row=2, column=0, padx=0, pady=0, sticky="nsw")

    # Create a flag to prevent update loops
    update_in_progress = False

    # Create vertical scrollbar with special handling
    vsb = Scrollbar(frm, orient="vertical")
    vsb.grid(row=2, column=1, sticky="ns")

    # Create a wrapper function for the scrollbar command
    def scrollbar_command(*args):
        nonlocal update_in_progress
        if update_in_progress:
            return
        update_in_progress = True
        script_text.yview(*args)
        # Use after to break the potential recursion chain
        root.after(10, lambda: line_numbers.redraw())
        update_in_progress = False

    # Set the command to our wrapper
    vsb.config(command=scrollbar_command)

    # Create a wrapper for the text widget's scrollbar communication
    def yscroll_set(*args):
        nonlocal update_in_progress
        if update_in_progress:
            return
        update_in_progress = True
        vsb.set(*args)
        # Use after to break the potential recursion chain
        root.after(10, lambda: line_numbers.redraw())
        update_in_progress = False

    # Configure the text widget to use our wrapper
    script_text.config(yscrollcommand=yscroll_set)

    # Define scroll handler for mouse wheel and keyboard events
    def on_scroll(event=None):
        # Use after to break potential recursion chain
        root.after(10, lambda: line_numbers.redraw())
        # Don't return anything to allow normal event handling

    # Bind to events that might affect scroll position
    script_text.bind("<MouseWheel>", on_scroll)
    script_text.bind("<Button-4>", on_scroll)  # Linux scroll up
    script_text.bind("<Button-5>", on_scroll)  # Linux scroll down
    script_text.bind("<Key-Up>", on_scroll)
    script_text.bind("<Key-Down>", on_scroll)
    script_text.bind("<Key-Prior>", on_scroll)  # Page Up
    script_text.bind("<Key-Next>", on_scroll)  # Page Down
    script_text.bind("<Key-Home>", on_scroll)  # Home
    script_text.bind("<Key-End>", on_scroll)  # End

    # Use a debounced configure handler to prevent excessive updates
    last_configure_id = None

    def on_configure(event=None):
        nonlocal last_configure_id
        if last_configure_id:
            root.after_cancel(last_configure_id)
        last_configure_id = root.after(50, lambda: line_numbers.redraw())

    # Make sure line numbers update when window size changes, with debounce
    script_text.bind("<Configure>", on_configure)

    def show_context_menu(event):
        """ ""\"
        show_context_menu

            Args:
                event (Any): Description of event.

            Returns:
                None: Description of return value.
        ""\" """
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
            accelerator="Ctrl+R",
        )
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
    script_text.bind("<Control-Up>", scroll_lines_up)
    script_text.bind("<Control-Down>", scroll_lines_down)

    # Show changes in text zone when line numbers width changes
    def show_changes_in_text_zone(event=None):
        offset = line_numbers.winfo_width() + 8
        script_text.grid(row=2, column=0, padx=(offset, 0), pady=0, sticky="nsew")

    line_numbers.bind("<Configure>", show_changes_in_text_zone)

    script_text.configure(bg="#1f1f1f", fg="white")
    script_text.config(insertbackground="#F0F0F0", selectbackground="#4d4d4d")
    script_text.bind("<Button-3>", show_context_menu)
    script_text.bind("<Key>", on_text_change)

    status_bar = Label(frm, text="Status Bar")

    # Call line_numbers.redraw() initially to make sure they're shown
    root.after(100, lambda: line_numbers.redraw())


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

    scrollbar.config(command=on_scroll)
    script_text.config(xscrollcommand=scrollbar.set)