import os
from tkinter import messagebox, END, filedialog, Menu

from src.controllers.menu_creators import create_python_menu, create_csv_menu, create_generic_text_menu, \
    create_markdown_menu, create_javascript_menu, create_html_menu, create_css_menu, create_java_menu, create_cpp_menu, \
    create_latex_menu, create_bash_menu, create_powershell_menu
from src.controllers.parameters import write_config_parameter
from src.localization import localization_data
from src.views.tk_utils import directory_label, script_name_label, script_text, root, menu, is_modified, file_name, last_saved_content


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


def open_file(file_path):
    """
    Opens the specified file and updates the editor with its contents.

    This function reads the content from the specified file path and updates the script editor. It tries various
    encodings to ensure correct file reading and updates the UI based on the file extension.
    """
    global is_modified, file_name, last_saved_content

    # Prompt to save changes before opening a new file
    if not prompt_save_changes():
        return  # Cancel opening the new file if user cancels the save dialog

    print("file_operations.py/open_file IS CALLED!")
    last_saved_content = ""
    file_name = file_path
    directory_path = os.path.dirname(file_path)
    directory_label.config(text=f"{directory_path}")

    # print("DIRECTORY LABEL:\t", directory_path)
    write_config_parameter("options.file_management.current_file_directory", directory_path)
    write_config_parameter("options.file_management.last_opened_script", file_name)

    script_name_label.config(text=f"{localization_data['save_changes']} in {os.path.basename(file_path)}")

    encodings = ['utf-8', 'cp1252', 'ISO-8859-1', 'utf-16']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                script_content = file.read()
                break
        except UnicodeDecodeError:
            continue
    else:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
            script_content = file.read()

    script_text.delete("1.0", END)
    script_text.insert("1.0", script_content)

    # Save the last saved content for comparison when checking modifications
    print("SAVING FILE CONTENT HERE TO LAST_SAVED_CONTENT")
    last_saved_content = script_content
    # print("THIS IS THE LAST SAVED SCRIPT CONTENT:\n", last_saved_content)

    ext = os.path.splitext(file_path)[1]
    update_menu_based_on_extension(ext)

    # Reset modification flag after loading the file
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

    print("OPEN SCRIPT IS CALLED!")
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
        write_config_parameter("options.file_management.current_file_path", file_path)
        write_config_parameter("options.file_management.current_working_directory", directory_label.cget("text"))
        # TO-DO: Refresh views
        # update_tree(read_config_parameter("options.file_management.current_working_directory"))


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


def update_title():
    """
    Updates the application window's title based on the file's modified status and the current file name.
    """
    global is_modified
    print("RENAME MAIN WINDOW TRIGGERED, IS MODIFIED?", is_modified)
    title = os.path.basename(file_name) if file_name else localization_data['untitled']

    if is_modified:
        root.title(f"*{title} - {localization_data['scripts_editor']}")
    else:
        root.title(f"{title} - {localization_data['scripts_editor']}")

    script_name_label.config(text=f"{localization_data['script_name_label']}{title}")


def on_text_change(event=None):
    """
    Updates the modified flag when text in the editor changes.
    """
    global is_modified, last_saved_content
    print("on_text_change triggered")
    current_content = script_text.get("1.0", END)

    if current_content != last_saved_content:
        print("Content has been modified.")
        if not is_modified:
            is_modified = True
            update_title()

    else:
        print("No changes detected.")
        if not is_modified:
            is_modified = False
            update_title()


def prompt_save_changes():
    """
    Prompts the user to save changes if the current file is modified.
    """
    if is_modified:
        response = messagebox.askyesnocancel("Save Changes", "You have unsaved changes. Would you like to save them?")
        if response is None:  # Cancel operation
            return False
        elif response:  # Save the file
            save_file()
    return True  # Proceed to open a new file


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
