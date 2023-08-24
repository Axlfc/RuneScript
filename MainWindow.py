#!/usr/bin/python3
from tkinter import Toplevel, Label, Button, Tk, StringVar, IntVar, Frame, Menu, Text, Entry, Listbox
from tkinter import END, INSERT, SEL_FIRST, SEL_LAST, SEL
from tkinter import ttk, scrolledtext, filedialog, simpledialog
import tkinter.messagebox as messagebox
import tkinter.colorchooser as colorchooser
from PIL import Image, ImageTk  # sudo apt-get install python3-pil python3-pil.imagetk
import tkinter
import os
from files import *


def show_context_menu(event):
    def destroy_menu():
        context_menu.unpost()

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

    # Bind the <Leave> event to destroy the context menu when the mouse cursor leaves it
    context_menu.bind("<Leave>", lambda e: destroy_menu())

    # Bind the <FocusOut> event to destroy the context menu when it loses focus
    context_menu.bind("<FocusOut>", lambda e: destroy_menu())


class MainWindow:

    def __init__(self):
        context_menu = None  # Define context_menu as a global variable

        # MAIN MENU METHODS

        file_name = ""  # Current file name.
        current_font_family = "Liberation Mono"
        current_font_size = 12
        fontColor = '#000000'
        fontBackground = '#FFFFFF'

        new_name = ""  # Used for renaming the file

        is_modified = False  # Added is_modified variable

        new_name = ""  # Used for renaming the file

        house_icon = "🏠"
        open_icon = "📂"
        save_icon = "💾"
        save_new_icon = "🆕"
        undo_icon = "⮪"
        redo_icon = "⮬"
        run_icon = "▶"

        root = Tk()

        # TOOLBAR
        toolbar = Frame(root, pady=2)

        # MENUBAR CREATION

        menu = Menu(root)
        root.config(menu=menu)

        frm = ttk.Frame(root, padding=0)
        directory_label = Label(frm, text=os.getcwd(), anchor="center")

        script_frm = ttk.Frame(root, padding=0)
        script_name_label = Label(script_frm, text="Script Name: ", anchor="center")

        script_text = scrolledtext.ScrolledText(root, wrap="word", height=20, width=60)
        text = Text(wrap="word", font=("Liberation Mono", 12), background="white", borderwidth=0, highlightthickness=0,
                    undo=True)

        all_fonts = StringVar()

        all_size = StringVar()

        entry_text = StringVar()
        content_frm = ttk.Frame(root, padding=0)
        entry_arguments_entry = ttk.Entry(content_frm, textvariable=entry_text, width=40)

        generate_stdin = IntVar()
        generate_stdin_err = IntVar()

        run_frm = ttk.Frame(root, padding=0)

        line_frm = ttk.Frame(root, padding=0)

        one_time_frm = ttk.Frame(root, padding=0)

        daily_frm = ttk.Frame(root, padding=0)

        # TOOLBAR BUTTONS
        # new
        new_button = Button(name="toolbar_b2", borderwidth=1, command=new, width=20, height=20)
        photo_new = Image.open("icons/new.png")
        photo_new = photo_new.resize((18, 18), Image.NEAREST)
        image_new = ImageTk.PhotoImage(photo_new)
        new_button.config(image=image_new)
        new_button.pack(in_=toolbar, side="left", padx=4, pady=4)

        # save
        save_button = Button(name="toolbar_b1", borderwidth=1, command=save, width=20, height=20)
        photo_save = Image.open("icons/save.png")
        photo_save = photo_save.resize((18, 18), Image.NEAREST)
        image_save = ImageTk.PhotoImage(photo_save)
        save_button.config(image=image_save)
        save_button.pack(in_=toolbar, side="left", padx=4, pady=4)

        # open
        open_button = Button(name="toolbar_b3", borderwidth=1, command=open_file, width=20, height=20)
        photo_open = Image.open("icons/open.png")
        photo_open = photo_open.resize((18, 18), Image.NEAREST)
        image_open = ImageTk.PhotoImage(photo_open)
        open_button.config(image=image_open)
        open_button.pack(in_=toolbar, side="left", padx=4, pady=4)

        # copy
        copy_button = Button(name="toolbar_b4", borderwidth=1, command=copy, width=20, height=20)
        photo_copy = Image.open("icons/copy.png")
        photo_copy = photo_copy.resize((18, 18), Image.NEAREST)
        image_copy = ImageTk.PhotoImage(photo_copy)
        copy_button.config(image=image_copy)
        copy_button.pack(in_=toolbar, side="left", padx=4, pady=4)

        # cut
        cut_button = Button(name="toolbar_b5", borderwidth=1, command=cut, width=20, height=20)
        photo_cut = Image.open("icons/cut.png")
        photo_cut = photo_cut.resize((18, 18), Image.NEAREST)
        image_cut = ImageTk.PhotoImage(photo_cut)
        cut_button.config(image=image_cut)
        cut_button.pack(in_=toolbar, side="left", padx=4, pady=4)

        # paste
        paste_button = Button(name="toolbar_b6", borderwidth=1, command=paste, width=20, height=20)
        photo_paste = Image.open("icons/paste.png")
        photo_paste = photo_paste.resize((18, 18), Image.NEAREST)
        image_paste = ImageTk.PhotoImage(photo_paste)
        paste_button.config(image=image_paste)
        paste_button.pack(in_=toolbar, side="left", padx=4, pady=4)

        # duplicate
        duplicate_button = Button(name="toolbar_b7", borderwidth=1, command=paste, width=20, height=20)
        photo_duplicate = Image.open("icons/duplicate.png")
        photo_duplicate = photo_paste.resize((18, 18), Image.NEAREST)
        image_duplicate = ImageTk.PhotoImage(photo_paste)
        duplicate_button.config(image=image_duplicate)
        duplicate_button.pack(in_=toolbar, side="left", padx=4, pady=4)

        # redo
        redo_button = Button(name="toolbar_b8", borderwidth=1, command=redo, width=20, height=20)
        photo_redo = Image.open("icons/redo.png")
        photo_redo = photo_redo.resize((18, 18), Image.NEAREST)
        image_redo = ImageTk.PhotoImage(photo_redo)
        redo_button.config(image=image_redo)
        redo_button.pack(in_=toolbar, side="left", padx=4, pady=4)

        # undo
        undo_button = Button(name="toolbar_b9", borderwidth=1, command=undo, width=20, height=20)
        photo_undo = Image.open("icons/undo.png")
        photo_undo = photo_undo.resize((18, 18), Image.NEAREST)
        image_undo = ImageTk.PhotoImage(photo_undo)
        undo_button.config(image=image_undo)
        undo_button.pack(in_=toolbar, side="left", padx=4, pady=4)

        # find
        find_button = Button(name="toolbar_b10", borderwidth=1, command=find_text, width=20, height=20)
        photo_find = Image.open("icons/find.png")
        photo_find = photo_find.resize((18, 18), Image.NEAREST)
        image_find = ImageTk.PhotoImage(photo_find)
        find_button.config(image=image_find)
        find_button.pack(in_=toolbar, side="left", padx=4, pady=4)

        at_window = None
        crontab_window = None

        # root.title("Untitled* - Script Editor")
        root.title("Scripts Editor")
        root.geometry("600x800")

        # setting resizable window
        root.resizable(True, True)
        root.minsize(600, 800)  # minimimum size possible

        is_modified = False

        # File menu.
        file_menu = Menu(menu)
        menu.add_cascade(label="File", menu=file_menu, underline=0)

        file_menu.add_command(label="New", command=new, compound='left', image=image_new, accelerator='Ctrl+N',
                              underline=0)  # command passed is here the method defined above.
        file_menu.add_command(label="Open", command=open_script, compound='left', image=image_open,
                              accelerator='Ctrl+O',
                              underline=0)
        file_menu.add_separator()
        file_menu.add_command(label="Save", command=save_script, compound='left', image=image_save,
                              accelerator='Ctrl+S',
                              underline=0)
        file_menu.add_command(label="Save As", command=save_as_new_script, accelerator='Ctrl+Shift+S', underline=1)
        # file_menu.add_command(label="Rename", command=rename, accelerator='Ctrl+Shift+R', underline=0)
        file_menu.add_separator()
        file_menu.add_command(label="Close", command=close, accelerator='Alt+F4', underline=0)

        # Edit Menu.
        edit_menu = Menu(menu)
        menu.add_cascade(label="Edit", menu=edit_menu, underline=0)

        # edit_menu.add_command(label="Undo", command=undo, compound='left', image=image_undo, accelerator='Ctrl+Z', underline=0)
        # edit_menu.add_command(label="Redo", command=redo, compound='left', image=image_redo, accelerator='Ctrl+Y', underline=0)
        # edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=cut, compound='left', image=image_cut, accelerator='Ctrl+X',
                              underline=0)
        edit_menu.add_command(label="Copy", command=copy, compound='left', image=image_copy, accelerator='Ctrl+C',
                              underline=1)
        edit_menu.add_command(label="Paste", command=paste, compound='left', image=image_paste, accelerator='Ctrl+P',
                              underline=0)
        edit_menu.add_command(label="Duplicate", command=duplicate, compound='left', image=image_duplicate,
                              accelerator='Ctrl+D',
                              underline=0)
        # edit_menu.add_command(label="Delete", command=delete, underline=0)
        # edit_menu.add_separator()
        # edit_menu.add_command(label="Select All", command=select_all, accelerator='Ctrl+A', underline=0)
        # edit_menu.add_command(label="Clear All", command=delete_all, underline=6)

        # Tool Menu
        tool_menu = Menu(menu)
        menu.add_cascade(label="Tools", menu=tool_menu, underline=0)

        tool_menu.add_command(label="Change Color", command=change_color)
        tool_menu.add_command(label="Search", command=find_text, compound='left', image=image_find,
                              accelerator='Ctrl+F')

        # Jobs Menu
        jobs_menu = Menu(menu)
        menu.add_cascade(label="Jobs", menu=jobs_menu, underline=0)

        jobs_menu.add_command(label="at", command=open_at_window)
        jobs_menu.add_command(label="crontab", command=open_cron_window)

        help_menu = Menu(menu)
        menu.add_cascade(label="Help", menu=help_menu, underline=0)
        help_menu.add_command(label="About", command=about, accelerator='Ctrl+H', underline=0)

        # DIRECTORY LINE
        frm.grid(row=0, column=0, pady=0, sticky="ew")  # Set sticky to "ew" to fill horizontally
        # Configure grid weights for the columns
        frm.columnconfigure(0, weight=0)  # First column doesn't expand
        frm.columnconfigure(1, weight=1)  # Second column expands

        directory_button = ttk.Button(frm, text=house_icon, command=select_directory)
        directory_button.grid(column=0, row=0, sticky="w")
        Tooltip(directory_button, "Choose Working Directory")

        directory_label.grid(column=1, row=0, padx=5, sticky="ew")  # Set sticky to "ew" to fill horizontally
        Tooltip(directory_label, "Current directory")
        
        # create open script line
        script_frm.grid(row=1, column=0, pady=0, sticky="ew")
        script_frm.grid_columnconfigure(2, weight=1)  # Make column 2 (file name entry) expandable

        open_button = ttk.Button(script_frm, text=open_icon, command=open_script)
        open_button.grid(column=0, row=0)
        Tooltip(open_button, "Open Script")

        script_name_label.grid(column=2, row=0, sticky="we", padx=5, pady=5)  # Expand to the right
        Tooltip(script_name_label, "File Name")

        save_button = ttk.Button(script_frm, text=save_icon, command=save_script)
        save_button.grid(column=3, row=0, sticky="e")  # Align to the right
        Tooltip(save_button, "Save Script")

        save_new_button = ttk.Button(script_frm, text=save_new_icon, command=save_as_new_script)
        save_new_button.grid(column=4, row=0, sticky="e")  # Align to the right
        Tooltip(save_new_button, "Save as New Script")

        undo_button = Button(script_frm, text=undo_icon)
        undo_button.grid(column=5, row=0, sticky="e")  # Align to the right
        Tooltip(undo_button, "Undo")

        redo_button = Button(script_frm, text=redo_icon)
        redo_button.grid(column=6, row=0, sticky="e")  # Align to the right
        Tooltip(redo_button, "Redo")


        # create_content_file_window()
        original_text = script_text.get("1.0", "end-1c")  # Store the original text of the file
        script_text.grid(row=2, column=0, padx=0, pady=0, sticky="nsew")
        script_text.configure(bg="#1f1f1f", fg="white")
        script_text.config(insertbackground='#F0F0F0', selectbackground='#4d4d4d')
        script_text.bind("<Button-3>", show_context_menu)
        script_text.bind("<Key>", update_modification_status)  # Add this line to track text insertion

        content_frm.grid(row=3, column=0, pady=0, sticky="ew")  # Set sticky to "ew" to fill horizontally

        entry_arguments_label = ttk.Label(content_frm, text="Entry Arguments:")
        entry_arguments_label.grid(row=0, column=0, padx=5, pady=0, sticky="w")

        entry_placeholder = ""  # Enter arguments...
        entry_arguments_entry.insert(0, entry_placeholder)
        entry_arguments_entry.grid(row=0, column=1, sticky="e")
        Tooltip(entry_arguments_entry, "Enter arguments")

        generate_stdin_check = ttk.Checkbutton(content_frm, text="stdout", variable=generate_stdin)
        generate_stdin_check.grid(row=0, column=2, sticky="e")  # sticky to "e" for right alignment
        Tooltip(generate_stdin_check, "Generate stdout")

        see_stderr_check = ttk.Checkbutton(content_frm, text="stderr", variable=generate_stdin_err)
        see_stderr_check.grid(row=0, column=3, padx=10, sticky="e")  # Set sticky to "e" for right alignment
        Tooltip(see_stderr_check, "Generate stderr")

        stdout_button = ttk.Button(content_frm, text="👁 out", command=see_stdout)
        stdout_button.grid(column=1, row=1, sticky="e")  # Align to the right
        Tooltip(stdout_button, "Show Standard Output (stdout)")

        stderr_button = ttk.Button(content_frm, text="👁 err", command=see_stderr)
        stderr_button.grid(column=2, row=1, sticky="e")  # Align to the right
        Tooltip(stderr_button, "Show Standard Error (stderr)")

        # create inmediately run line
        run_frm.grid(row=4, column=0, pady=0, sticky="nsew")  # Set sticky to "e" for right alignment

        ttk.Label(run_frm, text="Run immediately").grid(row=0, column=0, sticky="e", padx=5, pady=0)
        run_button = ttk.Button(run_frm, text=run_icon, command=run_script)
        run_button.grid(row=0, column=1, sticky="e", padx=5, pady=0)
        Tooltip(run_button, "Run Script")
        
        
        # create_execute_in_line
        line_frm.grid(row=5, column=0, pady=0, sticky="nsew")

        ttk.Label(line_frm, text="Script Timeout: ").grid(row=0, column=0, sticky="e", padx=5, pady=0)

        seconds_entry = ttk.Entry(line_frm, width=15)
        seconds_entry.grid(column=1, row=0, padx=(10, 0))
        Tooltip(seconds_entry, "number of seconds")

        run_button = ttk.Button(line_frm, text=run_icon,
                                command=lambda: run_script_with_timeout(timeout_seconds=float(seconds_entry.get())))
        run_button.grid(row=0, column=2, sticky="e", padx=15, pady=0)
        Tooltip(run_button, "Set the duration in seconds for the script to execute.")
        

        # create_execute_one_time_with_format()
        one_time_frm.grid(row=6, column=0, pady=0, sticky="nsew")

        ttk.Label(one_time_frm, text="Scheduled Script Execution: ").grid(row=0, column=0, sticky="e", padx=5, pady=0)

        date_entry = ttk.Entry(one_time_frm, width=15)
        date_entry.grid(column=1, row=0, padx=(10, 0))
        Tooltip(date_entry, "HH:MM AM/PM")

        run_button = ttk.Button(one_time_frm, text=run_icon, command=lambda: run_script_once(date_entry.get()))
        run_button.grid(row=0, column=2, sticky="e", padx=15, pady=0)
        Tooltip(run_button, "Use the 'at' command to run the script at a specific time.")

        # create_program_daily_with_format
        daily_frm.grid(row=7, column=0, pady=0, sticky="ew")

        ttk.Label(daily_frm, text="Daily Script Scheduling: ").grid(row=0, column=0, sticky="w", padx=5, pady=0)

        minute_entry = ttk.Entry(daily_frm, width=2)
        minute_entry.grid(column=1, row=0, padx=(10, 0))
        Tooltip(minute_entry, "every minute")

        hour_entry = ttk.Entry(daily_frm, width=2)
        hour_entry.grid(column=2, row=0, padx=(10, 0))
        Tooltip(hour_entry, "every hour")

        day_entry = ttk.Entry(daily_frm, width=2)
        day_entry.grid(column=3, row=0, padx=(10, 0))
        Tooltip(day_entry, "every day")

        month_entry = ttk.Entry(daily_frm, width=2)
        month_entry.grid(column=4, row=0, padx=(10, 0))
        Tooltip(month_entry, "every month")

        day_of_the_week_entry = ttk.Entry(daily_frm, width=2)
        day_of_the_week_entry.grid(column=5, row=0, padx=(10, 0))
        Tooltip(day_of_the_week_entry, "every day of the week")

        run_button = ttk.Button(
            daily_frm, text=run_icon,
            command=lambda: run_script_crontab(minute_entry.get(), hour_entry.get(), day_entry.get(), month_entry.get(),
                                               day_of_the_week_entry.get())
        )
        run_button.grid(row=0, column=6, sticky="e", padx=15, pady=0)
        Tooltip(run_button, "Utilize 'crontab' to set up script execution on a daily basis. (* = always)")

        root.grid_rowconfigure(2, weight=1)
        root.columnconfigure(0, weight=1)

        root.mainloop()
