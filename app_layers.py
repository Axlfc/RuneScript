from tkinter import Button, Checkbutton

from file_operations import select_directory
from menu_functions import run_icon, redo_icon, undo_icon, save_new_icon, save_icon, open_icon, house_icon, \
    open_script, save_script, save_as_new_script, update_modification_status, set_modified_status
from script_operations import see_stderr, see_stdout, run_script, run_script_with_timeout, run_script_once, \
    run_script_crontab
from ui_elements import Tooltip
from tk_utils import *


def undo():
    print("Undo function called.")
    script_text.edit_undo()


def redo():
    print("Redo function called.")
    script_text.edit_redo()


def cut():
    set_modified_status(True)
    script_text.event_generate("<<Cut>>")


def copy():
    set_modified_status(True)
    script_text.event_generate("<<Copy>>")


def paste():
    set_modified_status(True)
    script_text.event_generate("<<Paste>>")


def duplicate():
    set_modified_status(True)
    script_text.event_generate("<<Duplicate>>")


def create_directory_line():
    frm.grid(row=0, column=0, pady=0, sticky="ew")  # Set sticky to "ew" to fill horizontally
    # Configure grid weights for the columns
    frm.columnconfigure(0, weight=0)  # First column doesn't expand
    frm.columnconfigure(1, weight=1)  # Second column expands

    directory_button = Button(frm, text=house_icon, command=select_directory)
    directory_button.grid(column=0, row=0, sticky="w")
    Tooltip(directory_button, "Choose Working Directory")

    directory_label.grid(column=1, row=0, padx=5, sticky="ew")  # Set sticky to "ew" to fill horizontally
    Tooltip(directory_label, "Current directory")


def create_open_script_line():
    script_frm.grid(row=1, column=0, pady=0, sticky="ew")
    script_frm.grid_columnconfigure(2, weight=1)  # Make column 2 (file name entry) expandable

    open_button = Button(script_frm, text=open_icon, command=open_script)
    open_button.grid(column=0, row=0)
    Tooltip(open_button, "Open Script")

    script_name_label.grid(column=2, row=0, sticky="we", padx=5, pady=5)  # Expand to the right
    Tooltip(script_name_label, "File Name")

    save_button = Button(script_frm, text=save_icon, command=save_script)
    save_button.grid(column=3, row=0, sticky="e")  # Align to the right
    Tooltip(save_button, "Save Script")

    save_new_button = Button(script_frm, text=save_new_icon, command=save_as_new_script)
    save_new_button.grid(column=4, row=0, sticky="e")  # Align to the right
    Tooltip(save_new_button, "Save as New Script")

    undo_button = Button(script_frm, text=undo_icon, command=undo)
    undo_button.grid(column=5, row=0, sticky="e")  # Align to the right
    Tooltip(undo_button, "Undo")

    redo_button = Button(script_frm, text=redo_icon, command=redo)
    redo_button.grid(column=6, row=0, sticky="e")  # Align to the right
    Tooltip(redo_button, "Redo")


def create_content_file_window():
    original_text = script_text.get("1.0", "end-1c")  # Store the original text of the file

    def show_context_menu(event):
        # Create the context menu
        context_menu = Menu(root, tearoff=0)
        context_menu.add_command(label="Cut", command=cut)
        context_menu.add_command(label="Copy", command=copy)
        context_menu.add_command(label="Paste", command=paste)
        context_menu.add_command(label="Duplicate", command=duplicate)

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


def create_arguments_lines():
    content_frm.grid(row=3, column=0, pady=0, sticky="ew")  # Set sticky to "ew" to fill horizontally

    entry_arguments_label = Label(content_frm, text="Entry Arguments:")
    entry_arguments_label.grid(row=0, column=0, padx=5, pady=0, sticky="w")

    entry_placeholder = ""  # Enter arguments...
    entry_arguments_entry.insert(0, entry_placeholder)
    entry_arguments_entry.grid(row=0, column=1, sticky="e")
    Tooltip(entry_arguments_entry, "Enter arguments")

    generate_stdin_check = Checkbutton(content_frm, text="stdout", variable=generate_stdin)
    generate_stdin_check.grid(row=0, column=2, sticky="e")  # sticky to "e" for right alignment
    Tooltip(generate_stdin_check, "Generate stdout")

    see_stderr_check = Checkbutton(content_frm, text="stderr", variable=generate_stdin_err)
    see_stderr_check.grid(row=0, column=3, padx=10, sticky="e")  # Set sticky to "e" for right alignment
    Tooltip(see_stderr_check, "Generate stderr")

    stdout_button = Button(content_frm, text="👁 out", command=see_stdout)
    stdout_button.grid(column=1, row=1, sticky="e")  # Align to the right
    Tooltip(stdout_button, "Show Standard Output (stdout)")

    stderr_button = Button(content_frm, text="👁 err", command=see_stderr)
    stderr_button.grid(column=2, row=1, sticky="e")  # Align to the right
    Tooltip(stderr_button, "Show Standard Error (stderr)")


def create_immediately_run_line():
    run_frm.grid(row=4, column=0, pady=0, sticky="nsew")  # Set sticky to "e" for right alignment

    Label(run_frm, text="Run immediately").grid(row=0, column=0, sticky="e", padx=5, pady=0)
    run_button = Button(run_frm, text=run_icon, command=run_script)
    run_button.grid(row=0, column=1, sticky="e", padx=5, pady=0)
    Tooltip(run_button, "Run Script")


def create_execute_in_line():
    line_frm.grid(row=5, column=0, pady=0, sticky="nsew")

    Label(line_frm, text="Script Timeout: ").grid(row=0, column=0, sticky="e", padx=5, pady=0)

    seconds_entry = Entry(line_frm, width=15)
    seconds_entry.grid(column=1, row=0, padx=(10, 0))
    Tooltip(seconds_entry, "number of seconds")

    run_button = Button(line_frm,
                        text=run_icon,
                        command=lambda: run_script_with_timeout(timeout_seconds=float(seconds_entry.get()))
                        )
    run_button.grid(row=0, column=2, sticky="e", padx=15, pady=0)
    Tooltip(run_button, "Set the duration in seconds for the script to execute.")


def create_execute_one_time_with_format():
    one_time_frm.grid(row=6, column=0, pady=0, sticky="nsew")

    Label(one_time_frm, text="Scheduled Script Execution: ").grid(row=0, column=0, sticky="e", padx=5, pady=0)

    date_entry = Entry(one_time_frm, width=15)
    date_entry.grid(column=1, row=0, padx=(10, 0))
    Tooltip(date_entry, "HH:MM AM/PM")

    run_button = Button(one_time_frm, text=run_icon, command=lambda: run_script_once(date_entry.get()))
    run_button.grid(row=0, column=2, sticky="e", padx=15, pady=0)
    Tooltip(run_button, "Use the 'at' command to run the script at a specific time.")


def create_program_daily_with_format():
    daily_frm.grid(row=7, column=0, pady=0, sticky="ew")

    Label(daily_frm, text="Daily Script Scheduling: ").grid(row=0, column=0, sticky="w", padx=5, pady=0)

    minute_entry = Entry(daily_frm, width=2)
    minute_entry.grid(column=1, row=0, padx=(10, 0))
    Tooltip(minute_entry, "every minute")

    hour_entry = Entry(daily_frm, width=2)
    hour_entry.grid(column=2, row=0, padx=(10, 0))
    Tooltip(hour_entry, "every hour")

    day_entry = Entry(daily_frm, width=2)
    day_entry.grid(column=3, row=0, padx=(10, 0))
    Tooltip(day_entry, "every day")

    month_entry = Entry(daily_frm, width=2)
    month_entry.grid(column=4, row=0, padx=(10, 0))
    Tooltip(month_entry, "every month")

    day_of_the_week_entry = Entry(daily_frm, width=2)
    day_of_the_week_entry.grid(column=5, row=0, padx=(10, 0))
    Tooltip(day_of_the_week_entry, "every day of the week")

    run_button = Button(
        daily_frm, text=run_icon,
        command=lambda: run_script_crontab(minute_entry.get(), hour_entry.get(), day_entry.get(), month_entry.get(), day_of_the_week_entry.get())
    )
    run_button.grid(row=0, column=6, sticky="e", padx=15, pady=0)
    Tooltip(run_button, "Utilize 'crontab' to set up script execution on a daily basis. (* = always)")