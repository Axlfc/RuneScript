import os
from tkinter import messagebox, END, filedialog, Menu

from src.controllers.menu_creators import create_python_menu, create_csv_menu, create_generic_text_menu, \
    create_markdown_menu, create_javascript_menu, create_html_menu, create_css_menu, create_java_menu, create_cpp_menu, \
    create_latex_menu, create_bash_menu, create_powershell_menu
from src.controllers.parameters import write_config_parameter
from src.localization import localization_data
from src.views.tk_utils import directory_label, script_name_label, script_text, root, menu, is_modified


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

    print("OPEN FILE IS CALLED!")

    file_name = file_path
    # Update the directory label with the directory of the opened file
    directory_path = os.path.dirname(file_path)
    directory_label.config(text=f"{directory_path}")
    print("DIRECTORY LABEL:\t", directory_path)
    write_config_parameter("options.file_management.current_file_directory", directory_path)
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
        update_tree(read_config_parameter("options.file_management.current_working_directory"))


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
    # global is_modified

    title = os.path.basename(file_name) if file_name else localization_data['untitled']

    if is_modified:
        root.title(f"*{title} - {localization_data['scripts_editor']}")
    else:
        root.title(f"{title} - {localization_data['scripts_editor']}")

    script_name_label.config(text=f"{localization_data['script_name_label']}{os.path.basename(title)}")
