from tkinter import (
    Button,
    Checkbutton,
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
from tkinter.ttk import Treeview
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
    duplicate,
)
from src.models.script_operations import (
    run_script_with_timeout,
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
from src.controllers.file_operations import on_text_change


def create_app():
    """ ""\"
    create_app

    Args:
        None

    Returns:
        None: Description of return value.
    ""\" """
    create_menu()
    create_body()
    create_footer()


def create_footer():
    """ ""\"
    create_footer

    Args:
        None

    Returns:
        None: Description of return value.
    ""\" """
    create_execute_one_time_with_format()
    create_program_daily_with_format()


def create_body():
    """ ""\"
    create_body

    Args:
        None

    Returns:
        None: Description of return value.
    ""\" """
    create_content_file_window()
    create_filesystem_window()


def create_footer_line():
    """ ""\"
    create_footer_line

    Args:
        None

    Returns:
        None: Description of return value.
    ""\" """
    pass


def create_icon_buttons_line():
    """ ""\"
    create_icon_buttons_line

    Args:
        None

    Returns:
        None: Description of return value.
    ""\" """
    pass


def create_open_script_line():
    """ ""\"
    Creates the interface elements for opening a script file.

    This includes buttons and labels to facilitate the opening of script files from the file system into the application.

    Parameters:
    None

    Returns:
    None
    ""\" """
    script_frm.grid(row=1, column=0, pady=0, sticky="ew")
    script_frm.grid_columnconfigure(2, weight=1)
    open_button = Button(script_frm, text=open_icon, command=open_script)
    open_button.grid(column=0, row=0)
    Tooltip(open_button, localization_data["open_script"])
    script_name_label.grid(column=2, row=0, sticky="we", padx=5, pady=5)
    script_name_label.bind("<Double-1>", lambda event: prompt_rename_file())
    Tooltip(script_name_label, localization_data["file_name"])
    save_button = Button(script_frm, text=save_icon, command=save_script)
    save_button.grid(column=3, row=0, sticky="e")
    Tooltip(save_button, localization_data["save_script"])
    save_new_button = Button(script_frm, text=save_new_icon, command=save_as_new_script)
    save_new_button.grid(column=4, row=0, sticky="e")
    Tooltip(save_new_button, localization_data["save_as_new_script"])
    undo_button = Button(script_frm, text=undo_icon, command=undo)
    undo_button.grid(column=5, row=0, sticky="e")
    Tooltip(undo_button, localization_data["undo"])
    redo_button = Button(script_frm, text=redo_icon, command=redo)
    redo_button.grid(column=6, row=0, sticky="e")
    Tooltip(redo_button, localization_data["redo"])


def create_filesystem_window():
    """ ""\"
    create_filesystem_window

    Args:
        None

    Returns:
        None: Description of return value.
    ""\" """
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
    global is_modified
    original_text = script_text.get("1.0", "end-1c")
    line_numbers = LineNumberCanvas(script_text, width=0)
    line_numbers.grid(row=2, column=0, padx=0, pady=0, sticky="nsw")

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

    def show_changes_in_text_zone(event=None):
        """ ""\"
        Configure script_text grid to accommodate line numbers
        ""\" """
        offset = line_numbers.winfo_width() + 8
        script_text.grid(row=2, column=0, padx=(offset, 0), pady=0, sticky="nsew")

    line_numbers.bind("<Configure>", show_changes_in_text_zone)
    script_text.configure(bg="#1f1f1f", fg="white")
    script_text.config(insertbackground="#F0F0F0", selectbackground="#4d4d4d")
    script_text.bind("<Button-3>", show_context_menu)
    script_text.bind("<Key>", on_text_change)
    status_bar = Label(frm, text="Status Bar")


def create_horizontal_scrollbar_lines():
    """ ""\"
    Creates the horizontal scrollbar for the script_text widget.

    This function adds a horizontal scrollbar to the script_text widget, allowing users to scroll horizontally
    through the text content.

    Parameters:
    None

    Returns:
    None
    ""\" """
    scrollbar_frm.grid(row=3, column=0, pady=0, sticky="ew")
    scrollbar = Scrollbar(root, orient=HORIZONTAL, command=script_text.xview)
    scrollbar.grid(row=3, column=0, sticky="ew")
    script_text.config(xscrollcommand=scrollbar.set)


def create_execute_one_time_with_format():
    """ ""\"
    Sets up the interface elements for scheduling a one-time script execution.

    This function allows users to schedule a script to be run at a specific time, enhancing the scheduler
    capabilities of the application.

    Parameters:
    None

    Returns:
    None
    ""\" """
    if get_operative_system() != "Windows":
        one_time_frm.grid(row=8, column=0, pady=0, sticky="nsew")
        Label(one_time_frm, text=localization_data["scheduled_script_execution"]).grid(
            row=0, column=0, sticky="e", padx=5, pady=0
        )
        date_entry = Entry(one_time_frm, width=15)
        date_entry.grid(column=1, row=0, padx=(10, 0))
        Tooltip(date_entry, localization_data["time_format"])
        run_button = Button(
            one_time_frm,
            text=run_icon,
            command=lambda: run_script_once(date_entry.get()),
        )
        run_button.grid(row=0, column=2, sticky="e", padx=15, pady=0)
        Tooltip(run_button, localization_data["use_at_command"])


def create_program_daily_with_format():
    """ ""\"
    Creates UI components for setting up daily scheduled script execution.

    This interface enables users to schedule scripts to run daily at specified times, supporting routine
    automation tasks.

    Parameters:
    None

    Returns:
    None
    ""\" """
    if get_operative_system() != "Windows":
        daily_frm.grid(row=9, column=0, pady=0, sticky="ew")
        Label(daily_frm, text=localization_data["daily_script_scheduling"]).grid(
            row=0, column=0, sticky="w", padx=5, pady=0
        )
        minute_entry = Entry(daily_frm, width=2)
        minute_entry.grid(column=1, row=0, padx=(10, 0))
        Tooltip(minute_entry, localization_data["every_minute"])
        hour_entry = Entry(daily_frm, width=2)
        hour_entry.grid(column=2, row=0, padx=(10, 0))
        Tooltip(hour_entry, localization_data["every_hour"])
        day_entry = Entry(daily_frm, width=2)
        day_entry.grid(column=3, row=0, padx=(10, 0))
        Tooltip(day_entry, localization_data["every_day"])
        month_entry = Entry(daily_frm, width=2)
        month_entry.grid(column=4, row=0, padx=(10, 0))
        Tooltip(month_entry, localization_data["every_month"])
        day_of_the_week_entry = Entry(daily_frm, width=2)
        day_of_the_week_entry.grid(column=5, row=0, padx=(10, 0))
        Tooltip(day_of_the_week_entry, localization_data["every_day_of_week"])
        run_button = Button(
            daily_frm,
            text=run_icon,
            command=lambda: run_script_crontab(
                minute_entry.get(),
                hour_entry.get(),
                day_entry.get(),
                month_entry.get(),
                day_of_the_week_entry.get(),
            ),
        )
        run_button.grid(row=0, column=6, sticky="e", padx=15, pady=0)
        Tooltip(run_button, localization_data["utilize_crontab"])
