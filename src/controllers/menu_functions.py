import json
import os
import sys
import subprocess
from tkinter import Menu, Button, messagebox, filedialog, END, Label, Checkbutton, Entry, Text, BooleanVar

from PIL import Image, ImageTk

from src.controllers.scheduled_tasks import open_cron_window, open_at_window, open_scheduled_tasks_window, open_new_at_task_window, \
    open_new_crontab_task_window
from src.models.file_operations import prompt_rename_file
from src.models.script_operations import get_operative_system, see_stdout, see_stderr, run_script, run_script_windows, \
    run_script_with_timeout
from src.controllers.script_tasks import analyze_csv_data, render_markdown_to_html, generate_html_from_markdown, \
    run_javascript_analysis, analyze_generic_text_data, render_latex_to_pdf, generate_latex_pdf, run_python_script, \
    change_interpreter, render_markdown_to_latex
from src.localization import localization_data
from src.views.edit_operations import undo, redo, duplicate

from src.views.tk_utils import toolbar, menu, root, script_name_label, script_text, is_modified, \
    file_name, last_saved_content, local_python_var, show_directory_view_var, show_file_view_var, frm, directory_label, \
    script_frm, content_frm, entry_arguments_entry, generate_stdin, generate_stdin_err, show_arguments_view_var, \
    show_run_view_var, run_frm, line_frm, show_timeout_view_var, show_interactive_view_var, interactive_frm, \
    show_filesystem_view_var, filesystem_frm
from src.controllers.tool_functions import (find_text, change_color, open_search_replace_dialog, open_terminal_window,
                                            open_ai_assistant_window, open_webview, open_terminal_window,
                                            create_url_input_window, open_ipynb_window,
                                            create_settings_window, open_git_window,
                                            open_image_generation_window, open_music_generation_window,
                                            open_audio_generation_window, open_kanban_window, open_winget_window,
                                            open_system_info_window)
from src.controllers.parameters import read_config_parameter, write_config_parameter

from src.controllers.tool_functions import open_git_window, git_console_instance
from lib.git import git_icons
import lib.git as git
from src.views.ui_elements import Tooltip

# Add this line
git_console_instance = None

house_icon = "🏠"
open_icon = "📂"
save_icon = "💾"
save_new_icon = "🆕"
undo_icon = "⮪"
redo_icon = "⮬"
run_icon = "▶"

file_types = [
    ("All Files", "*.*"),
    ("Python Scripts", "*.py"),
    ("Shell Scripts", "*.sh"),
    ("PowerShell Scripts", "*.ps1"),
    ("Text Files", "*.txt"),
    ("LaTeX Files", "*.tex"),
    ("CSV Files", "*.csv"),
    ("JavaScript Files", "*.js"),
    ("HTML Files", "*.html"),
    ("CSS Files", "*.css"),
    ("Java Files", "*.java"),
    ("C++ Files", "*.cpp"),
    ("Ruby Scripts", "*.rb"),
    ("Perl Scripts", "*.pl"),
    ("PHP Scripts", "*.php"),
    ("Python Notebooks", "*.ipynb"),
    ("Swift Scripts", "*.swift"),
    ("Go Files", "*.go"),
    ("R Scripts", "*.r"),
    ("Rust Files", "*.rs"),
    ("Dart Files", "*.dart")
]


def init_git_console():
    global git_console_instance
    if git_console_instance is None:
        git_console_instance = "Something"


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


'''def duplicate():
    """
        Duplicates the selected text in the script editor.

        This function creates a copy of the selected text and inserts it immediately after the current selection.

        Parameters:
        None

        Returns:
        None
        """
    # set_modified_status(True)
    script_text.event_generate("<<Duplicate>>")'''


# Help Menu
def about(event=None):
    """
        Displays the 'About' information of the application.

        This function triggers a messagebox that provides details about the ScriptsEditor, including its creation and version.

        Parameters:
        event (optional): An event object, not directly used in this function.

        Returns:
        None
    """
    messagebox.showinfo(localization_data['about_scripts_editor'],
                        localization_data['scripts_editor_info'])


def set_modified_status(value):
    """
        Sets the modified status of the current file.

        This function updates the global 'is_modified' flag to the given value, indicating whether the current file
        has unsaved changes.

        Parameters:
        value (bool): The modified status to set (True or False).

        Returns:
        None
    """
    global is_modified  # Add file_name to the global declaration
    is_modified = value
    update_title()


def update_title():
    """
    Updates the application window's title based on the file's modified status and the current file name.
    """
    global is_modified

    title = os.path.basename(file_name) if file_name else localization_data['untitled']

    if is_modified:
        root.title(f"*{title} - {localization_data['scripts_editor']}")
    else:
        root.title(f"{title} - {localization_data['scripts_editor']}")

    script_name_label.config(text=f"{localization_data['script_name_label']}{os.path.basename(title)}")


def new():
    """
        Creates a new file in the editor.
        Prompts the user to save the current file if it is modified, then clears the text editor.
    """
    global is_modified
    if is_modified:
        response = messagebox.askyesnocancel(localization_data['save_file'], localization_data['save_changes_confirmation'])
        if response:  # User chose 'Yes'
            save()
            clear_editor()
        elif response is None:  # User chose 'Cancel'
            return  # Cancel new file operation
        elif not response:
            clear_editor()

    file_name = ""
    clear_editor()  # Clears the editor after handling the save dialog


def clear_editor():
    """
        Clears the text editor and resets the title and modified flag.
    """
    global file_name
    global is_modified

    script_text.delete('1.0', 'end')
    file_name = ""
    is_modified = False
    update_title()


def on_text_change(event=None):
    """
        Updates the modified flag when text in the editor changes.
    """
    global is_modified
    current_content = script_text.get("1.0", END).strip()

    # Check if the content is empty and if the file is considered 'new' (i.e., not yet saved or loaded from disk)
    if current_content != last_saved_content:
        if not is_modified:  # Update only if there are changes
            is_modified = True
            update_title()
            print("DEBUG: WE REACHED ORIGINAL FILE TEXT CONTENT")  # Debug print statement added
    elif not current_content and (not file_name or file_name == "Untitled"):
        if is_modified:  # Only update if the status is currently 'modified'
            is_modified = False
            update_title()
    else:
        if not is_modified:  # Only update if the status is currently 'not modified'
            is_modified = True
            update_title()


def open_file(file_path):
    """
        Opens the specified file and updates the editor with its contents.

        This function reads the content from the specified file path and updates the script editor. It tries various
        encodings to ensure correct file reading and updates the UI based on the file extension.

        Parameters:
        file_path (str): The path of the file to open.

        Returns:
        None
    """
    global is_modified, file_name, last_saved_content

    file_name = file_path
    # Update the directory label with the directory of the opened file
    directory_path = os.path.dirname(file_path)
    directory_label.config(text=f"{directory_path}")
    script_name_label.config(text=f"{localization_data['save_changes']}{os.path.basename(file_path)}")

    # Try opening the file with different encodings
    encodings = ['utf-8', 'cp1252', 'ISO-8859-1', 'utf-16']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                script_content = file.read()
                break
        except UnicodeDecodeError:
            continue
    else:
        # If all encodings fail, use 'utf-8' with 'replace' option
        with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
            script_content = file.read()
            last_saved_content = script_content  # Update the last saved content

    script_text.delete("1.0", END)
    script_text.insert("1.0", script_content)

    # Update dynamic menu and title based on file extension
    ext = os.path.splitext(file_path)[1]
    update_menu_based_on_extension(ext)
    # Reset the modified flag after loading the file
    is_modified = False
    update_title()


def open_script():
    """
        Opens an existing file into the script editor.

        This function displays a file dialog for the user to choose a file. Once a file is selected, it is opened
        and its contents are displayed in the script editor.

        Parameters:
        None

        Returns:
        None
    """
    if is_modified:
        response = messagebox.askyesnocancel(localization_data['save_changes'],
                                             localization_data['save_confirmation'])
        if response:  # User wants to save changes
            if not save():
                return  # If save was not successful, cancel the file open operation
        elif response is None:  # User cancelled the prompt
            return  # Cancel the file open operation

    # If there are no unsaved changes, or the user has dealt with them, show the open file dialog
    file_path = filedialog.askopenfilename(filetypes=file_types)
    if file_path:
        open_file(file_path)

def create_csv_menu(parent_menu):
    """
        Creates a submenu for CSV-related operations.

        This function adds specific options related to CSV files, such as data analysis, to the given parent menu.

        Parameters:
        parent_menu (Menu): The parent menu to which the CSV submenu will be added.

        Returns:
        None
    """
    entries = {
        "Analyze Data": analyze_csv_data
    }
    create_submenu(parent_menu, "CSV", entries)


def create_bash_menu(parent_menu):
    parent_menu.add_command(label="Analyze Data")


def create_powershell_menu(parent_menu):
    parent_menu.add_command(label="Analyze Data")


def create_markdown_menu(parent_menu):
    entries = {
        "Render HTML": render_markdown_to_html,
        "Generate HTML": generate_html_from_markdown,
        "Render LaTeX PDF": render_markdown_to_latex
    }
    create_submenu(parent_menu, "Markdown", entries)


def create_javascript_menu(parent_menu):
    entries = {
        "Analyze Data": run_javascript_analysis
    }
    create_submenu(parent_menu, "JavaScript", entries)


def create_html_menu(parent_menu):
    parent_menu.add_command(label="Analyze Data")


def create_css_menu(parent_menu):
    parent_menu.add_command(label="Analyze Data")


def create_java_menu(parent_menu):
    parent_menu.add_command(label="Analyze Data")


def create_cpp_menu(parent_menu):
    parent_menu.add_command(label="Analyze Data")


def create_generic_text_menu(parent_menu):
    entries = {
        "Analyze Data": analyze_generic_text_data
    }
    create_submenu(parent_menu, "Text", entries)


def create_latex_menu(parent_menu):
    entries = {
        "Render PDF": render_latex_to_pdf,
        "Generate PDF": generate_latex_pdf
    }
    create_submenu(parent_menu, "LaTeX", entries)


def create_python_menu(parent_menu):
    entries = {
        "Create Virtual Environment": change_interpreter,  # create_venv_at_path, / Change Virtual Environment
        "Manage pip packages": change_interpreter,  # show_local_pip_packages
        "Change Interpreter": change_interpreter
        # Add more options as needed
    }

    parent_menu.add_checkbutton(
        label="ScriptsEditor Local Python 3",
        variable=local_python_var,
        command=run_python_script
    )

    create_submenu(parent_menu, "Interpreter", entries)


def update_menu_based_on_extension(ext):
    """
    Updates the application menu based on the file extension of the currently open file.

    Parameters:
    ext (str): The file extension of the currently open file.

    Returns:
    None
    """

    # Menu creators for different file extensions
    menu_creators = {
        ".py": create_python_menu,
        ".csv": create_csv_menu,
        ".txt": create_generic_text_menu,
        ".md": create_markdown_menu,
        ".js": create_javascript_menu,
        ".html": create_html_menu,
        ".css": create_css_menu,
        ".java": create_java_menu,
        ".cpp": create_cpp_menu,
        ".tex": create_latex_menu,
        ".sh": create_bash_menu,
        ".ps1": create_powershell_menu
    }

    # File type labels
    file_type_labels = {
        ".py": "Python",
        ".csv": "CSV",
        ".txt": "Text",
        ".md": "Markdown",
        ".js": "Javascript",
        ".html": "HTML",
        ".css": "CSS",
        ".java": "Java",
        ".cpp": "C++",
        ".tex": "LaTeX",
        ".sh": "Bash",
        ".ps1": "PowerShell"
    }

    # Find the index of the 'Jobs' menu
    jobs_menu_index = None
    for index in range(menu.index('end') + 1):
        if 'Jobs' in menu.entrycget(index, 'label'):
            jobs_menu_index = index
            break

    if jobs_menu_index is None:
        return

    # Check if a dynamic menu already exists and delete it if found
    dynamic_menu_index = None
    for index in range(menu.index('end') + 1):
        try:
            if menu.entrycget(index, 'label') in file_type_labels.values() or menu.entrycget(index, 'label') == "Other":
                dynamic_menu_index = index
                menu.delete(dynamic_menu_index)
                break
        except Exception as e:
            continue

    # Create and insert the new dynamic menu
    dynamic_menu = Menu(menu, tearoff=0, name='dynamic')
    if ext in menu_creators:
        menu_creators[ext](dynamic_menu)
        label = file_type_labels.get(ext, "Other")
    else:
        create_generic_text_menu(dynamic_menu)
        label = "Other"

    # Insert the dynamic menu after the Jobs menu
    menu.insert_cascade(jobs_menu_index + 1, label=label, menu=dynamic_menu)


def update_title_with_filename(file_name):
    """
        Updates the window title with the name of the currently open file.

        This function sets the application window's title to include the base name of the given file path.

        Parameters:
        file_name (str): The full path of the currently open file.

        Returns:
        None
    """
    # Esta función actualizará el título de la ventana con el nuevo nombre de archivo
    base_name = os.path.basename(file_name)
    root.title(f"{base_name} - Scripts Editor")


def update_modification_status(event):
    """
        Updates the modification status of the file to 'modified'.

        This function should be called whenever a change is made to the text content, setting the file's status
        as modified.

        Parameters:
        event: The event object representing the triggering event.

        Returns:
        None
    """
    set_modified_status(True)


def save():
    """
    Saves the current file. If the file doesn't have a name, calls 'save_as' function.
    """
    global is_modified, file_name

    if not file_name or file_name == "Untitled":
        return save_as()  # If no filename, use 'Save As' to get a new filename

    try:
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(script_text.get('1.0', 'end-1c'))
            is_modified = False
            update_title()
            messagebox.showinfo("Save", "File saved successfully!")
            return True
    except Exception as e:
        messagebox.showerror("Save Error", f"An error occurred: {e}")
        return False


def save_as():
    print("ENTERING SAVE AS")
    """
        Opens a 'Save As' dialog to save the current file with a specified name.
    """
    global file_name
    global is_modified

    new_file_name = filedialog.asksaveasfilename(defaultextension=".*", filetypes=file_types)
    if not new_file_name:
        return False

    file_name = new_file_name
    save()
    update_script_name_label(new_file_name)
    update_title()
    return True


def close(event=None):
    if save():  # Proceed only if the user saves the file or chooses not to save
        root.quit()


def save_file(file_name, content):
    with open(file_name, "w", encoding='utf-8') as file:
        file.write(content)
    messagebox.showinfo("Save", "Script saved successfully!")


def save_script():
    """
    Triggered when 'Save' is clicked. Saves the current file or prompts to save as new if it's a new file.
    """
    global file_name, is_modified

    if not file_name or file_name == "Untitled":
        # If the file is new (i.e., no file_name or it's 'Untitled'), use 'save_as_new_script'
        print("Saving new script...")
        save_as_new_script()
    else:
        # If the file exists, just save it
        print("Saving existing script...")
        content = script_text.get("1.0", "end-1c")  # Get text from editor
        try:
            with open(file_name, 'w', encoding='utf-8') as file:
                file.write(content)
            is_modified = False  # Reset modification status
            update_title()  # Update the window title
            update_script_name_label(file_name)  # Ensure the script name label is updated
            messagebox.showinfo("Save", "File saved successfully!")
        except Exception as e:
            messagebox.showerror("Save Error", f"An error occurred while saving: {e}")


def save_as_new_script():
    """
    Saves the current content as a new file. Opens a file dialog for the user to choose where to save.
    """
    global file_name, is_modified

    new_file_name = filedialog.asksaveasfilename(defaultextension=".*", filetypes=file_types)
    if not new_file_name:
        return  # User cancelled the 'Save As' operation

    file_name = new_file_name  # Update file name
    save_script()  # Call save_script to save the file


def update_script_name_label(file_path):
    """
    Updates the script name label with the base name of the provided file path.
    """
    base_name = os.path.basename(file_path)
    script_name_label.config(text=f"File Name: {base_name}")


# TOOLBAR BUTTONS
# new
new_button = Button(name="toolbar_b2", borderwidth=1, command=new, width=20, height=20)
photo_new = Image.open("icons/new.png")
photo_new = photo_new.resize((18, 18), Image.LANCZOS)
image_new = ImageTk.PhotoImage(photo_new)
new_button.config(image=image_new)
new_button.grid(in_=toolbar, row=0, column=0, padx=4, pady=4, sticky="w")

# save
save_button = Button(name="toolbar_b1", borderwidth=1, command=save, width=20, height=20)
photo_save = Image.open("icons/save.png")
photo_save = photo_save.resize((18, 18), Image.LANCZOS)
image_save = ImageTk.PhotoImage(photo_save)
save_button.config(image=image_save)
save_button.grid(in_=toolbar, row=0, column=1, padx=4, pady=4, sticky="w")

# open
open_button = Button(name="toolbar_b3", borderwidth=1, command=open_file, width=20, height=20)
photo_open = Image.open("icons/open.png")
photo_open = photo_open.resize((18, 18), Image.LANCZOS)
image_open = ImageTk.PhotoImage(photo_open)
open_button.config(image=image_open)
open_button.grid(in_=toolbar, row=0, column=2, padx=4, pady=4, sticky="w")

# copy
copy_button = Button(name="toolbar_b4", borderwidth=1, command=copy, width=20, height=20)
photo_copy = Image.open("icons/copy.png")
photo_copy = photo_copy.resize((18, 18), Image.LANCZOS)
image_copy = ImageTk.PhotoImage(photo_copy)
copy_button.config(image=image_copy)
copy_button.grid(in_=toolbar, row=0, column=3, padx=4, pady=4, sticky="w")

# cut
cut_button = Button(name="toolbar_b5", borderwidth=1, command=cut, width=20, height=20)
photo_cut = Image.open("icons/cut.png")
photo_cut = photo_cut.resize((18, 18), Image.LANCZOS)
image_cut = ImageTk.PhotoImage(photo_cut)
cut_button.config(image=image_cut)
cut_button.grid(in_=toolbar, row=0, column=4, padx=4, pady=4, sticky="w")

# paste
paste_button = Button(name="toolbar_b6", borderwidth=1, command=paste, width=20, height=20)
photo_paste = Image.open("icons/paste.png")
photo_paste = photo_paste.resize((18, 18), Image.LANCZOS)
image_paste = ImageTk.PhotoImage(photo_paste)
paste_button.config(image=image_paste)
paste_button.grid(in_=toolbar, row=0, column=5, padx=4, pady=4, sticky="w")


# duplicate
duplicate_button = Button(name="toolbar_b7", borderwidth=1, command=duplicate, width=20, height=20)
photo_duplicate = Image.open("icons/duplicate.png")
photo_duplicate = photo_paste.resize((18, 18), Image.LANCZOS)
image_duplicate = ImageTk.PhotoImage(photo_paste)
duplicate_button.config(image=image_duplicate)
duplicate_button.grid(in_=toolbar, row=0, column=6, padx=4, pady=4, sticky="w")

# redo
redo_button = Button(name="toolbar_b8", borderwidth=1, command=redo, width=20, height=20)
photo_redo = Image.open("icons/redo.png")
photo_redo = photo_redo.resize((18, 18), Image.LANCZOS)
image_redo = ImageTk.PhotoImage(photo_redo)
redo_button.config(image=image_redo)
redo_button.grid(in_=toolbar, row=0, column=7, padx=4, pady=4, sticky="w")

# undo
undo_button = Button(name="toolbar_b9", borderwidth=1, command=undo, width=20, height=20)
photo_undo = Image.open("icons/undo.png")
photo_undo = photo_undo.resize((18, 18), Image.LANCZOS)
image_undo = ImageTk.PhotoImage(photo_undo)
undo_button.config(image=image_undo)
undo_button.grid(in_=toolbar, row=0, column=8, padx=4, pady=4, sticky="w")

# find
find_button = Button(name="toolbar_b10", borderwidth=1, command=find_text, width=20, height=20)
photo_find = Image.open("icons/find.png")
photo_find = photo_find.resize((18, 18), Image.LANCZOS)
image_find = ImageTk.PhotoImage(photo_find)
find_button.config(image=image_find)
find_button.grid(in_=toolbar, row=0, column=9, padx=4, pady=4, sticky="w")


def toggle_directory_view_visibility(frame):
    global current_directory
    global directory_label
    print("DIRECTORY VIEW VISIBILITY TOGGLED")

    def select_directory():
        """
            Opens a dialog for the user to select a directory, and changes the current working directory to the selected one.

            After the directory is selected, the function updates the directory label in the UI and opens the first text file
            (if any) in the selected directory.

            Parameters:
            None

            Returns:
            None
        """
        directory = filedialog.askdirectory()
        if directory:
            os.chdir(directory)
            global current_directory  # Declare current_directory as global if it's not in the same file
            current_directory = directory  # Update the current_directory variable
            directory_label.config(text=f"{directory}")
            # Ask user if they want to open the first text file
            if messagebox.askyesno(localization_data['open_script'],
                                   localization_data['open_first_file_from_directory']):
                open_first_text_file(directory)

    def open_first_text_file(directory):
        """
            Opens the first text file in the given directory.

            This function scans the specified directory for text files and, if found, opens the first one. It is typically
            used after changing the working directory to automatically open a text file from that directory.

            Parameters:
            directory (str): The directory path in which to search for text files.

            Returns:
            None
        """
        text_files = get_text_files(directory)
        if text_files:
            file_path = os.path.join(directory, text_files[0])
            open_file(file_path)

    def open_current_directory():
        directory = directory_label.cget("text")
        if sys.platform == "win32":
            os.startfile(directory)
        elif sys.platform == "darwin":
            subprocess.run(["open", directory])
        else:  # Assuming Linux or similar
            subprocess.run(["xdg-open", directory])

    def get_text_files(directory):
        """
            Retrieves a list of text files in the specified directory.

            This function scans the provided directory and creates a list of all files ending with a '.txt' extension.

            Parameters:
            directory (str): The directory path in which to search for text files.

            Returns:
            list: A list of text file names found in the directory.
        """
        text_files = []
        for file in os.listdir(directory):
            if file.endswith(".txt"):
                text_files.append(file)
        return text_files

    if show_directory_view_var.get() == 1:
        write_config_parameter("options.view_options.is_directory_view_visible", "true")

        frame.grid(row=0, column=0, pady=0, sticky="ew")

        directory_button = Button(frame, text=house_icon, command=select_directory)
        directory_button.grid(column=0, row=0, sticky="w")

        Tooltip(directory_button, localization_data['choose_working_directory'])

        directory_label.grid(column=1, row=0, padx=5, sticky="ew")
        directory_label.bind("<Double-1>", lambda event: open_current_directory())
        Tooltip(directory_label, localization_data['current_directory'])
    else:
        write_config_parameter("options.view_options.is_directory_view_visible", "false")
        frame.grid_forget()

    # print("IS DIRECTORY VISIBLE?\t", read_config_parameter("options").get("is_directory_view_visible"))


def toggle_file_view_visibility(frame):
    if show_file_view_var.get() == 1:
        write_config_parameter("options.view_options.is_file_view_visible", "true")

        frame.grid(row=1, column=0, pady=0, sticky="ew")
        frame.grid_columnconfigure(2, weight=1)  # Make column 2 (file name entry) expandable

        open_button = Button(frame, text=open_icon, command=open_script)
        open_button.grid(column=0, row=0)
        Tooltip(open_button, localization_data['open_script'])

        script_name_label.grid(column=2, row=0, sticky="we", padx=5, pady=5)  # Expand to the right
        script_name_label.bind("<Double-1>", lambda event: prompt_rename_file())
        Tooltip(script_name_label, localization_data['file_name'])

        save_button = Button(frame, text=save_icon, command=save_script)
        save_button.grid(column=3, row=0, sticky="e")  # Align to the right
        Tooltip(save_button, localization_data['save_script'])

        save_new_button = Button(frame, text=save_new_icon, command=save_as_new_script)
        save_new_button.grid(column=4, row=0, sticky="e")  # Align to the right
        Tooltip(save_new_button, localization_data['save_as_new_script'])

        undo_button = Button(frame, text=undo_icon, command=undo)
        undo_button.grid(column=5, row=0, sticky="e")  # Align to the right
        Tooltip(undo_button, localization_data['undo'])

        redo_button = Button(frame, text=redo_icon, command=redo)
        redo_button.grid(column=6, row=0, sticky="e")  # Align to the right
        Tooltip(redo_button, localization_data['redo'])
    else:
        write_config_parameter("options.view_options.is_file_view_visible", "false")
        frame.grid_forget()


def toggle_arguments_view_visibility(frame):
    if show_arguments_view_var.get() == 1:
        write_config_parameter("options.view_options.is_arguments_view_visible", "true")
        frame.grid(row=5, column=0, pady=0, sticky="ew")  # Set sticky to "ew" to fill horizontally

        entry_arguments_label = Label(frame, text=localization_data['entry_arguments'])
        entry_arguments_label.grid(row=0, column=0, padx=5, pady=0, sticky="w")

        entry_placeholder = ""  # Enter arguments...
        entry_arguments_entry.insert(0, entry_placeholder)
        entry_arguments_entry.grid(row=0, column=1, sticky="e")
        Tooltip(entry_arguments_entry, localization_data['enter_arguments'])

        generate_stdin_check = Checkbutton(frame, text=localization_data['stdout'], variable=generate_stdin)
        generate_stdin_check.grid(row=0, column=2, sticky="e")  # sticky to "e" for right alignment
        Tooltip(generate_stdin_check, localization_data['generate_stdout'])

        see_stderr_check = Checkbutton(frame, text=localization_data['stderr'], variable=generate_stdin_err)
        see_stderr_check.grid(row=0, column=3, padx=10, sticky="e")  # Set sticky to "e" for right alignment
        Tooltip(see_stderr_check, localization_data['generate_stderr'])

        stdout_button = Button(frame, text=localization_data['see_stdout'], command=see_stdout)
        stdout_button.grid(column=2, row=1, padx=10, sticky="e")  # Align to the right
        Tooltip(stdout_button, localization_data['see_stdout_tooltip'])

        stderr_button = Button(frame, text=localization_data['see_stderr'], command=see_stderr)
        stderr_button.grid(column=3, row=1, padx=10, sticky="e")  # Align to the right
        Tooltip(stderr_button, localization_data['see_stderr_tooltip'])
    else:
        write_config_parameter("options.view_options.is_arguments_view_visible", "false")
        frame.grid_forget()


def toggle_run_view_visibility(frame):
    if show_run_view_var.get() == 1:
        write_config_parameter("options.view_options.is_run_view_visible", "true")
        if get_operative_system() != "Windows":
            frame.grid(row=8, column=0, pady=0, sticky="nsew")  # Set sticky to "e" for right alignment
            Label(frame, text=localization_data['run_inmediately']).grid(row=0, column=0, sticky="e", padx=5, pady=0)
            run_button = Button(frame, text=run_icon, command=run_script)
            run_button.grid(row=0, column=1, sticky="e", padx=5, pady=0)
            Tooltip(run_button, localization_data['run_script'])
        else:
            frame.grid(row=8, column=0, pady=0, sticky="nsew")  # Set sticky to "e" for right alignment
            Label(frame, text=localization_data['run_inmediately']).grid(row=0, column=0, sticky="e", padx=5, pady=0)
            run_button = Button(frame, text=run_icon, command=run_script_windows)
            run_button.grid(row=0, column=1, sticky="e", padx=5, pady=0)
            Tooltip(run_button, localization_data['run_script'])
    else:
        write_config_parameter("options.view_options.is_run_view_visible", "false")
        frame.grid_forget()


def toggle_timeout_view_visibility(frame):
    if show_timeout_view_var.get() == 1:
        write_config_parameter("options.view_options.is_timeout_view_visible", "true")
        if get_operative_system() != "Windows":
            frame.grid(row=9, column=0, pady=0, sticky="nsew")

            Label(frame, text=localization_data['script_timeout']).grid(row=0, column=0, sticky="e", padx=5, pady=0)

            seconds_entry = Entry(frame, width=15)
            seconds_entry.grid(column=1, row=0, padx=(10, 0))
            Tooltip(seconds_entry, localization_data['number_of_seconds'])

            run_button = Button(frame,
                                text=run_icon,
                                command=lambda: run_script_with_timeout(timeout_seconds=float(seconds_entry.get()))
                                )
            run_button.grid(row=0, column=2, sticky="e", padx=15, pady=0)
            Tooltip(run_button, localization_data['set_duration_for_script_execution'])
        else:
            frame.grid(row=9, column=0, pady=0, sticky="nsew")

            Label(frame, text=localization_data['script_timeout']).grid(row=0, column=0, sticky="e", padx=5, pady=0)

            seconds_entry = Entry(frame, width=15)
            seconds_entry.grid(column=1, row=0, padx=(10, 0))
            Tooltip(seconds_entry, localization_data['number_of_seconds'])

            run_button = Button(frame,
                                text=run_icon,
                                command=lambda: run_script_with_timeout(timeout_seconds=float(seconds_entry.get()))
                                )
            run_button.grid(row=0, column=2, sticky="e", padx=15, pady=0)
            Tooltip(run_button, localization_data['set_duration_for_script_execution'])
    else:
        write_config_parameter("options.view_options.is_timeout_view_visible", "false")
        frame.grid_forget()


def toggle_interactive_view_visibility(frame):
    if show_interactive_view_var.get() == 1:
        write_config_parameter("options.view_options.is_interactive_view_visible", "true")
        # Make sure interactive_frm expands horizontally
        frame.grid(row=4, column=0, pady=0, sticky="ew")  # Set sticky to "ew" to fill horizontally

        # Create the Text widget with sticky option to expand horizontally
        input_field = Text(frame, height=1)
        input_field.grid(row=7, column=0, padx=8, pady=(0, 8), sticky="ew")

        # Ensure that interactive_frm expands horizontally and the column weights are set
        frame.grid_columnconfigure(0, weight=1)
    else:
        write_config_parameter("options.view_options.is_interactive_view_visible", "false")
        frame.grid_forget()


def toggle_filesystem_view_visibility(frame):
    if show_filesystem_view_var.get() == 1:
        frame.grid(row=2, column=2, sticky='nsew')
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
    else:
        frame.grid_remove()


def add_view_section_to_menu(options_parameter_name, view_variable, menu_section, view_section_name, frame, function):
    print("ADDING VIEW SECTION TO MENU (", view_section_name, ")")
    # Assuming the structure is now options.options.view_options.is_*_view_visible
    is_view_visible = read_config_parameter(f"options.view_options.{options_parameter_name}")

    if isinstance(view_variable, BooleanVar):
        view_variable.set(is_view_visible if isinstance(is_view_visible, bool) else True)
    else:
        view_variable.set(1 if is_view_visible else 0)

    menu_section.add_checkbutton(
        label=view_section_name,
        onvalue=1,
        offvalue=0,
        variable=view_variable,
        command=lambda: toggle_view(frame, function, options_parameter_name, view_variable)
    )
    toggle_view(frame, function, options_parameter_name, view_variable)


def toggle_view(frame, function, options_parameter_name, view_variable):
    print("TOGGLED VIEW!!!")
    function(frame)
    update_config(options_parameter_name, view_variable.get())


def update_config(option_name, value):
    user_config_file = "data/user_config.json"
    try:
        with open(user_config_file, 'r') as config_file:
            config_data = json.load(config_file)
    except (FileNotFoundError, json.JSONDecodeError):
        config_data = {"options": {"view_options": {}}}

    config_data["options"]["view_options"][option_name] = bool(value)

    with open(user_config_file, 'w') as config_file:
        json.dump(config_data, config_file, indent=4)


def create_menu():
    """
        Creates and adds the main menu to the application window.

        This function sets up the menu bar at the top of the application, adding file, edit, and other menus
        with their respective menu items and functionalities.

        Parameters:
        None

        Returns:
        None
    """
    global show_directory_view_var
    global show_file_view_var
    global show_arguments_view_var
    global show_run_view_var
    global show_timeout_view_var
    global show_interactive_view_var
    global show_filesystem_view_var

    # File menu.
    file_menu = Menu(menu)
    menu.add_cascade(label=localization_data['file'], menu=file_menu, underline=0)

    file_menu.add_command(label="New", command=new, compound='left', image=image_new, accelerator='Ctrl+N',
                          underline=0)  # command passed is here the method defined above.
    file_menu.add_command(label="Open", command=open_script, compound='left', image=image_open, accelerator='Ctrl+O',
                          underline=0)
    # TODO:
    file_menu.add_command(label="Recent files", command=open_script, compound='left', image=None, accelerator='Ctrl+O',
                          underline=0)
    # TODO:
    file_menu.add_command(label="Close", command=open_script, compound='left', image=None, accelerator='Ctrl+W',
                          underline=0)
    # TODO:
    file_menu.add_command(label="Close All", command=open_script, compound='left', image=None, accelerator='Ctrl+Shift+W',
                          underline=0)
    file_menu.add_command(label="Save", command=save_script, compound='left', image=image_save, accelerator='Ctrl+S',
                          underline=0)
    file_menu.add_command(label="Save All Files", command=save_script, compound='left', image=image_save, accelerator='Ctrl+S',
                          underline=0)
    file_menu.add_command(label="Save As...", command=save_as_new_script, accelerator='Ctrl+Shift+S', underline=1)
    file_menu.add_command(label="Save Copy...", command=save_as_new_script, accelerator=None, underline=1)
    file_menu.add_command(label="Move / Rename", command=None, accelerator=None, underline=0)
    file_menu.add_separator()
    file_menu.add_command(label="Print...", command=None, accelerator='Ctrl+P', underline=0)
    file_menu.add_separator()
    file_menu.add_command(label="Close", command=close, accelerator='Alt+F4', underline=0)

    # Edit Menu.
    edit_menu = Menu(menu)
    menu.add_cascade(label="Edit", menu=edit_menu, underline=0)

    edit_menu.add_command(label="Undo",
                          command=undo,
                          compound='left',
                          image=image_undo,
                          accelerator='Ctrl+Z',
                          underline=0
                          )
    edit_menu.add_command(label="Redo",
                          command=redo,
                          compound='left',
                          image=image_redo,
                          accelerator='Ctrl+Y',
                          underline=0
                          )

    edit_menu.add_separator()

    edit_menu.add_command(label="Cut",
                          command=cut,
                          compound='left',
                          image=image_cut,
                          accelerator='Ctrl+X',
                          underline=0
                          )
    edit_menu.add_command(label="Copy",
                          command=copy,
                          compound='left',
                          image=image_copy,
                          accelerator='Ctrl+C',
                          underline=1
                          )
    edit_menu.add_command(label="Paste",
                          command=paste,
                          compound='left',
                          image=image_paste,
                          accelerator='Ctrl+V',
                          underline=0
                          )
    edit_menu.add_command(label="Duplicate",
                          command=duplicate,
                          compound='left',
                          image=image_paste,
                          accelerator='Ctrl+D',
                          underline=0
                          )
    edit_menu.add_command(label="Select All",
                          command=duplicate,
                          compound='left',
                          image=image_duplicate,
                          accelerator='Ctrl+D',
                          underline=0
                          )
    # TODO: python specific menu sections (triggered by python dynamic menu)
    # edit_menu.add_separator()
    # edit_menu.add_command(label="Indent selected lines", command=duplicate, compound='left', accelerator='Tab')
    # edit_menu.add_command(label="Dedent selected lines", command=duplicate, compound='left', accelerator='Shift+Tab')
    # edit_menu.add_command(label="Replace tabs with spaces", command=duplicate, compound='left', accelerator='Tab')

    # TODO: comment functions
    # edit_menu.add_separator()
    # edit_menu.add_command(label="Toggle comment", command=duplicate, compound='left', accelerator='Ctrl+3')
    # edit_menu.add_command(label="Comment out", command=duplicate, compound='left', accelerator='Alt+3')
    # edit_menu.add_command(label="Uncomment", command=duplicate, compound='left', accelerator='Alt+4')
    edit_menu.add_separator()
    edit_menu.add_command(label="Go to line...", command=duplicate, compound='left', accelerator='Ctrl+G')
    edit_menu.add_separator()
    edit_menu.add_command(label="Auto-complete", command=duplicate, compound='left', accelerator='Ctrl+Space')

    find_submenu = Menu(menu, tearoff=0)
    edit_menu.add_cascade(label="Find", menu=find_submenu)
    find_submenu.add_command(label="Find", command=find_text, compound='left', image=image_find, accelerator='Ctrl+F')
    find_submenu.add_command(label="Find and Replace", command=open_search_replace_dialog, compound='left', image=image_find, accelerator='Ctrl+R')
    edit_menu.add_separator()
    edit_menu.add_command(label="Clear shell", command=duplicate, compound='left', image=image_find, accelerator='Ctrl+L')

    # edit_menu.add_command(label="Delete", command=delete, underline=0)
    #edit_menu.add_separator()
    #edit_menu.add_command(label="Select All", command=select_all, accelerator='Ctrl+A', underline=0)
    #edit_menu.add_command(label="Clear All", command=delete_all, underline=6)

    # View Menu
    view_menu = Menu(menu)
    menu.add_cascade(label="View", menu=view_menu, underline=0)

    add_view_section_to_menu("is_directory_view_visible",
                             show_directory_view_var,
                             view_menu,
                             "Directory",
                             frm,
                             toggle_directory_view_visibility)

    add_view_section_to_menu("is_file_view_visible",
                             show_file_view_var,
                             view_menu,
                             "File",
                             script_frm,
                             toggle_file_view_visibility)

    view_menu.add_separator()

    add_view_section_to_menu("is_arguments_view_visible",
                             show_arguments_view_var,
                             view_menu,
                             "Script Arguments",
                             content_frm,
                             toggle_arguments_view_visibility)

    add_view_section_to_menu("is_run_view_visible",
                             show_run_view_var,
                             view_menu,
                             "Run",
                             run_frm,
                             toggle_run_view_visibility)

    add_view_section_to_menu("is_timeout_view_visible",
                             show_timeout_view_var,
                             view_menu,
                             "Timeout",
                             line_frm,
                             toggle_timeout_view_visibility)

    add_view_section_to_menu("is_interactive_view_visible",
                             show_interactive_view_var,
                             view_menu,
                             "Interactive",
                             interactive_frm,
                             toggle_interactive_view_visibility)

    add_view_section_to_menu("is_filesystem_view_visible",
                             show_filesystem_view_var,
                             view_menu,
                             "Filesystem",
                             filesystem_frm,
                             toggle_filesystem_view_visibility)

    # Run Menu
    # run_menu = Menu(menu)
    # menu.add_cascade(label="Run", menu=run_menu, underline=0)

    # Tool Menu
    tool_menu = Menu(menu)
    menu.add_cascade(label="Tools", menu=tool_menu, underline=0)

    #tool_menu.add_command(label="Change Color", command=change_color)
    # tool_menu.add_command(label="Change Theme", command=open_change_theme_window)
    tool_menu.add_separator()
    tool_menu.add_command(label="System Shell", command=open_terminal_window, accelerator='Ctrl+T')
    tool_menu.add_command(label="Git Console", command=open_git_window, accelerator='Ctrl+Alt+G')
    tool_menu.add_command(label="Kanban", command=open_kanban_window, accelerator='Alt+K')
    #tool_menu.add_command(label="Notebook", command=open_ipynb_window, accelerator='Alt+N')
    tool_menu.add_command(label="AI Assistant", command=open_ai_assistant_window, accelerator='Alt+G')
    tool_menu.add_command(label="Generate Image", command=open_image_generation_window, accelerator='Alt+I')
    #  tool_menu.add_command(label="Generate Audio", command=open_audio_generation_window, accelerator='Alt+A')
    #  tool_menu.add_command(label="Generate Music", command=open_music_generation_window, accelerator='Alt+M')
    #tool_menu.add_command(label="BlackBox", command=lambda: open_webview('BlackBox', 'https://www.blackbox.ai/form'))
    #tool_menu.add_command(label="Web Browser", command=create_url_input_window)
    #tool_menu.add_command(label="big-AGI", command=lambda: open_webview('big-AGI', 'http://localhost:3000'))
    tool_menu.add_command(label="Open ScriptsStudio program folder...", command=about, accelerator=None)
    tool_menu.add_command(label="Open ScriptsStudio data folder...", command=about, accelerator=None)
    tool_menu.add_separator()
    tool_menu.add_command(label="Options...",
                          command=create_settings_window,
                          compound='left',
                          accelerator='Alt+S',
                          underline=0)

    # System Menu
    system_menu = Menu(menu)
    menu.add_cascade(label="System", menu=system_menu, underline=0)
    programs_submenu = Menu(menu, tearoff=0)
    system_menu.add_cascade(label="Programs", menu=programs_submenu)
    if get_operative_system() == "Windows":
        programs_submenu.add_command(label="Open Winget Window", command=open_winget_window, compound='left', accelerator=None)
    system_menu.add_command(label="PC Information", command=open_system_info_window, compound='left', accelerator=None)

    # Jobs Menu
    jobs_menu = Menu(menu)
    menu.add_cascade(label="Jobs", menu=jobs_menu, underline=0)
    jobs_menu.add_command(label="New 'at'", command=open_new_at_task_window)
    jobs_menu.add_command(label="New 'crontab'", command=open_new_crontab_task_window)
    jobs_menu.add_separator()
    get_scheduled_tasks(jobs_menu)

    help_menu = Menu(menu)
    menu.add_cascade(label="Help", menu=help_menu, underline=0)
    help_menu.add_command(label="Help contents", command=about, accelerator=None, underline=0)
    help_menu.add_separator()
    help_menu.add_command(label="Report problems", command=about, accelerator=None, underline=0)
    help_menu.add_separator()
    help_menu.add_command(label="About", command=about, accelerator='Ctrl+H', underline=0)


def get_scheduled_tasks(submenu):
    """
        Populates the 'Jobs' submenu with options based on the operating system.

        For Windows, it adds an option to view scheduled tasks. For other systems, it adds options for 'at' and 'crontab' jobs.

        Parameters:
        submenu (Menu): The submenu to which the job options will be added.

        Returns:
        None
    """
    if get_operative_system() == "Windows":
        submenu.add_command(label="Scheduled Tasks", command=open_scheduled_tasks_window)
    else:
        submenu.add_command(label="at", command=open_at_window)
        submenu.add_command(label="crontab", command=open_cron_window)


def create_submenu(parent_menu, title, entries):
    """
        Creates a submenu with specified entries under the given parent menu.

        Parameters:
        parent_menu (Menu): The parent menu to which the submenu will be added.
        title (str): The title of the submenu.
        entries (dict): A dictionary of menu item labels and their corresponding command functions.

        Returns:
        None
    """
    submenu = Menu(parent_menu, tearoff=0)
    parent_menu.add_cascade(label=title, menu=submenu)

    for label, command in entries.items():
        submenu.add_command(label=label, command=command)
