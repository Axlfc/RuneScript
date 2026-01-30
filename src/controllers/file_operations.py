import os
from tkinter import messagebox, END, filedialog, Menu, TclError, Frame
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
    create_powershell_menu)
from src.controllers.parameters import write_config_parameter
from src.views.tk_utils import (
    localization_data,
    directory_label,
    script_name_label,
    script_text,
    root,
    menu,
    editor_state)
from src.views.ui_elements import LineNumberCanvas

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
    from src.views.tk_utils import tab_manager
    print("file_operations.py/open_file IS CALLED!")

    # Check if already open
    if tab_manager:
        for i, tab in enumerate(tab_manager.tabs):
            if tab.file_path == file_path:
                tab_manager.switch_to_tab(i)
                return

    encodings = ["utf-8", "cp1252", "ISO-8859-1", "utf-16"]
    script_content = ""
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

    if tab_manager:
        tab_manager.add_tab(file_path, script_content, is_modified=False, original_content=script_content)
        directory_path = os.path.dirname(file_path)
        directory_label.configure(text=f"{directory_path}")
        write_config_parameter("options.file_management.current_file_directory", directory_path)
        write_config_parameter("options.file_management.last_opened_script", file_path)
        return

    # Reset internal modified flag during loading
    try:
        target_widget = getattr(script_text, "_textbox", script_text)
        target_widget.edit_modified(False)
    except Exception:
        pass

    script_text.delete("1.0", END)
    script_text.insert("1.0", script_content)

    print("SAVING FILE CONTENT HERE TO LAST_SAVED_CONTENT")
    editor_state.update_original_content(script_content)

    # Ensure the widget's internal modified flag is reset AFTER insertion
    try:
        target_widget = getattr(script_text, "_textbox", script_text)
        target_widget.edit_modified(False)
    except Exception:
        pass

    ext = os.path.splitext(file_path)[1]
    print("EXT of Opened File IS:\t", ext)
    update_menu_based_on_extension(ext, directory_path)
    update_title()

    # We need to trigger a redraw of the line numbers and adjust text position
    # root.after(10, update_line_numbers)  # Small delay to ensure text is fully loaded


def update_menu_based_on_extension(ext, directory_path):
    from src.controllers.menu_functions import _update_interpreters

    # If a Python file is opened, refresh the python submenu
    if ext == ".py":
        _update_interpreters(directory_path)
    # For any other file, remove the python submenu
    else:
        try:
            menu.delete("Python")
        except TclError:
            pass  # Ignore if menu doesn't exist

    menu_creators = {
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

    file_type_labels = {
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

    jobs_menu_index = None
    for index in range(menu.index('end') + 1):
        try:
            if menu.type(index) == "separator":
                continue
            if localization_data["jobs"] in menu.entrycget(index, 'label'):
                jobs_menu_index = index
                break
        except TclError:
            continue

    if jobs_menu_index is None:
        return

    # Delete any previous dynamic menu
    possible_labels = list(file_type_labels.values()) + ["Other"]
    for index in range(menu.index('end') + 1):
        try:
            if menu.type(index) == "separator":
                continue
            if menu.entrycget(index, 'label') in possible_labels:
                menu.delete(index)
                break
        except Exception:
            continue

    # Create new dynamic menu for non-python files
    if ext != ".py":
        dynamic_menu = Menu(menu, tearoff=0, name='dynamic')
        if ext in menu_creators:
            menu_creators[ext](dynamic_menu)
            label = file_type_labels.get(ext, "Other")
        else:
            create_generic_text_menu(dynamic_menu)
            label = "Other"
        menu.insert_cascade(jobs_menu_index + 1, label=label, menu=dynamic_menu)


def open_script(event=None):
    print("OPEN SCRIPT IS CALLED!")
    file_path = filedialog.askopenfilename(filetypes=file_types)
    if file_path:
        open_file(file_path)
        write_config_parameter("options.file_management.current_file_path", file_path)
        write_config_parameter(
            "options.file_management.current_working_directory",
            directory_label.cget("text"))

def update_title():
    print("RENAME MAIN WINDOW TRIGGERED, IS MODIFIED?", editor_state.is_modified)
    title = os.path.basename(editor_state.file_name) if editor_state.file_name else localization_data["untitled"]
    if editor_state.is_modified:
        root.title(f"*{title} - {localization_data['scripts_editor']}")
    else:
        root.title(f"{title} - {localization_data['scripts_editor']}")
    script_name_label.configure(text=f"{localization_data['script_name_label']}{title}")


def on_text_change(event=None):
    # This might be triggered by <<Modified>> event
    try:
        target_widget = getattr(script_text, "_textbox", script_text)
        # If it was a real modification according to the widget
        if not target_widget.edit_modified():
            return
    except Exception:
        pass

    print("on_text_change triggered")
    current_content = script_text.get("1.0", "end-1c")
    was_modified = editor_state.is_modified
    is_now_modified = editor_state.check_modified(current_content)

    if was_modified != is_now_modified:
        update_title()
        from src.views.tk_utils import tab_manager
        if tab_manager and tab_manager.active_tab_index != -1:
            tab = tab_manager.tabs[tab_manager.active_tab_index]
            tab.is_modified = is_now_modified
            tab_manager.refresh_tab_bar()

    # Reset the internal modified flag so we can receive the event again
    try:
        target_widget = getattr(script_text, "_textbox", script_text)
        target_widget.edit_modified(False)
    except Exception:
        pass


def prompt_save_changes():
    if editor_state.is_modified:
        response = messagebox.askyesnocancel(
            "Save Changes", "You have unsaved changes. Would you like to save them?"
        )
        if response is None:
            return False
        elif response:
            save_script()
    return True


def save():
    if not editor_state.file_name or editor_state.file_name == "Untitled":
        return save_as()
    try:
        content = script_text.get("1.0", "end-1c")
        with open(editor_state.file_name, "w", encoding="utf-8") as file:
            file.write(content)
            editor_state.update_original_content(content)
            update_title()

            from src.views.tk_utils import tab_manager
            if tab_manager and tab_manager.active_tab_index != -1:
                tab = tab_manager.tabs[tab_manager.active_tab_index]
                tab.file_path = editor_state.file_name
                tab.is_modified = False
                tab.original_content = editor_state.last_saved_content
                tab_manager.refresh_tab_bar()

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
    new_file_name = filedialog.asksaveasfilename(
        defaultextension=".*", filetypes=file_types
    )
    if not new_file_name:
        return False
    editor_state.file_name = new_file_name
    save()
    update_script_name_label(new_file_name)
    update_title()
    return True


def close():
    root.quit()


def save_file(file_name, content):
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(content)
    messagebox.showinfo("Save", "Script saved successfully!")


def save_script(event=None):
    if not editor_state.file_name or editor_state.file_name == "Untitled":
        print("Saving new script...")
        save_as_new_script()
    else:
        print("Saving existing script...")
        content = script_text.get("1.0", "end-1c")
        try:
            with open(editor_state.file_name, "w", encoding="utf-8") as file:
                file.write(content)
            editor_state.update_original_content(content)
            update_title()
            update_script_name_label(editor_state.file_name)

            from src.views.tk_utils import tab_manager
            if tab_manager and tab_manager.active_tab_index != -1:
                tab = tab_manager.tabs[tab_manager.active_tab_index]
                tab.file_path = editor_state.file_name
                tab.is_modified = False
                tab.original_content = editor_state.last_saved_content
                tab_manager.refresh_tab_bar()

            messagebox.showinfo("Save", "File saved successfully!")
        except Exception as e:
            messagebox.showerror("Save Error", f"An error occurred while saving: {e}")


def save_as_new_script(event=None):
    new_file_name = filedialog.asksaveasfilename(
        defaultextension=".*", filetypes=file_types
    )
    if not new_file_name:
        return
    editor_state.file_name = new_file_name
    save_script()


def update_script_name_label(file_path):
    base_name = os.path.basename(file_path)
    message = localization_data["file_name"] + ": " + base_name
    script_name_label.configure(text=message)


def new(event=None):
    from src.views.tk_utils import tab_manager
    if tab_manager:
        tab_manager.add_tab()
    else:
        if editor_state.is_modified:
            response = messagebox.askyesnocancel(
                localization_data["save_file"],
                localization_data["save_changes_confirmation"])
            if response:
                save()
                clear_editor()
            elif response is None:
                return
            elif not response:
                clear_editor()
        editor_state.file_name = ""
        clear_editor()


def clear_editor():
    script_text.delete("1.0", "end")
    editor_state.file_name = ""
    editor_state.update_original_content("")
    update_title()

