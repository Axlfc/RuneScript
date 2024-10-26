import os
from tkinter import messagebox, END, filedialog, Menu
from src.controllers.menu_creators import (
    create_python_menu,
    create_csv_menu,
    create_generic_text_menu,
    create_markdown_menu,
    create_javascript_menu,
    create_html_menu,
    create_css_menu,
    create_java_menu,
    create_cpp_menu,
    create_latex_menu,
    create_bash_menu,
    create_powershell_menu,
)
from src.controllers.parameters import write_config_parameter
from src.localization import localization_data
from src.views.tk_utils import (
    directory_label,
    script_name_label,
    script_text,
    root,
    menu,
    is_modified,
    file_name,
    last_saved_content,
)

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
    ("Dart Files", "*.dart"),
]


def open_file(file_path):
    """ ""\"
    ""\"
    Opens the specified file and updates the editor with its contents.

    This function reads the content from the specified file path and updates the script editor. It tries various
    encodings to ensure correct file reading and updates the UI based on the file extension.
    ""\"
    ""\" """
    global is_modified, file_name, last_saved_content
    if not prompt_save_changes():
        return
    print("file_operations.py/open_file IS CALLED!")
    last_saved_content = ""
    file_name = file_path
    directory_path = os.path.dirname(file_path)
    directory_label.config(text=f"{directory_path}")
    write_config_parameter(
        "options.file_management.current_file_directory", directory_path
    )
    write_config_parameter("options.file_management.last_opened_script", file_name)
    script_name_label.config(
        text=f"{localization_data['save_changes']} in {os.path.basename(file_path)}"
    )
    encodings = ["utf-8", "cp1252", "ISO-8859-1", "utf-16"]
    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as file:
                script_content = file.read()
                break
        except UnicodeDecodeError:
            continue
    else:
        with open(file_path, "r", encoding="utf-8", errors="replace") as file:
            script_content = file.read()
    script_text.delete("1.0", END)
    script_text.insert("1.0", script_content)
    print("SAVING FILE CONTENT HERE TO LAST_SAVED_CONTENT")
    last_saved_content = script_content
    ext = os.path.splitext(file_path)[1]
    update_menu_based_on_extension(ext)
    is_modified = False
    update_title()


def open_script(event=None):
    """ ""\"
    ""\"
    Opens an existing file into the script editor.

    This function displays a file dialog for the user to choose a file. Once a file is selected, it is opened
    and its contents are displayed in the script editor.

    Parameters:
    None

    Returns:
    None
    ""\"
    ""\" """
    print("OPEN SCRIPT IS CALLED!")
    if is_modified:
        response = messagebox.askyesnocancel(
            localization_data["save_changes"], localization_data["save_confirmation"]
        )
        if response:
            if not save():
                return
        elif response is None:
            return
    file_path = filedialog.askopenfilename(filetypes=file_types)
    if file_path:
        open_file(file_path)
        write_config_parameter("options.file_management.current_file_path", file_path)
        write_config_parameter(
            "options.file_management.current_working_directory",
            directory_label.cget("text"),
        )


def update_menu_based_on_extension(ext):
    """ ""\"
    ""\"
    Updates the application menu based on the file extension of the currently open file.

    Parameters:
    ext (str): The file extension of the currently open file.

    Returns:
    None
    ""\"
    ""\" """
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
        ".ps1": create_powershell_menu,
    }
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
        "": "Bash",
        ".ps1": "PowerShell",
    }
    jobs_menu_index = None
    my_index = menu.index("end") + 1
    for index in range(my_index):
        if "Jobs" in menu.entrycget(index, "label"):
            jobs_menu_index = index
            break
    if jobs_menu_index is None:
        return
    dynamic_menu_index = None
    for index in range(menu.index("end") + 1):
        try:
            if (
                menu.entrycget(index, "label") in file_type_labels.values()
                or menu.entrycget(index, "label") == "Other"
            ):
                dynamic_menu_index = index
                menu.delete(dynamic_menu_index)
                break
        except Exception as e:
            continue
    dynamic_menu = Menu(menu, tearoff=0, name="dynamic")
    if ext in menu_creators:
        menu_creators[ext](dynamic_menu)
        label = file_type_labels.get(ext, "Other")
    else:
        create_generic_text_menu(dynamic_menu)
        label = "Other"
    menu.insert_cascade(jobs_menu_index + 1, label=label, menu=dynamic_menu)


def update_title():
    """ ""\"
    ""\"
    Updates the application window's title based on the file's modified status and the current file name.
    ""\"
    ""\" """
    global is_modified
    print("RENAME MAIN WINDOW TRIGGERED, IS MODIFIED?", is_modified)
    title = os.path.basename(file_name) if file_name else localization_data["untitled"]
    if is_modified:
        root.title(f"*{title} - {localization_data['scripts_editor']}")
    else:
        root.title(f"{title} - {localization_data['scripts_editor']}")
    script_name_label.config(text=f"{localization_data['script_name_label']}{title}")


def on_text_change(event=None):
    """ ""\"
    ""\"
    Updates the modified flag when text in the editor changes.
    ""\"
    ""\" """
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
    """ ""\"
    ""\"
    Prompts the user to save changes if the current file is modified.
    ""\"
    ""\" """
    if is_modified:
        response = messagebox.askyesnocancel(
            "Save Changes", "You have unsaved changes. Would you like to save them?"
        )
        if response is None:
            return False
        elif response:
            save_file()
    return True


def save():
    """ ""\"
    ""\"
    Saves the current file. If the file doesn't have a name, calls 'save_as' function.
    ""\"
    ""\" """
    global is_modified, file_name
    if not file_name or file_name == "Untitled":
        return save_as()
    try:
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(script_text.get("1.0", "end-1c"))
            is_modified = False
            update_title()
            messagebox.showinfo("Save", "File saved successfully!")
            return True
    except Exception as e:
        messagebox.showerror("Save Error", f"An error occurred: {e}")
        return False


def save_as():
    """ ""\"
    ""\"
    save_as

    Args:
        None

    Returns:
        None: Description of return value.
    ""\"
    ""\" """
    print("ENTERING SAVE AS")
    """
        Opens a 'Save As' dialog to save the current file with a specified name.
    """
    global file_name
    global is_modified
    new_file_name = filedialog.asksaveasfilename(
        defaultextension=".*", filetypes=file_types
    )
    if not new_file_name:
        return False
    file_name = new_file_name
    save()
    update_script_name_label(new_file_name)
    update_title()
    return True


def close():
    root.quit()


def save_file(file_name, content):
    """ ""\"
    ""\"
    save_file

    Args:
        file_name (Any): Description of file_name.
        content (Any): Description of content.

    Returns:
        None: Description of return value.
    ""\"
    ""\" """
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(content)
    messagebox.showinfo("Save", "Script saved successfully!")


def save_script(event=None):
    """ ""\"
    ""\"
    Triggered when 'Save' is clicked. Saves the current file or prompts to save as new if it's a new file.
    ""\"
    ""\" """
    global file_name, is_modified
    if not file_name or file_name == "Untitled":
        print("Saving new script...")
        save_as_new_script()
    else:
        print("Saving existing script...")
        content = script_text.get("1.0", "end-1c")
        try:
            with open(file_name, "w", encoding="utf-8") as file:
                file.write(content)
            is_modified = False
            update_title()
            update_script_name_label(file_name)
            messagebox.showinfo("Save", "File saved successfully!")
        except Exception as e:
            messagebox.showerror("Save Error", f"An error occurred while saving: {e}")


def save_as_new_script(event=None):
    """ ""\"
    ""\"
    Saves the current content as a new file. Opens a file dialog for the user to choose where to save.
    ""\"
    ""\" """
    global file_name, is_modified
    new_file_name = filedialog.asksaveasfilename(
        defaultextension=".*", filetypes=file_types
    )
    if not new_file_name:
        return
    file_name = new_file_name
    save_script()


def update_script_name_label(file_path):
    """ ""\"
    ""\"
    Updates the script name label with the base name of the provided file path.
    ""\"
    ""\" """
    base_name = os.path.basename(file_path)
    script_name_label.config(text=f"File Name: {base_name}")


def new(event=None):
    global is_modified
    if is_modified:
        response = messagebox.askyesnocancel(
            localization_data["save_file"],
            localization_data["save_changes_confirmation"],
        )
        if response:
            save()
            clear_editor()
        elif response is None:
            return
        elif not response:
            clear_editor()
    file_name = ""
    clear_editor()


def clear_editor():
    """ ""\"
    ""\"
    Clears the text editor and resets the title and modified flag.
    ""\"
    ""\" """
    global file_name
    global is_modified
    script_text.delete("1.0", "end")
    file_name = ""
    is_modified = False
    update_title()
