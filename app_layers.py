from tkinter import Button, Checkbutton

from file_operations import select_directory
from menu_functions import run_icon, redo_icon, undo_icon, save_new_icon, save_icon, open_icon, house_icon, \
    open_script, save_script, save_as_new_script, update_modification_status, set_modified_status, on_text_change
from script_operations import see_stderr, see_stdout, run_script, run_script_with_timeout, run_script_once, \
    run_script_crontab, get_operative_system, run_script_windows
from src.localization import localization_data
from ui_elements import Tooltip
from tk_utils import *


def undo():
    """
        Reverts the last action taken in the script text editor.

        This function undoes the last change made to the text in the script editor, allowing for simple
        mistake correction.

        Parameters:
        None

        Returns:
        None
    """
    print("Undo function called.")
    script_text.edit_undo()


def redo():
    """
        Redoes the last action that was undone in the script text editor.

        If an action was undone using the undo function, this function allows the user to redo that action.

        Parameters:
        None

        Returns:
        None
    """
    print("Redo function called.")
    script_text.edit_redo()


def cut():
    """
        Cuts the selected text from the script editor to the clipboard.

        This function removes the currently selected text from the document and places it on the clipboard,
        allowing it to be pasted elsewhere.

        Parameters:
        None

        Returns:
        None
    """
    #set_modified_status(True)
    script_text.event_generate("<<Cut>>")


def copy():
    """
        Copies the selected text from the script editor to the clipboard.

        This function copies the currently selected text to the clipboard without removing it from the document.

        Parameters:
        None

        Returns:
        None
    """
    # set_modified_status(True)
    script_text.event_generate("<<Copy>>")


def paste():
    """
        Pastes text from the clipboard into the script editor at the cursor's current location.

        This function inserts the contents of the clipboard into the document at the current cursor position.

        Parameters:
        None

        Returns:
        None
    """
    # set_modified_status(True)
    script_text.event_generate("<<Paste>>")


def duplicate():
    """
        Duplicates the selected text in the script editor.

        This function creates a copy of the selected text and inserts it immediately after the current selection.

        Parameters:
        None

        Returns:
        None
        """
    # set_modified_status(True)
    script_text.event_generate("<<Duplicate>>")


def create_directory_line():
    """
        Creates and displays the directory selection interface in the application.

        This interface element allows users to select and display the current working directory, facilitating
        the process of opening and saving files in the chosen directory.

        Parameters:
        None

        Returns:
        None
    """
    global current_directory
    frm.grid(row=0, column=0, pady=0, sticky="ew")  # Set sticky to "ew" to fill horizontally
    # Configure grid weights for the columns
    frm.columnconfigure(0, weight=0)  # First column doesn't expand
    frm.columnconfigure(1, weight=1)  # Second column expands

    directory_button = Button(frm, text=house_icon, command=select_directory)
    directory_button.grid(column=0, row=0, sticky="w")
    Tooltip(directory_button, localization_data['choose_working_directory'])

    directory_label.grid(column=1, row=0, padx=5, sticky="ew")  # Set sticky to "ew" to fill horizontally
    Tooltip(directory_label, localization_data['current_directory'])


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

    def show_context_menu(event):
        # Create the context menu
        context_menu = Menu(root, tearoff=0)
        context_menu.add_command(label=localization_data[localization_data['cut']], command=cut)
        context_menu.add_command(label=localization_data[localization_data['copy']], command=copy)
        context_menu.add_command(label=localization_data[localization_data['paste']], command=paste)
        context_menu.add_command(label=localization_data[localization_data['duplicate']], command=duplicate)

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

    script_text.grid(row=2, column=0, padx=0, pady=0, sticky="nsew")
    script_text.configure(bg="#1f1f1f", fg="white")
    script_text.config(insertbackground='#F0F0F0', selectbackground='#4d4d4d')
    script_text.bind("<Button-3>", show_context_menu)
    script_text.bind("<Key>", update_modification_status)  # Add this line to track text insertion
    script_text.bind("<<Modified>>", on_text_change)


def create_arguments_lines():
    """
        Creates the interface for entering script execution arguments.

        This part of the UI allows users to input arguments that will be passed to scripts when they are run, enhancing the
        flexibility and usability of script execution.

        Parameters:
        None

        Returns:
        None
    """
    content_frm.grid(row=3, column=0, pady=0, sticky="ew")  # Set sticky to "ew" to fill horizontally

    entry_arguments_label = Label(content_frm, text=localization_data['entry_arguments'])
    entry_arguments_label.grid(row=0, column=0, padx=5, pady=0, sticky="w")

    entry_placeholder = ""  # Enter arguments...
    entry_arguments_entry.insert(0, entry_placeholder)
    entry_arguments_entry.grid(row=0, column=1, sticky="e")
    Tooltip(entry_arguments_entry, localization_data['enter_arguments'])

    generate_stdin_check = Checkbutton(content_frm, text=localization_data['stdout'], variable=generate_stdin)
    generate_stdin_check.grid(row=0, column=2, sticky="e")  # sticky to "e" for right alignment
    Tooltip(generate_stdin_check, localization_data['generate_stdout'])

    see_stderr_check = Checkbutton(content_frm, text=localization_data['stderr'], variable=generate_stdin_err)
    see_stderr_check.grid(row=0, column=3, padx=10, sticky="e")  # Set sticky to "e" for right alignment
    Tooltip(see_stderr_check, localization_data['generate_stderr'])

    stdout_button = Button(content_frm, text=localization_data['see_stdout'], command=see_stdout)
    stdout_button.grid(column=1, row=1, sticky="e")  # Align to the right
    Tooltip(stdout_button, localization_data['see_stdout_tooltip'])

    stderr_button = Button(content_frm, text=localization_data['see_stderr'], command=see_stderr)
    stderr_button.grid(column=2, row=1, sticky="e")  # Align to the right
    Tooltip(stderr_button, localization_data['see_stderr_tooltip'])


def create_immediately_run_line():
    """
        Sets up the interface for immediate script execution.

        This function adds a button or interface element that allows users to run the currently open script instantly.

        Parameters:
        None

        Returns:
        None
    """
    if get_operative_system() != "Windows":
        run_frm.grid(row=4, column=0, pady=0, sticky="nsew")  # Set sticky to "e" for right alignment

        Label(run_frm, text=localization_data['run_inmediately']).grid(row=0, column=0, sticky="e", padx=5, pady=0)
        run_button = Button(run_frm, text=run_icon, command=run_script)
        run_button.grid(row=0, column=1, sticky="e", padx=5, pady=0)
        Tooltip(run_button, localization_data['run_script'])
    else:
        run_frm.grid(row=4, column=0, pady=0, sticky="nsew")  # Set sticky to "e" for right alignment

        Label(run_frm, text=localization_data['run_inmediately']).grid(row=0, column=0, sticky="e", padx=5, pady=0)
        run_button = Button(run_frm, text=run_icon, command=run_script_windows)
        run_button.grid(row=0, column=1, sticky="e", padx=5, pady=0)
        Tooltip(run_button, localization_data['run_script'])


def create_execute_in_line():
    """
        Creates the UI components for executing a script with a timeout.

        This part of the interface allows the user to specify a timeout duration for script execution, providing
        additional control over how scripts are run.

        Parameters:
        None

        Returns:
        None
    """
    if get_operative_system() != "Windows":
        line_frm.grid(row=5, column=0, pady=0, sticky="nsew")

        Label(line_frm, text=localization_data['script_timeout']).grid(row=0, column=0, sticky="e", padx=5, pady=0)

        seconds_entry = Entry(line_frm, width=15)
        seconds_entry.grid(column=1, row=0, padx=(10, 0))
        Tooltip(seconds_entry, localization_data['number_of_seconds'])

        run_button = Button(line_frm,
                            text=run_icon,
                            command=lambda: run_script_with_timeout(timeout_seconds=float(seconds_entry.get()))
                            )
        run_button.grid(row=0, column=2, sticky="e", padx=15, pady=0)
        Tooltip(run_button, localization_data['set_duration_for_script_execution'])
    else:
        line_frm.grid(row=5, column=0, pady=0, sticky="nsew")

        Label(line_frm, text=localization_data['script_timeout']).grid(row=0, column=0, sticky="e", padx=5, pady=0)

        seconds_entry = Entry(line_frm, width=15)
        seconds_entry.grid(column=1, row=0, padx=(10, 0))
        Tooltip(seconds_entry, localization_data['number_of_seconds'])

        run_button = Button(line_frm,
                            text=run_icon,
                            command=lambda: run_script_with_timeout(timeout_seconds=float(seconds_entry.get()))
                            )
        run_button.grid(row=0, column=2, sticky="e", padx=15, pady=0)
        Tooltip(run_button, localization_data['set_duration_for_script_execution'])


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
        one_time_frm.grid(row=6, column=0, pady=0, sticky="nsew")

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
        daily_frm.grid(row=7, column=0, pady=0, sticky="ew")

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