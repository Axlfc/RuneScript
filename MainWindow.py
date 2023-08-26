#!/usr/bin/python3
from tkinter import Toplevel, Label, Button, Tk, StringVar, IntVar, Frame, Menu, Text, Entry, Listbox, Checkbutton
from tkinter import END, INSERT, SEL_FIRST, SEL_LAST, SEL
from tkinter import ttk, scrolledtext, filedialog, simpledialog
import tkinter.messagebox as messagebox
import tkinter.colorchooser as colorchooser
from PIL import Image, ImageTk  # sudo apt-get install python3-pil python3-pil.imagetk
import tkinter
from os_utils import *


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event):
        self.tooltip = Toplevel()
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = Label(self.tooltip, text=self.text, background="#ffffe0", relief="solid", borderwidth=1)
        label.pack()

    def leave(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class MainWindow:
    def __init__(self):
        self.context_menu = None  # Define context_menu as a global variable

        # MAIN MENU METHODS

        self.file_name = ""  # Current file name.
        self.current_font_family = "Liberation Mono"
        self.current_font_size = 12
        self.fontColor = '#000000'
        self.fontBackground = '#FFFFFF'

        self.new_name = ""  # Used for renaming the file

        self.is_modified = False  # Added is_modified variable

        self.new_name = ""  # Used for renaming the file

        self.house_icon = "🏠"
        self.open_icon = "📂"
        self.save_icon = "💾"
        self.save_new_icon = "🆕"
        self.undo_icon = "⮪"
        self.redo_icon = "⮬"
        self.run_icon = "▶"

        self.root = Tk()

        # TOOLBAR
        self.toolbar = Frame(self.root, pady=2)

        # MENUBAR CREATION

        self.menu = Menu(self.root)
        self.root.config(menu=self.menu)

        self.frm = Frame(self.root)
        self.directory_label = Label(self.frm, text=os.getcwd(), anchor="center")

        self.script_frm = Frame(self.root)
        self.script_name_label = Label(self.script_frm, text="Script Name: ", anchor="center")

        self.script_text = scrolledtext.ScrolledText(self.root, wrap="word", height=20, width=60)
        self.text = Text(wrap="word", font=("Liberation Mono", 12), background="white", borderwidth=0, highlightthickness=0,
                    undo=True)

        self.all_fonts = StringVar()

        self.all_size = StringVar()

        self.entry_text = StringVar()
        self.content_frm = Frame(self.root)
        self.entry_arguments_entry = Entry(self.content_frm, textvariable=self.entry_text, width=40)

        self.generate_stdin = IntVar()
        self.generate_stdin_err = IntVar()

        self.run_frm = Frame(self.root)

        self.line_frm = Frame(self.root)

        self.one_time_frm = Frame(self.root)

        self.daily_frm = Frame(self.root)

        # TOOLBAR BUTTONS
        # new
        self.new_button = Button(name="toolbar_b2", borderwidth=1, command=self.new, width=20, height=20)
        self.photo_new = Image.open("icons/new.png")
        self.photo_new = self.photo_new.resize((18, 18), Image.NEAREST)
        self.image_new = ImageTk.PhotoImage(self.photo_new)
        self.new_button.config(image=self.image_new)
        self.new_button.pack(in_=self.toolbar, side="left", padx=4, pady=4)

        # save
        self.save_button = Button(name="toolbar_b1", borderwidth=1, command=self.save, width=20, height=20)
        self.photo_save = Image.open("icons/save.png")
        self.photo_save = self.photo_save.resize((18, 18), Image.NEAREST)
        self.image_save = ImageTk.PhotoImage(self.photo_save)
        self.save_button.config(image=self.image_save)
        self.save_button.pack(in_=self.toolbar, side="left", padx=4, pady=4)

        # open
        self.open_button = Button(name="toolbar_b3", borderwidth=1, command=self.open_file, width=20, height=20)
        self.photo_open = Image.open("icons/open.png")
        self.photo_open = self.photo_open.resize((18, 18), Image.NEAREST)
        self.image_open = ImageTk.PhotoImage(self.photo_open)
        self.open_button.config(image=self.image_open)
        self.open_button.pack(in_=self.toolbar, side="left", padx=4, pady=4)

        # copy
        self.copy_button = Button(name="toolbar_b4", borderwidth=1, command=self.copy, width=20, height=20)
        self.photo_copy = Image.open("icons/copy.png")
        self.photo_copy = self.photo_copy.resize((18, 18), Image.NEAREST)
        self.image_copy = ImageTk.PhotoImage(self.photo_copy)
        self.copy_button.config(image=self.image_copy)
        self.copy_button.pack(in_=self.toolbar, side="left", padx=4, pady=4)

        # cut
        self.cut_button = Button(name="toolbar_b5", borderwidth=1, command=self.cut, width=20, height=20)
        self.photo_cut = Image.open("icons/cut.png")
        self.photo_cut = self.photo_cut.resize((18, 18), Image.NEAREST)
        self.image_cut = ImageTk.PhotoImage(self.photo_cut)
        self.cut_button.config(image=self.image_cut)
        self.cut_button.pack(in_=self.toolbar, side="left", padx=4, pady=4)

        # paste
        self.paste_button = Button(name="toolbar_b6", borderwidth=1, command=self.paste, width=20, height=20)
        self.photo_paste = Image.open("icons/paste.png")
        self.photo_paste = self.photo_paste.resize((18, 18), Image.NEAREST)
        self.image_paste = ImageTk.PhotoImage(self.photo_paste)
        self.paste_button.config(image=self.image_paste)
        self.paste_button.pack(in_=self.toolbar, side="left", padx=4, pady=4)

        # duplicate
        self.duplicate_button = Button(name="toolbar_b7", borderwidth=1, command=self.duplicate, width=20, height=20)
        self.photo_duplicate = Image.open("icons/duplicate.png")
        self.photo_duplicate = self.photo_duplicate.resize((18, 18), Image.NEAREST)
        self.image_duplicate = ImageTk.PhotoImage(self.photo_duplicate)
        self.duplicate_button.config(image=self.image_duplicate)
        self.duplicate_button.pack(in_=self.toolbar, side="left", padx=4, pady=4)

        # redo
        self.redo_button = Button(name="toolbar_b8", borderwidth=1, command=self.redo, width=20, height=20)
        self.photo_redo = Image.open("icons/redo.png")
        self.photo_redo = self.photo_redo.resize((18, 18), Image.NEAREST)
        self.image_redo = ImageTk.PhotoImage(self.photo_redo)
        self.redo_button.config(image=self.image_redo)
        self.redo_button.pack(in_=self.toolbar, side="left", padx=4, pady=4)

        # undo
        self.undo_button = Button(name="toolbar_b9", borderwidth=1, command=self.undo, width=20, height=20)
        self.photo_undo = Image.open("icons/undo.png")
        self.photo_undo = self.photo_undo.resize((18, 18), Image.NEAREST)
        self.image_undo = ImageTk.PhotoImage(self.photo_undo)
        self.undo_button.config(image=self.image_undo)
        self.undo_button.pack(in_=self.toolbar, side="left", padx=4, pady=4)

        # find
        self.find_button = Button(name="toolbar_b10", borderwidth=1, command=self.find_text, width=20, height=20)
        self.photo_find = Image.open("icons/find.png")
        self.photo_find = self.photo_find.resize((18, 18), Image.NEAREST)
        self.image_find = ImageTk.PhotoImage(self.photo_find)
        self.find_button.config(image=self.image_find)
        self.find_button.pack(in_=self.toolbar, side="left", padx=4, pady=4)

        # delete
        self.delete_button = Button(name="toolbar_b11", borderwidth=1, command=self.delete, width=20, height=20)
        self.photo_delete = Image.open("icons/delete.png")
        self.photo_delete = self.photo_delete.resize((18, 18), Image.NEAREST)
        self.image_delete = ImageTk.PhotoImage(self.photo_delete)
        self.delete_button.config(image=self.image_delete)
        self.delete_button.pack(in_=self.toolbar, side="left", padx=4, pady=4)

        self.at_window = None
        self.crontab_window = None

        # root.title("Untitled* - Script Editor")
        self.root.title("Scripts Editor")
        self.root.geometry("600x800")

        # setting resizable window
        self.root.resizable(True, True)
        self.root.minsize(600, 800)  # minimimum size possible

        self.is_modified = False

        # File menu.
        self.file_menu = Menu(self.menu)
        self.menu.add_cascade(label="File", menu=self.file_menu, underline=0)

        self.file_menu.add_command(label="New", command=self.new, compound='left', image=self.image_new, accelerator='Ctrl+N',
                              underline=0)  # command passed is here the method defined above.
        self.file_menu.add_command(label="Open", command=self.open_script, compound='left', image=self.image_open,
                              accelerator='Ctrl+O',
                              underline=0)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Save", command=self.save_script, compound='left', image=self.image_save,
                              accelerator='Ctrl+S',
                              underline=0)
        self.file_menu.add_command(label="Save As", command=self.save_as_new_script, accelerator='Ctrl+Shift+S', underline=1)
        # file_menu.add_command(label="Rename", command=rename, accelerator='Ctrl+Shift+R', underline=0)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Close", command=self.close, accelerator='Alt+F4', underline=0)

        # Edit Menu.
        self.edit_menu = Menu(self.menu)
        self.menu.add_cascade(label="Edit", menu=self.edit_menu, underline=0)

        # edit_menu.add_command(label="Undo", command=undo, compound='left', image=image_undo, accelerator='Ctrl+Z', underline=0)
        # edit_menu.add_command(label="Redo", command=redo, compound='left', image=image_redo, accelerator='Ctrl+Y', underline=0)
        # edit_menu.add_separator()
        self.edit_menu.add_command(label="Undo", command=self.undo, compound='left', image=self.image_undo,
                                   accelerator='Ctrl+Z',
                                   underline=0)
        self.edit_menu.add_command(label="Redo", command=self.redo, compound='left', image=self.image_redo,
                                   accelerator='Ctrl+Y',
                                   underline=1)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Cut", command=self.cut, compound='left', image=self.image_cut, accelerator='Ctrl+X',
                              underline=0)
        self.edit_menu.add_command(label="Copy", command=self.copy, compound='left', image=self.image_copy, accelerator='Ctrl+C',
                              underline=1)
        self.edit_menu.add_command(label="Paste", command=self.paste, compound='left', image=self.image_paste, accelerator='Ctrl+P',
                              underline=0)
        self.edit_menu.add_command(label="Duplicate", command=self.duplicate, compound='left', image=self.image_duplicate,
                              accelerator='Ctrl+D',
                              underline=0)
        self.edit_menu.add_command(label="Delete", command=self.delete, compound='left', image=self.image_delete,
                                   accelerator='DEL',
                                   underline=0)
        # edit_menu.add_command(label="Delete", command=delete, underline=0)
        # edit_menu.add_separator()
        # edit_menu.add_command(label="Select All", command=select_all, accelerator='Ctrl+A', underline=0)
        # edit_menu.add_command(label="Clear All", command=delete_all, underline=6)

        # Tool Menu
        self.tool_menu = Menu(self.menu)
        self.menu.add_cascade(label="Tools", menu=self.tool_menu, underline=0)

        self.tool_menu.add_command(label="Change Color", command=self.change_color)
        self.tool_menu.add_command(label="Search", command=self.find_text, compound='left', image=self.image_find,
                              accelerator='Ctrl+F')

        # Jobs Menu
        self.jobs_menu = Menu(self.menu)
        self.menu.add_cascade(label="Jobs", menu=self.jobs_menu, underline=0)

        self.jobs_menu.add_command(label="at", command=self.open_at_window)
        self.jobs_menu.add_command(label="crontab", command=self.open_cron_window)

        self.help_menu = Menu(self.menu)
        self.menu.add_cascade(label="Help", menu=self.help_menu, underline=0)
        self.help_menu.add_command(label="About", command=self.about, accelerator='Ctrl+H', underline=0)

        # DIRECTORY LINE
        self.frm.grid(row=0, column=0, pady=0, sticky="ew")  # Set sticky to "ew" to fill horizontally
        # Configure grid weights for the columns
        self.frm.columnconfigure(0, weight=0)  # First column doesn't expand
        self.frm.columnconfigure(1, weight=1)  # Second column expands

        self.directory_button = Button(self.frm, text=self.house_icon, command=self.select_directory)
        self.directory_button.grid(column=0, row=0, sticky="w")
        Tooltip(self.directory_button, "Choose Working Directory")

        self.directory_label.grid(column=1, row=0, padx=5, sticky="ew")  # Set sticky to "ew" to fill horizontally
        Tooltip(self.directory_label, "Current directory")
        
        # create open script line
        self.script_frm.grid(row=1, column=0, pady=0, sticky="ew")
        self.script_frm.grid_columnconfigure(2, weight=1)  # Make column 2 (file name entry) expandable

        self.open_button = Button(self.script_frm, text=self.open_icon, command=self.open_script)
        self.open_button.grid(column=0, row=0)
        Tooltip(self.open_button, "Open Script")

        self.script_name_label.grid(column=2, row=0, sticky="we", padx=5, pady=5)  # Expand to the right
        Tooltip(self.script_name_label, "File Name")

        self.save_button = Button(self.script_frm, text=self.save_icon, command=self.save_script)
        self.save_button.grid(column=3, row=0, sticky="e")  # Align to the right
        Tooltip(self.save_button, "Save Script")

        self.save_new_button = Button(self.script_frm, text=self.save_new_icon, command=self.save_as_new_script)
        self.save_new_button.grid(column=4, row=0, sticky="e")  # Align to the right
        Tooltip(self.save_new_button, "Save as New Script")

        self.undo_button = Button(self.script_frm, text=self.undo_icon)
        self.undo_button.grid(column=5, row=0, sticky="e")  # Align to the right
        Tooltip(self.undo_button, "Undo")

        self.redo_button = Button(self.script_frm, text=self.redo_icon)
        self.redo_button.grid(column=6, row=0, sticky="e")  # Align to the right
        Tooltip(self.redo_button, "Redo")


        # create_content_file_window()
        self.original_text = self.script_text.get("1.0", "end-1c")  # Store the original text of the file
        self.script_text.grid(row=2, column=0, padx=0, pady=0, sticky="nsew")
        self.script_text.configure(bg="#1f1f1f", fg="white")
        self.script_text.config(insertbackground='#F0F0F0', selectbackground='#4d4d4d')
        self.script_text.bind("<Button-3>", self.show_context_menu)
        self.script_text.bind("<Key>", self.update_modification_status)  # Add this line to track text insertion

        self.content_frm.grid(row=3, column=0, pady=0, sticky="ew")  # Set sticky to "ew" to fill horizontally

        self.entry_arguments_label = Label(self.content_frm, text="Entry Arguments:")
        self.entry_arguments_label.grid(row=0, column=0, padx=5, pady=0, sticky="w")

        self.entry_placeholder = ""  # Enter arguments...
        self.entry_arguments_entry.insert(0, self.entry_placeholder)
        self.entry_arguments_entry.grid(row=0, column=1, sticky="e")
        Tooltip(self.entry_arguments_entry, "Enter arguments")

        self.generate_stdin_check = Checkbutton(self.content_frm, text="stdout", variable=self.generate_stdin)
        self.generate_stdin_check.grid(row=0, column=2, sticky="e")  # sticky to "e" for right alignment
        Tooltip(self.generate_stdin_check, "Generate stdout")

        self.see_stderr_check = Checkbutton(self.content_frm, text="stderr", variable=self.generate_stdin_err)
        self.see_stderr_check.grid(row=0, column=3, padx=10, sticky="e")  # Set sticky to "e" for right alignment
        Tooltip(self.see_stderr_check, "Generate stderr")

        self.stdout_button = Button(self.content_frm, text="👁 out", command=self.see_stdout)
        self.stdout_button.grid(column=1, row=1, sticky="e")  # Align to the right
        Tooltip(self.stdout_button, "Show Standard Output (stdout)")

        self.stderr_button = Button(self.content_frm, text="👁 err", command=self.see_stderr)
        self.stderr_button.grid(column=2, row=1, sticky="e")  # Align to the right
        Tooltip(self.stderr_button, "Show Standard Error (stderr)")

        # create inmediately run line
        self.run_frm.grid(row=4, column=0, pady=0, sticky="nsew")  # Set sticky to "e" for right alignment

        Label(self.run_frm, text="Run immediately").grid(row=0, column=0, sticky="e", padx=5, pady=0)
        self.run_button = Button(self.run_frm, text=self.run_icon, command=self.run_script)
        self.run_button.grid(row=0, column=1, sticky="e", padx=5, pady=0)
        Tooltip(self.run_button, "Run Script")
        
        
        # create_execute_in_line
        self.line_frm.grid(row=5, column=0, pady=0, sticky="nsew")

        Label(self.line_frm, text="Script Timeout: ").grid(row=0, column=0, sticky="e", padx=5, pady=0)

        self.seconds_entry = Entry(self.line_frm, width=15)
        self.seconds_entry.grid(column=1, row=0, padx=(10, 0))
        Tooltip(self.seconds_entry, "number of seconds")

        self.run_button = Button(self.line_frm, text=self.run_icon,
                                command=lambda: self.run_script_with_timeout(timeout_seconds=float(self.seconds_entry.get())))
        self.run_button.grid(row=0, column=2, sticky="e", padx=15, pady=0)
        Tooltip(self.run_button, "Set the duration in seconds for the script to execute.")
        

        # create_execute_one_time_with_format()
        self.one_time_frm.grid(row=6, column=0, pady=0, sticky="nsew")

        Label(self.one_time_frm, text="Scheduled Script Execution: ").grid(row=0, column=0, sticky="e", padx=5, pady=0)

        self.date_entry = Entry(self.one_time_frm, width=15)
        self.date_entry.grid(column=1, row=0, padx=(10, 0))
        Tooltip(self.date_entry, "HH:MM AM/PM")

        self.run_button = Button(self.one_time_frm, text=self.run_icon, command=lambda: self.run_script_once(self.date_entry.get()))
        self.run_button.grid(row=0, column=2, sticky="e", padx=15, pady=0)
        Tooltip(self.run_button, "Use the 'at' command to run the script at a specific time.")

        # create_program_daily_with_format
        self.daily_frm.grid(row=7, column=0, pady=0, sticky="ew")

        Label(self.daily_frm, text="Daily Script Scheduling: ").grid(row=0, column=0, sticky="w", padx=5, pady=0)

        self.minute_entry = Entry(self.daily_frm, width=2)
        self.minute_entry.grid(column=1, row=0, padx=(10, 0))
        Tooltip(self.minute_entry, "every minute")

        self.hour_entry = Entry(self.daily_frm, width=2)
        self.hour_entry.grid(column=2, row=0, padx=(10, 0))
        Tooltip(self.hour_entry, "every hour")

        self.day_entry = Entry(self.daily_frm, width=2)
        self.day_entry.grid(column=3, row=0, padx=(10, 0))
        Tooltip(self.day_entry, "every day")

        self.month_entry = Entry(self.daily_frm, width=2)
        self.month_entry.grid(column=4, row=0, padx=(10, 0))
        Tooltip(self.month_entry, "every month")

        self.day_of_the_week_entry = Entry(self.daily_frm, width=2)
        self.day_of_the_week_entry.grid(column=5, row=0, padx=(10, 0))
        Tooltip(self.day_of_the_week_entry, "every day of the week")

        self.run_button = Button(
            self.daily_frm, text=self.run_icon,
            command=lambda: self.run_script_crontab(self.minute_entry.get(), self.hour_entry.get(), self.day_entry.get(), self.month_entry.get(),
                                               self.day_of_the_week_entry.get())
        )
        self.run_button.grid(row=0, column=6, sticky="e", padx=15, pady=0)
        Tooltip(self.run_button, "Utilize 'crontab' to set up script execution on a daily basis. (* = always)")

        self.root.grid_rowconfigure(2, weight=1)
        self.root.columnconfigure(0, weight=1)

        self.root.mainloop()

    def open_at_window(self):
        def update_at_jobs():
            listbox.delete(0, END)
            self.populate_at_jobs(listbox)
            self.at_window.after(5000, update_at_jobs)

        # global at_window
        self.at_window = Toplevel(self.root)
        self.at_window.title("AT Jobs")
        self.at_window.geometry("600x400")

        listbox = Listbox(self.at_window, width=80)
        listbox.pack(fill="both", expand=True)

        self.populate_at_jobs(listbox)

        remove_button = Button(self.at_window, text="Remove Selected", command=lambda: self.remove_selected_at_job(listbox))
        remove_button.pack(side="bottom")

        self.at_window.after(0, update_at_jobs)
        self.at_window.mainloop()

    def populate_at_jobs(self, listbox):
        try:
            at_output = subprocess.check_output(["atq"], text=True).splitlines()
            if not at_output:
                username = subprocess.check_output(["whoami"], text=True).strip()  # Get the current user
                listbox.insert(END, f"No AT jobs found for user {username}.")
            else:
                for line in at_output:
                    listbox.insert(END, line)
        except subprocess.CalledProcessError:
            messagebox.showerror("Error", "Failed to retrieve AT jobs")

    def remove_selected_at_job(self, listbox):
        selected_indices = listbox.curselection()
        if not selected_indices:
            return

        selected_index = selected_indices[0]
        selected_item = listbox.get(selected_index)

        if "No AT jobs found for user" in selected_item:
            listbox.delete(selected_index)  # Delete the special message
        else:
            job_id = selected_item.split()[0]
            try:
                subprocess.run(["atrm", job_id], check=True)
                listbox.delete(selected_index)
            except subprocess.CalledProcessError:
                messagebox.showerror("Error", f"Failed to remove AT job {job_id}")

    def open_cron_window(self):
        def update_cron_jobs():
            listbox.delete(0, END)
            self.populate_cron_jobs(listbox)
            self.crontab_window.after(5000, update_cron_jobs)

        global crontab_window
        self.crontab_window = Toplevel(self.root)
        self.crontab_window.title("Cron Jobs")
        self.crontab_window.geometry("600x400")

        listbox = Listbox(self.crontab_window, width=80)
        listbox.pack(fill="both", expand=True)

        listbox.insert(END, "Loading cron jobs...")  # Initial message while loading

        self.populate_cron_jobs(listbox)

        remove_button = Button(self.crontab_window, text="Remove Selected",
                               command=lambda: self.remove_selected_cron_job(listbox))
        remove_button.pack(side="bottom")

        self.crontab_window.after(0, update_cron_jobs)
        self.crontab_window.mainloop()

    def populate_cron_jobs(self, listbox):
        try:
            cron_output = subprocess.check_output(["crontab", "-l"], text=True).splitlines()
            # print("hola" + cron_output)
            if not cron_output:
                username = subprocess.check_output(["whoami"], text=True).strip()  # Get the current user
                listbox.insert(END, f"No cron jobs found for user {username}.")
            else:
                for line in cron_output:
                    listbox.insert(END, line)
        except subprocess.CalledProcessError:
            username = subprocess.check_output(["whoami"], text=True).strip()  # Get the current user
            listbox.insert(END, f"No cron jobs found for user {username}.")
            # messagebox.showwarning("Warning", "Failed to retrieve cron jobs")

    def remove_selected_cron_job(self, listbox):
        selected_indices = listbox.curselection()
        if not selected_indices:
            return

        selected_index = selected_indices[0]
        selected_job = listbox.get(selected_index)

        try:
            # Create a temporary file to store modified crontab
            temp_file = tempfile.NamedTemporaryFile(delete=False)

            # Save the current crontab to the temporary file
            subprocess.run(["crontab", "-l"], text=True, stdout=temp_file)

            # Reset the file pointer to the beginning
            temp_file.seek(0)

            selected_job_bytes = selected_job.encode("utf-8")

            # Filter out the selected job and write to a new temporary file
            filtered_lines = [line for line in temp_file if selected_job_bytes not in line]

            temp_file.close()

            # Write the filtered content back to the temporary file
            with open(temp_file.name, "wb") as f:
                f.writelines(filtered_lines)

            # Load the modified crontab from the temporary file
            subprocess.run(["crontab", temp_file.name], check=True)

            # Delete the temporary file
            os.remove(temp_file.name)

            # Remove the item from the listbox
            listbox.delete(selected_index)

        except subprocess.CalledProcessError:
            messagebox.showerror("Error", "Failed to remove cron job")

    # Help Menu
    def about(self, event=None):
        messagebox.showinfo("About",
                            "ScriptsEditor\nCreated in Python using Tkinter\nAxlfc, 2023")

    def select_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            os.chdir(directory)
            self.directory_label.config(text=f"{directory}")
            # open_first_text_file(directory)

    def colorize_text(self):
        script_content = self.script_text.get("1.0", "end")
        self.script_text.delete("1.0", "end")
        self.script_text.insert("1.0", script_content)

    def open_file(self, file_path):
        self.script_name_label.config(text=f"{os.path.basename(file_path)}")
        with open(file_path, "r") as file:
            script_content = file.read()
        self.script_text.delete("1.0", "end")
        self.script_text.insert("1.0", script_content)
        self.colorize_text()

    def open_script(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("All Files", "*.*"), ("Python Scripts", "*.py"), ("Shell Scripts", "*.sh"),
                       ("Text Files", "*.txt"), ("TeX Files", "*.tex")])
        if file_path:
            self.open_file(file_path)
        self.set_modified_status(False)  # Reset the modification status

    def update_title(self):
        title = self.root.title()
        if is_modified and not title.startswith("*"):
            self.root.title("*" + title)
        elif not is_modified and title.startswith("*"):
            self.root.title(title[1:])

    def new(self, event=None):
        global file_name

        ans = messagebox.askquestion(title="Save File", message="Would you like to save this file?")
        if ans == "yes":
            self.save()

        file_name = ""
        self.script_text.delete('1.0', 'end')
        self.root.title("*New file - Script Editor")

    '''def open_file(self, event=None):
        self.new()
        file = filedialog.askopenfile()
        global file_name
        file_name = file.name
        self.text.insert(INSERT, file.read())'''

    def set_modified_status(self, value):
        global is_modified
        is_modified = value
        self.update_title()

    def update_modification_status(self, event):
        self.set_modified_status(True)

    def show_context_menu(self, event):
        def destroy_menu():
            context_menu.unpost()

        # Create the context menu
        context_menu = Menu(self.root, tearoff=0)
        context_menu.add_command(label="Cut", command=self.cut)
        context_menu.add_command(label="Copy", command=self.copy)
        context_menu.add_command(label="Paste", command=self.paste)
        context_menu.add_command(label="Duplicate", command=self.duplicate)
        context_menu.add_command(label="Delete", command=self.delete)

        # Post the context menu at the cursor location
        context_menu.post(event.x_root, event.y_root)

        # Give focus to the context menu
        context_menu.focus_set()

        # Bind the <Leave> event to destroy the context menu when the mouse cursor leaves it
        context_menu.bind("<Leave>", lambda e: destroy_menu())

        # Bind the <FocusOut> event to destroy the context menu when it loses focus
        context_menu.bind("<FocusOut>", lambda e: destroy_menu())

    def save_as_new_script(self):
        file_types = [("Python Scripts", "*.py"),
                      ("Shell Scripts", "*.sh"),
                      ("Text Files", "*.txt"),
                      ("LaTeX Files", "*.tex"),
                      ("All Files", "*.*")]
        file = filedialog.asksaveasfile(filetypes=file_types)
        if file is not None:
            # Get the selected file type
            selected_extension = file.name.split('.')[-1]
            # Append the selected extension to the file name
            file_path = file.name + '.' + selected_extension
            # Implement your save logic here using the file_path
            file.close()

    def save_script(self):
        script_name = self.script_name_label.cget("text").split(": ")[-1]
        if script_name:
            script_content = self.script_text.get("1.0", "end")
            self.save_file(script_name, script_content)
            self.set_modified_status(False)  # Reset the modification status
        else:
            self.save_as_new_script()

    def save_file(self, file_name, content):
        with open(file_name, "w") as file:
            file.write(content)
        messagebox.showinfo("Save", "Script saved successfully!")

    def save(self):
        global file_name

        if file_name:
            # Save the file
            with open(file_name, 'w') as file:
                file.write(self.script_text.get('1.0', 'end-1c'))

            # Update the window title
            self.root.title(file_name + " - Script Editor")
        else:
            self.save_as()

        # Remove the asterisk from the title
        self.root.title(self.root.title().replace('*', ''))

    def close(self, event=None):
        self.save()
        self.root.quit()

    def run_script(self):
        arguments = self.entry_arguments_entry.get()
        generate_stdout = self.generate_stdin.get()
        generate_stderr = self.generate_stdin_err.get()

        try:
            # Execute the script with provided arguments
            # Use the subprocess module to run the script as a separate process
            # result = subprocess.run([script] + arguments.split(), capture_output=True, shell=True)
            # TODO "/"
            process = subprocess.Popen(["bash"] + [
                self.directory_label.cget('text') + "/" + self.script_name_label.cget('text')] + arguments.split(),
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            stdout_data, stderr_data = process.communicate()

            # Print the stdout and stderr
            if generate_stdout:
                script_out_name = self.script_name_label.cget('text') + ".out"
                print(script_out_name)
                p = open(script_out_name, "w+")
                p.write(stdout_data.decode())

            if generate_stderr:
                script_err_name = self.script_name_label.cget('text') + ".err"
                p = open(script_err_name, "w+")
                p.write(stderr_data.decode())

            messagebox.showinfo("Script Execution", "Script executed successfully.")
        except Exception as e:
            messagebox.showerror("Script Execution", f"Error executing script:\n{str(e)}")

    def run_script_with_timeout(self, timeout_seconds):
        arguments = self.entry_arguments_entry.get()
        generate_stdout = self.generate_stdin.get()
        generate_stderr = self.generate_stdin_err.get()

        try:
            # Execute the script with provided arguments
            # Use the subprocess module to run the script as a separate process
            # result = subprocess.run([script] + arguments.split(), capture_output=True, shell=True)
            # TODO "/"
            process = subprocess.Popen(
                ["bash"] + [
                    self.directory_label.cget('text') + "/" + self.script_name_label.cget('text')] + arguments.split(),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            sleep(timeout_seconds)
            stdout_data, stderr_data = process.communicate()

            # Print the stdout and stderr
            if generate_stdout:
                script_out_name = self.script_name_label.cget('text') + ".out"
                print(script_out_name)
                p = open(script_out_name, "w+")
                p.write(stdout_data.decode())

            if generate_stderr:
                script_err_name = self.script_name_label.cget('text') + ".err"
                p = open(script_err_name, "w+")
                p.write(stderr_data.decode())

            messagebox.showinfo("Script Execution", "Script executed successfully.")
        except Exception as e:
            messagebox.showerror("Script Execution", f"Error executing script:\n{str(e)}")

    def run_script_once(self, schedule_time):
        script_path = os.path.join(self.directory_label.cget('text'), self.script_name_label.cget('text'))
        arguments = self.entry_arguments_entry.get()
        generate_stdout = self.generate_stdin.get()
        generate_stderr = self.generate_stdin_err.get()

        # Extract hour, minute, and AM/PM from the input time string
        match = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?', schedule_time)
        if not match:
            messagebox.showerror("Invalid Time", "Please enter a valid time in HH:MM AM/PM format.")
            return

        hour = int(match.group(1))
        minute = int(match.group(2))
        am_pm = match.group(3)

        # Adjust hour for 12-hour clock format
        if am_pm and am_pm.lower() == 'pm' and hour != 12:
            hour += 12

        if am_pm and am_pm.lower() == 'am' and hour == 12:
            hour = 0

        if not validate_time(hour, minute):
            return

        try:
            # Use the 'at' command to schedule the script execution and redirection
            at_time = f"{hour:02d}:{minute:02d}"

            stdout_redirect = f">{self.script_name_label.cget('text')}.out" if generate_stdout else "/dev/null"
            stderr_redirect = f"2>{self.script_name_label.cget('text')}.err" if generate_stderr else "/dev/null"

            at_command = f"atq; at {at_time} <<EOF\n{script_path} {arguments} {stdout_redirect} {stderr_redirect}\nEOF"

            process = subprocess.Popen(at_command, shell=True)
            process.wait()

            messagebox.showinfo("Script Scheduled", f"Script scheduled to run at {at_time}.")
        except Exception as e:
            messagebox.showerror("Error Scheduling Script", f"An error occurred while scheduling the script:\n{str(e)}")

    def run_script_crontab(self, minute, hour, day, month, day_of_week):
        if not minute or not hour or not day or not month or not day_of_week:
            messagebox.showerror("Error Scheduling Script", "All cron schedule fields must be filled.")
            return

        # Build the cron schedule string
        cron_schedule = f"{minute} {hour} {day} {month} {day_of_week}"

        script_path = os.path.join(self.directory_label.cget('text'), self.script_name_label.cget('text'))
        arguments = self.entry_arguments_entry.get()

        generate_stdout = self.generate_stdin.get()
        generate_stderr = self.generate_stdin_err.get()

        # Determine the full path for .out and .err files based on the selected directory
        out_file = os.path.join(self.directory_label.cget('text'), f"{self.script_name_label.cget('text')}.out")
        err_file = os.path.join(self.directory_label.cget('text'), f"{self.script_name_label.cget('text')}.err")

        try:
            stdout_redirect = f">{out_file}" if generate_stdout else "/dev/null"
            stderr_redirect = f"2>{err_file}" if generate_stderr else "/dev/null"

            # Use the 'crontab' command to set up the script execution schedule
            crontab_command = f"(crontab -l; echo '{cron_schedule} {script_path} {arguments} {stdout_redirect} {stderr_redirect}') | crontab -"
            process = subprocess.Popen(crontab_command, shell=True)
            process.wait()

            messagebox.showinfo("Script Scheduled", f"Script scheduled with cron: {cron_schedule}")
        except Exception as e:
            messagebox.showerror("Error Scheduling Script", f"An error occurred while scheduling the script:\n{str(e)}")

    def see_stdout(self):
        stdout_window = Toplevel(self.root)
        stdout_window.title("Standard Output (stdout)")
        stdout_text = Text(stdout_window)
        stdout_text.pack()

        script_out_name = self.script_name_label.cget('text') + ".out"
        try:
            with open(script_out_name, "r") as f:
                stdout_text.insert("1.0", f.read())
        except FileNotFoundError:
            stdout_text.insert("1.0", "No stdout data available.")

    def see_stderr(self):
        stderr_window = Toplevel(self.root)
        stderr_window.title("Standard Error (stderr)")
        stderr_text = Text(stderr_window)
        stderr_text.pack()

        script_err_name = self.script_name_label.cget('text') + ".err"
        try:
            with open(script_err_name, "r") as f:
                stderr_text.insert("1.0", f.read())
        except FileNotFoundError:
            stderr_text.insert("1.0", "No stderr data available.")

        # Configure the text widget to use red font color
        stderr_text.tag_configure("red", foreground="red")
        stderr_text.tag_add("red", "1.0", "end")

    def on_text_change(self, event=None):
        global is_modified

        if not is_modified:
            is_modified = True
            self.root.title("*" + self.root.title())

    def remove_asterisk_from_title(self):
        title = self.root.title()
        if title.startswith("*"):
            self.root.title(title[1:])

    def cut(self, event=None):
        self.set_modified_status(True)
        self.script_text.event_generate("<<Cut>>")
        # first clear the previous text on the clipboard.
        self.root.clipboard_clear()
        self.text.clipboard_append(string=self.text.selection_get())
        # index of the first and yhe last letter of our selection.
        self.text.delete(index1=SEL_FIRST, index2=SEL_LAST)

    def copy(self, event=None):
        self.set_modified_status(True)
        self.script_text.event_generate("<<Copy>>")
        # first clear the previous text on the clipboard.
        print(self.text.index(SEL_FIRST))
        print(self.text.index(SEL_LAST))
        self.root.clipboard_clear()
        self.text.clipboard_append(string=self.text.selection_get())

    def paste(self, event=None):
        self.set_modified_status(True)
        self.script_text.event_generate("<<Paste>>")
        # get gives everyting from the clipboard and paste it on the current cursor position
        # it does'nt removes it from the clipboard.
        self.text.insert(INSERT, self.root.clipboard_get())

    def duplicate(self, event=None):
        self.set_modified_status(True)
        self.script_text.event_generate("<<Duplicate>>")
        selected_text = self.text.get("sel.first", "sel.last")
        self.text.insert("insert", selected_text)

    def delete(self):
        self.text.delete(index1=SEL_FIRST, index2=SEL_LAST)

    def undo(self):
        self.text.edit_undo()

    def redo(self):
        self.text.edit_redo()

    def check(self, value):
        self.text.tag_remove('found', '1.0', END)
        self.text.tag_config('found', foreground='red')
        list_of_words = value.split(' ')
        for word in list_of_words:
            idx = '1.0'
            while idx:
                idx = self.text.search(word, idx, nocase=1, stopindex=END)
                if idx:
                    lastidx = '%s+%dc' % (idx, len(word))
                    self.text.tag_add('found', idx, lastidx)
                    print(lastidx)
                    idx = lastidx

    def find_text(self, event=None):
        search_toplevel = Toplevel(self.root)
        search_toplevel.title('Find Text')
        search_toplevel.transient(self.root)
        search_toplevel.resizable(False, False)
        Label(search_toplevel, text="Find All:").grid(row=0, column=0, sticky='e')
        search_entry_widget = Entry(search_toplevel, width=25)
        search_entry_widget.grid(row=0, column=1, padx=2, pady=2, sticky='we')
        search_entry_widget.focus_set()
        Button(search_toplevel, text="Ok", underline=0, command=lambda: self.check(search_entry_widget.get())).grid(row=0,
                                                                                                               column=2,
                                                                                                               sticky='e' + 'w',
                                                                                                               padx=2,
                                                                                                               pady=5)
        Button(search_toplevel, text="Cancel", underline=0,
               command=lambda: self.find_text_cancel_button(search_toplevel)).grid(
            row=0, column=4, sticky='e' + 'w', padx=2, pady=2)

    # remove search tags and destroys the search box
    def find_text_cancel_button(self, search_toplevel):
        self.text.tag_remove('found', '1.0', END)
        search_toplevel.destroy()
        return "break"

    def make_tag(self):
        current_tags = self.text.tag_names()
        if "bold" in current_tags:
            weight = "bold"
        else:
            weight = "normal"

        if "italic" in current_tags:
            slant = "italic"
        else:
            slant = "roman"

        if "underline" in current_tags:
            underline = 1
        else:
            underline = 0

        if "overstrike" in current_tags:
            overstrike = 1
        else:
            overstrike = 0

        big_font = tkinter.font.Font(self.text, self.text.cget("font"))
        big_font.configure(slant=slant, weight=weight, underline=underline, overstrike=overstrike,
                           family=current_font_family, size=current_font_size)
        text.tag_config("BigTag", font=big_font, foreground=fontColor, background=fontBackground)
        if "BigTag" in current_tags:
            text.tag_remove("BigTag", 1.0, END)
        text.tag_add("BigTag", 1.0, END)

    def change_color(self):
        color = colorchooser.askcolor(initialcolor='#ff0000')
        color_name = color[1]
        global fontColor
        fontColor = color_name
        current_tags = text.tag_names()
        if "font_color_change" in current_tags:
            # first char is bold, so unbold the range
            text.tag_delete("font_color_change", 1.0, END)
        else:
            # first char is normal, so bold the whole selection
            text.tag_add("font_color_change", 1.0, END)
        self.make_tag()

    def save_as(self):
        global file_name

        new_file_name = filedialog.asksaveasfilename(defaultextension=".txt",
                                                     filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if new_file_name:
            file_name = new_file_name
            self.save()
        else:
            messagebox.showinfo("Info", "File saving canceled.")

    def rename(self, event=None):
        global file_name
        if file_name == "":
            # Prompt the user to enter the file path or select a file using a file dialog
            file_path = simpledialog.askstring("Rename", "Enter file path or select a file")
            if not file_path:
                # User cancelled the operation
                return

            print("File path:", file_path)
            if not os.path.exists(file_path):
                messagebox.showerror("Error", "File does not exist")
                return

            file_name = file_path

        # Extract the directory path and file name
        dir_path, old_name = os.path.split(file_name)
        new_name = simpledialog.askstring("Rename", "Enter new name")

        try:
            # Rename the file
            new_path = os.path.join(dir_path, new_name)
            os.rename(file_name, new_path)
            file_name = new_path
            self.root.title(file_name + " - Script Editor")
        except OSError as e:
            messagebox.showerror("Error", f"Failed to rename file: {e}")

    # EDIT MENU METHODS

    def select_all(self, event=None):
        self.text.tag_add(SEL, "1.0", END)

    def delete_all(self):
        self.text.delete(1.0, END)
