from tkinter import Button, Checkbutton, Scrollbar, HORIZONTAL
from tkinter.ttk import Treeview

from src.controllers.tool_functions import find_text, open_search_replace_dialog
from src.models.file_operations import prompt_rename_file
from src.controllers.menu_functions import (create_menu, run_icon, redo_icon, undo_icon, save_new_icon, save_icon, \
    open_icon, open_script, save_script, save_as_new_script, update_modification_status, on_text_change, cut, copy,
                                            paste,
                                            duplicate)
from src.models.script_operations import (run_script_with_timeout, run_script_once, run_script_crontab,
                                          get_operative_system)
from src.views.edit_operations import undo, redo
from src.views.ui_elements import Tooltip, LineNumberCanvas
from src.views.tk_utils import *


def create_app():
    create_menu()
    create_body()
    create_footer()


def create_footer():
    # TODO: New footer line with line count and other information like UTF-8 and other information.
    create_execute_one_time_with_format()  # GNU/Linux only
    create_program_daily_with_format()  # GNU/Linux only


def create_body():
    create_content_file_window()
    # create_horizontal_scrollbar_lines()
    create_filesystem_window()


def create_footer_line():
    # TODO: print("Footer not seen")
    pass


def create_icon_buttons_line():
    pass


def create_open_script_line():
    """
        Creates the interface elements for opening a script file.

        This includes buttons and labels to facilitate the opening of script files from the file system into the application.

        Parameters:
        None

        Returns:
        None
    """
    script_frm.grid(row=1, column=0, pady=0, sticky="ew")
    script_frm.grid_columnconfigure(2, weight=1)  # Make column 2 (file name entry) expandable

    open_button = Button(script_frm, text=open_icon, command=open_script)
    open_button.grid(column=0, row=0)
    Tooltip(open_button, localization_data['open_script'])

    script_name_label.grid(column=2, row=0, sticky="we", padx=5, pady=5)  # Expand to the right
    script_name_label.bind("<Double-1>", lambda event: prompt_rename_file())
    Tooltip(script_name_label, localization_data['file_name'])

    save_button = Button(script_frm, text=save_icon, command=save_script)
    save_button.grid(column=3, row=0, sticky="e")  # Align to the right
    Tooltip(save_button, localization_data['save_script'])

    save_new_button = Button(script_frm, text=save_new_icon, command=save_as_new_script)
    save_new_button.grid(column=4, row=0, sticky="e")  # Align to the right
    Tooltip(save_new_button, localization_data['save_as_new_script'])

    undo_button = Button(script_frm, text=undo_icon, command=undo)
    undo_button.grid(column=5, row=0, sticky="e")  # Align to the right
    Tooltip(undo_button, localization_data['undo'])

    redo_button = Button(script_frm, text=redo_icon, command=redo)
    redo_button.grid(column=6, row=0, sticky="e")  # Align to the right
    Tooltip(redo_button, localization_data['redo'])


def create_filesystem_window():
    # global current_directory
    # Create the frame for the filesystem view
    print("CREATING FILESYSTEM VIEW")
    current_directory = directory_label.cget('text')
    # This is returning correctly the first path of current directory
    print(current_directory)
    # Create the tree view widget
    tree = Treeview(filesystem_frm)
    tree.grid(row=0, column=0, sticky="nsew")

    # Ensure that the frame can expand with the treeview
    filesystem_frm.grid_rowconfigure(0, weight=1)
    filesystem_frm.grid_columnconfigure(0, weight=1)

    # Function to update the tree view with directory contents
    def update_tree(path):
        tree.delete(*tree.get_children())
        for entry in os.listdir(path):
            abs_path = os.path.join(path, entry)
            parent_id = ''

            if os.path.isdir(abs_path):
                parent_id = tree.insert('', 'end', text=entry, open=True)
                populate_tree(parent_id, abs_path)
            else:
                tree.insert('', 'end', text=entry)

    # Recursive function to populate the tree view
    def populate_tree(parent_id, path):
        for entry in os.listdir(path):
            abs_path = os.path.join(path, entry)
            if os.path.isdir(abs_path):
                oid = tree.insert(parent_id, 'end', text=entry, open=False)
                populate_tree(oid, abs_path)
            else:
                tree.insert(parent_id, 'end', text=entry)

    return filesystem_frm, update_tree


def create_content_file_window():
    """
    Sets up the main text area for file content display and editing.

    This function is responsible for initializing and configuring the main text area where the content of opened files
    is displayed and can be edited by the user.

    Parameters:
    None

    Returns:
    None
    """
    original_text = script_text.get("1.0", "end-1c")  # Store the original text of the file

    line_numbers = LineNumberCanvas(script_text, width=0)
    line_numbers.grid(row=2, column=0, padx=0, pady=0, sticky="nsw")

    def show_context_menu(event):
        global is_modified
        # TODO: Locales
        # Create the context menu
        context_menu = Menu(root, tearoff=0)
        context_menu.add_command(label=localization_data['undo'], command=undo, accelerator='Ctrl+Z')
        context_menu.add_command(label=localization_data['redo'], command=redo, accelerator='Ctrl+Y')

        context_menu.add_separator()
        context_menu.add_command(label=localization_data['paste'], command=paste, accelerator='Ctrl+V')
        context_menu.add_command(label=localization_data['copy'], command=copy, accelerator='Ctrl+C')
        context_menu.add_command(label=localization_data['cut'], command=cut, accelerator='Ctrl+X')
        # context_menu.add_command(label=localization_data['duplicate'], command=duplicate, accelerator='Ctrl+D')
        # context_menu.add_separator()
        # context_menu.add_command(label="Go to line...", command=duplicate, accelerator='Ctrl+G')
        context_menu.add_separator()
        #  context_menu.add_command(label="Auto-complete", command=duplicate, compound='left', accelerator='Ctrl+Space')

        find_submenu = Menu(menu, tearoff=0)
        context_menu.add_cascade(label="Find", menu=find_submenu)

        find_submenu.add_command(label="Find", command=find_text, compound='left', accelerator='Ctrl+F')
        find_submenu.add_command(label="Find and Replace", command=open_search_replace_dialog, compound='left', accelerator='Ctrl+R')

        #context_menu.add_separator()
        #context_menu.add_command(label="Run", command=duplicate, accelerator='F5')
        #context_menu.add_command(label="Debug", command=duplicate, accelerator='F9')
        #context_menu.add_command(label="Run Preferences", command=duplicate, accelerator='F10')
        #context_menu.add_separator()
        #open_in_submenu = Menu(menu, tearoff=0)
        #context_menu.add_cascade(label="Open in", menu=open_in_submenu)
        #open_in_submenu.add_command(label="Explorer", command=duplicate, compound='left', accelerator='Ctrl+F')
        #open_in_submenu.add_command(label="Terminal", command=duplicate, compound='left', accelerator='Ctrl+R')
        #context_menu.add_separator()
        #git_submenu = Menu(menu, tearoff=0)
        #context_menu.add_cascade(label="Git", menu=git_submenu, accelerator='Ctl+Alt+G')
        #git_submenu.add_command(label="Commit File...", command=duplicate, compound='left', accelerator='Ctrl+Alt+C')
        #git_submenu.add_command(label="Add", command=duplicate, compound='left', accelerator='Ctrl+Alt+A')
        #git_submenu.add_separator()
        #git_submenu.add_command(label="Blame", command=duplicate, compound='left', accelerator='Ctrl+Alt+A')
        #git_submenu.add_command(label="Diff", command=duplicate, compound='left', accelerator='Ctrl+Alt+A')
        #git_submenu.add_separator()
        #git_submenu.add_command(label="Push...", command=duplicate, compound='left', accelerator='Ctrl+Alt+A')
        #git_submenu.add_command(label="Pull...", command=duplicate, compound='left', accelerator='Ctrl+Alt+A')
        #git_submenu.add_command(label="Fetch", command=duplicate, compound='left', accelerator='Ctrl+Alt+A')
        #git_submenu.add_separator()
        #git_submenu.add_command(label="Merge...", command=duplicate, compound='left', accelerator='Ctrl+Alt+A')
        #git_submenu.add_command(label="Rebase...", command=duplicate, compound='left', accelerator='Ctrl+Alt+A')
        #git_submenu.add_separator()
        #git_submenu.add_command(label="Branches", command=duplicate, compound='left', accelerator='Ctrl+Alt+A')
        #git_submenu.add_command(label="New Branch...", command=duplicate, compound='left', accelerator='Ctrl+Alt+A')
        #git_submenu.add_command(label="Delete Branch...", command=duplicate, compound='left', accelerator='Ctrl+Alt+A')
        #git_submenu.add_command(label="Reset HEAD...", command=duplicate, compound='left', accelerator='Ctrl+Alt+A')
        #git_submenu.add_separator()
        #git_submenu.add_command(label="Stash Changes...", command=duplicate, compound='left', accelerator='Ctrl+Alt+A')
        '''git_submenu.add_command(label="Unstash Changes...", command=duplicate, compound='left',
                                accelerator='Ctrl+Alt+A')'''
        #git_submenu.add_separator()
        #git_submenu.add_command(label="Manage Remotes...", command=duplicate, compound='left', accelerator='Ctrl+Alt+A')
        #git_submenu.add_command(label="Clone...", command=duplicate, compound='left', accelerator='Ctrl+Alt+A')
        #context_menu.add_separator()
        #context_menu.add_command(label="Clear script", command=duplicate, compound='left', accelerator='Ctrl+L')

        # Post the context menu at the cursor location
        context_menu.post(event.x_root, event.y_root)

        # Give focus to the context menu
        context_menu.focus_set()

        def destroy_menu():
            context_menu.unpost()

        # Bind the <Leave> event to destroy the context menu when the mouse cursor leaves it
        context_menu.bind("<Leave>", lambda e: destroy_menu())

        # Bind the <FocusOut> event to destroy the context menu when it loses focus
        context_menu.bind("<FocusOut>", lambda e: destroy_menu())

    def show_changes_in_text_zone(event=None):
        ''' Configure script_text grid to accommodate line numbers '''
        offset = line_numbers.winfo_width() + 8  # Add some padding
        script_text.grid(row=2, column=0, padx=(offset, 0), pady=0, sticky="nsew")

    # Bind the function to the event of line_numbers widget configuration change
    line_numbers.bind("<Configure>", show_changes_in_text_zone)

    script_text.configure(bg="#1f1f1f", fg="white")
    script_text.config(insertbackground='#F0F0F0', selectbackground='#4d4d4d')

    script_text.bind("<Button-3>", show_context_menu)
    script_text.bind("<Key>", update_modification_status)  # Add this line to track text insertion
    script_text.bind("<<Modified>>", on_text_change)

    status_bar = Label(frm, text="Status Bar")

    is_modified = False

    # Add Keyboard Shortcuts Here
    #script_text.bind("<Control-z>", undo)
    #script_text.bind("<Control-y>", redo)


def create_horizontal_scrollbar_lines():
    """
    Creates the horizontal scrollbar for the script_text widget.

    This function adds a horizontal scrollbar to the script_text widget, allowing users to scroll horizontally
    through the text content.

    Parameters:
    None

    Returns:
    None
    """
    scrollbar_frm.grid(row=3, column=0, pady=0, sticky="ew")  # Set sticky to "ew" to fill horizontally
    scrollbar = Scrollbar(root, orient=HORIZONTAL, command=script_text.xview)
    scrollbar.grid(row=3, column=0, sticky="ew")
    script_text.config(xscrollcommand=scrollbar.set)


def create_execute_one_time_with_format():
    """
        Sets up the interface elements for scheduling a one-time script execution.

        This function allows users to schedule a script to be run at a specific time, enhancing the scheduler
        capabilities of the application.

        Parameters:
        None

        Returns:
        None
    """
    if get_operative_system() != "Windows":
        one_time_frm.grid(row=8, column=0, pady=0, sticky="nsew")

        Label(one_time_frm, text=localization_data['scheduled_script_execution']).grid(row=0, column=0, sticky="e", padx=5, pady=0)

        date_entry = Entry(one_time_frm, width=15)
        date_entry.grid(column=1, row=0, padx=(10, 0))
        Tooltip(date_entry, localization_data['time_format'])

        run_button = Button(one_time_frm, text=run_icon, command=lambda: run_script_once(date_entry.get()))
        run_button.grid(row=0, column=2, sticky="e", padx=15, pady=0)
        Tooltip(run_button, localization_data['use_at_command'])


def create_program_daily_with_format():
    """
        Creates UI components for setting up daily scheduled script execution.

        This interface enables users to schedule scripts to run daily at specified times, supporting routine
        automation tasks.

        Parameters:
        None

        Returns:
        None
    """
    if get_operative_system() != "Windows":
        daily_frm.grid(row=9, column=0, pady=0, sticky="ew")

        Label(daily_frm, text=localization_data['daily_script_scheduling']).grid(row=0, column=0, sticky="w", padx=5, pady=0)

        minute_entry = Entry(daily_frm, width=2)
        minute_entry.grid(column=1, row=0, padx=(10, 0))
        Tooltip(minute_entry, localization_data['every_minute'])

        hour_entry = Entry(daily_frm, width=2)
        hour_entry.grid(column=2, row=0, padx=(10, 0))
        Tooltip(hour_entry, localization_data['every_hour'])

        day_entry = Entry(daily_frm, width=2)
        day_entry.grid(column=3, row=0, padx=(10, 0))
        Tooltip(day_entry, localization_data['every_day'])

        month_entry = Entry(daily_frm, width=2)
        month_entry.grid(column=4, row=0, padx=(10, 0))
        Tooltip(month_entry, localization_data['every_month'])

        day_of_the_week_entry = Entry(daily_frm, width=2)
        day_of_the_week_entry.grid(column=5, row=0, padx=(10, 0))
        Tooltip(day_of_the_week_entry, localization_data['every_day_of_week'])

        run_button = Button(
            daily_frm, text=run_icon,
            command=lambda: run_script_crontab(minute_entry.get(), hour_entry.get(), day_entry.get(), month_entry.get(), day_of_the_week_entry.get())
        )
        run_button.grid(row=0, column=6, sticky="e", padx=15, pady=0)
        Tooltip(run_button, localization_data['utilize_crontab'])

