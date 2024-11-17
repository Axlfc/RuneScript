import json
import os
import sys
import subprocess
import webbrowser
from tkinter import (
    Menu,
    Button,
    messagebox,
    filedialog,
    END,
    Label,
    Checkbutton,
    Entry,
    Text,
    BooleanVar,
)

from PIL import Image, ImageTk
from src.controllers.scheduled_tasks import (
    open_cron_window,
    open_at_window,
    open_scheduled_tasks_window,
    open_new_at_task_window,
    open_new_crontab_task_window,
)
from src.models.FindInFilesWindow import FindInFilesWindow
from src.models.PromptLookup import PromptLookup, setup_prompt_completion, PromptInterpreter
from src.models.SystemInfoWindow import SystemInfoWindow
from src.models.file_operations import prompt_rename_file
from src.models.script_operations import (
    get_operative_system,
    see_stdout,
    see_stderr,
    run_script,
    run_script_windows,
    run_script_with_timeout,
)
from src.views.edit_operations import undo, redo, duplicate, copy, cut, paste
from src.views.tk_utils import (
    localization_data,
    toolbar,
    menu,
    root,
    script_name_label,
    script_text,
    is_modified,
    file_name,
    last_saved_content,
    local_python_var,
    show_directory_view_var,
    show_file_view_var,
    frm,
    directory_label,
    script_frm,
    content_frm,
    entry_arguments_entry,
    generate_stdin,
    generate_stdin_err,
    show_arguments_view_var,
    show_run_view_var,
    run_frm,
    line_frm,
    show_timeout_view_var,
    show_interactive_view_var,
    interactive_frm,
    show_filesystem_view_var,
    filesystem_frm, my_font,
)
from src.controllers.tool_functions import (
    open_ai_assistant_window,
)
from src.controllers.parameters import read_config_parameter, write_config_parameter

from src.views.tree_functions import update_tree
from src.views.ui_elements import Tooltip
from src.controllers.file_operations import (
    open_file,
    open_script,
    update_title,
    file_types,
    new,
    save,
    save_script,
    save_as_new_script,
    close,
)

from src.models.AboutWindow import AboutWindow
from src.models.AudioGenerationWindow import AudioGenerationWindow
from src.models.FindInFilesWindow import FindInFilesWindow
from src.models.GitWindow import GitWindow
from src.models.HelpWindow import HelpWindow
from src.models.IPythonNotebookTerminal import IPythonNotebookTerminal
from src.models.ImageGenerationWindow import ImageGenerationWindow
from src.models.KanbanWindow import KanbanWindow
from src.models.LaTeXMarkdownEditor import LaTeXMarkdownEditor
from src.models.MnemonicsWindow import MnemonicsWindow
from src.models.PromptEnhancementWindow import PromptEnhancementWindow
from src.models.PythonTerminalWindow import PythonTerminalWindow
from src.models.CalculatorWindow import CalculatorWindow
from src.models.SearchAndReplaceWindow import SearchAndReplaceWindow
from src.models.SearchWindow import SearchWindow
from src.models.ShortcutsWindow import ShortcutsWindow
from src.models.SettingsWindow import SettingsWindow
from src.models.TerminalWindow import TerminalWindow
from src.models.TranslatorWindow import TranslatorWindow
from src.models.WingetWindow import WingetWindow


git_console_instance = None
house_icon = "🏠"
open_icon = "📂"
save_icon = "💾"
save_new_icon = "🆕"
undo_icon = "⮪"
redo_icon = "⮬"
run_icon = "▶"


config_option_to_row_mapping = {
    "is_directory_view_visible": 0,
    "is_file_view_visible": 1,
    "is_arguments_view_visible": 5,
    "is_run_view_visible": 8,
    "is_timeout_view_visible": 9,
    "is_interactive_view_visible": 4,
    "is_filesystem_view_visible": 2,
}


def init_git_console():
    global git_console_instance
    if git_console_instance is None:
        git_console_instance = "Something"


def open_current_directory(path):
    if not os.path.isdir(path):
        print(f"Error: The directory '{path}' does not exist.")
        return

    try:
        if sys.platform.startswith('darwin'):
            # macOS
            subprocess.Popen(['open', path])
        elif sys.platform.startswith('win'):
            # Windows
            os.startfile(path)
        elif sys.platform.startswith('linux'):
            # Linux (uses xdg-open)
            subprocess.Popen(['xdg-open', path])
        else:
            print(f"Unsupported OS: {sys.platform}")
    except Exception as e:
        print(f"Failed to open directory '{path}': {e}")


def report_url(event=None, url="https://github.com/Axlfc/ScriptsEditor/issues/new"):
    try:
        webbrowser.open(url)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open web browser: {e}")


def create_settings_window(event=None):
    return SettingsWindow()


def open_system_info_window(event=None):
    return SystemInfoWindow()

def open_find_in_files_window(event=None):
    return FindInFilesWindow()


def open_search_replace_window(event=None):
    return SearchAndReplaceWindow()


def open_search_window(event=None):
    return SearchWindow()


def open_help_window(event=None):
    return HelpWindow()


def open_shortcuts_window(event=None):
    return ShortcutsWindow()


def open_mnemonics_window(event=None):
    return MnemonicsWindow()


def about(event=None):
   return AboutWindow(root)


def open_winget_window(event=None):
    return WingetWindow()


def open_git_window(repo_dir=None):
    return GitWindow(repo_dir)


def open_calculator_window(event=None):
    return CalculatorWindow()


def open_kanban_window(event=None):
    return KanbanWindow()


def open_latex_markdown_editor(event=None):
    return LaTeXMarkdownEditor()


def open_ipython_notebook_window(event=None):
    return IPythonNotebookTerminal()


def open_python_terminal_window(event=None):
    return PythonTerminalWindow()


def open_terminal_window(event=None):
    return TerminalWindow()


def open_prompt_enhancement_window(event=None):
    return PromptEnhancementWindow()


def open_translator_window(event=None):
    return TranslatorWindow()


def open_audio_generation_window():
    return AudioGenerationWindow()


def open_music_generation_window():
    pass


def open_image_generation_window():
    return ImageGenerationWindow()



def open_scriptsstudio_folder(event=None):
    """
    Opens the ScriptsStudio program folder in the system's file explorer.

    Args:
        event (tkinter.Event, optional): The event object (default is None).

    Returns:
        None
    """
    scriptsstudio_dir = read_config_parameter("options.file_management.scriptsstudio_directory")
    open_current_directory(scriptsstudio_dir)

def open_scriptsstudio_data_folder(event=None):
    """
    Opens the ScriptsStudio data folder in the system's file explorer.

    Args:
        event (tkinter.Event, optional): The event object (default is None).

    Returns:
        None
    """
    scriptsstudio_data_dir = os.path.join(
        read_config_parameter("options.file_management.scriptsstudio_directory"),
        "data"
    )
    open_current_directory(scriptsstudio_data_dir)


new_button = Button(name="toolbar_b2", borderwidth=1, command=new, width=20, height=20)
photo_new = Image.open("icons/new.png")
photo_new = photo_new.resize((18, 18), Image.LANCZOS)
image_new = ImageTk.PhotoImage(photo_new)
new_button.config(image=image_new)
new_button.grid(in_=toolbar, row=0, column=0, padx=4, pady=4, sticky="w")
save_button = Button(
    name="toolbar_b1", borderwidth=1, command=save, width=20, height=20
)
photo_save = Image.open("icons/save.png")
photo_save = photo_save.resize((18, 18), Image.LANCZOS)
image_save = ImageTk.PhotoImage(photo_save)
save_button.config(image=image_save)
save_button.grid(in_=toolbar, row=0, column=1, padx=4, pady=4, sticky="w")
open_button = Button(
    name="toolbar_b3", borderwidth=1, command=open_file, width=20, height=20
)
photo_open = Image.open("icons/open.png")
photo_open = photo_open.resize((18, 18), Image.LANCZOS)
image_open = ImageTk.PhotoImage(photo_open)
open_button.config(image=image_open)
open_button.grid(in_=toolbar, row=0, column=2, padx=4, pady=4, sticky="w")
copy_button = Button(
    name="toolbar_b4", borderwidth=1, command=copy, width=20, height=20
)
photo_copy = Image.open("icons/copy.png")
photo_copy = photo_copy.resize((18, 18), Image.LANCZOS)
image_copy = ImageTk.PhotoImage(photo_copy)
copy_button.config(image=image_copy)
copy_button.grid(in_=toolbar, row=0, column=3, padx=4, pady=4, sticky="w")
cut_button = Button(name="toolbar_b5", borderwidth=1, command=cut, width=20, height=20)
photo_cut = Image.open("icons/cut.png")
photo_cut = photo_cut.resize((18, 18), Image.LANCZOS)
image_cut = ImageTk.PhotoImage(photo_cut)
cut_button.config(image=image_cut)
cut_button.grid(in_=toolbar, row=0, column=4, padx=4, pady=4, sticky="w")
paste_button = Button(
    name="toolbar_b6", borderwidth=1, command=paste, width=20, height=20
)
photo_paste = Image.open("icons/paste.png")
photo_paste = photo_paste.resize((18, 18), Image.LANCZOS)
image_paste = ImageTk.PhotoImage(photo_paste)
paste_button.config(image=image_paste)
paste_button.grid(in_=toolbar, row=0, column=5, padx=4, pady=4, sticky="w")
duplicate_button = Button(
    name="toolbar_b7", borderwidth=1, command=duplicate, width=20, height=20
)
photo_duplicate = Image.open("icons/duplicate.png")
photo_duplicate = photo_paste.resize((18, 18), Image.LANCZOS)
image_duplicate = ImageTk.PhotoImage(photo_paste)
duplicate_button.config(image=image_duplicate)
duplicate_button.grid(in_=toolbar, row=0, column=6, padx=4, pady=4, sticky="w")
redo_button = Button(
    name="toolbar_b8", borderwidth=1, command=redo, width=20, height=20
)
photo_redo = Image.open("icons/redo.png")
photo_redo = photo_redo.resize((18, 18), Image.LANCZOS)
image_redo = ImageTk.PhotoImage(photo_redo)
redo_button.config(image=image_redo)
redo_button.grid(in_=toolbar, row=0, column=7, padx=4, pady=4, sticky="w")
undo_button = Button(
    name="toolbar_b9", borderwidth=1, command=undo, width=20, height=20
)
photo_undo = Image.open("icons/undo.png")
photo_undo = photo_undo.resize((18, 18), Image.LANCZOS)
image_undo = ImageTk.PhotoImage(photo_undo)
undo_button.config(image=image_undo)
undo_button.grid(in_=toolbar, row=0, column=8, padx=4, pady=4, sticky="w")
find_button = Button(
    name="toolbar_b10", borderwidth=1, command=open_search_window, width=20, height=20
)
photo_find = Image.open("icons/find.png")
photo_find = photo_find.resize((18, 18), Image.LANCZOS)
image_find = ImageTk.PhotoImage(photo_find)
find_button.config(image=image_find)
find_button.grid(in_=toolbar, row=0, column=9, padx=4, pady=4, sticky="w")


def select_directory():
    directory = filedialog.askdirectory()
    if directory:
        os.chdir(directory)
        global current_directory
        current_directory = directory
        directory_label.config(text=f"{directory}")
        if messagebox.askyesno(
            localization_data["open_script"],
            localization_data["open_first_file_from_directory"],
        ):
            open_first_text_file(directory)
        write_config_parameter(
            "options.file_management.current_working_directory", directory
        )
        update_tree(current_directory)


def open_first_text_file(directory):
    text_files = get_text_files(directory)
    if text_files:
        file_path = os.path.join(directory, text_files[0])
        open_file(file_path)


def get_text_files(directory):
    text_files = []
    for file in os.listdir(directory):
        if file.endswith(".txt"):
            text_files.append(file)
    return text_files


def toggle_directory_view_visibility(event=None):
    global current_directory
    global directory_label
    if show_directory_view_var.get() == 1:
        write_config_parameter("options.view_options.is_directory_view_visible", "true")
        frm.grid(row=0, column=0, pady=0, sticky="ew")
        directory_button = Button(frm, text=house_icon, command=select_directory)
        directory_button.grid(column=0, row=0, sticky="w")
        Tooltip(directory_button, localization_data["choose_working_directory"])
        directory_label.grid(column=1, row=0, padx=5, sticky="ew")
        directory_label.bind(
            "<Double-1>",
            lambda event: open_current_directory(
                read_config_parameter(
                    "options.file_management.current_working_directory"
                )
            ),
        )
        Tooltip(directory_label, localization_data["current_directory"])
    else:
        write_config_parameter(
            "options.view_options.is_directory_view_visible", "false"
        )
        frm.grid_forget()


def toggle_file_view_visibility(frame):
    if show_file_view_var.get() == 1:
        write_config_parameter("options.view_options.is_file_view_visible", "true")
        frame.grid(row=1, column=0, pady=0, sticky="ew")
        frame.grid_columnconfigure(2, weight=1)
        open_button = Button(frame, text=open_icon, command=open_script)
        open_button.grid(column=0, row=0)
        Tooltip(open_button, localization_data["open_script"])
        script_name_label.grid(column=2, row=0, sticky="we", padx=5, pady=5)
        script_name_label.bind("<Double-1>", lambda event: prompt_rename_file())
        Tooltip(script_name_label, localization_data["file_name"])
        save_button = Button(frame, text=save_icon, command=save_script)
        save_button.grid(column=3, row=0, sticky="e")
        Tooltip(save_button, localization_data["save_script"])
        save_new_button = Button(frame, text=save_new_icon, command=save_as_new_script)
        save_new_button.grid(column=4, row=0, sticky="e")
        Tooltip(save_new_button, localization_data["save_as_new_script"])
        undo_button = Button(frame, text=undo_icon, command=undo)
        undo_button.grid(column=5, row=0, sticky="e")
        Tooltip(undo_button, localization_data["undo"])
        redo_button = Button(frame, text=redo_icon, command=redo)
        redo_button.grid(column=6, row=0, sticky="e")
        Tooltip(redo_button, localization_data["redo"])
    else:
        write_config_parameter("options.view_options.is_file_view_visible", "false")
        frame.grid_forget()


def toggle_interactive_view_visibility(frame):
    if show_interactive_view_var.get() == 1:
        write_config_parameter(
            "options.view_options.is_interactive_view_visible", "true"
        )
        frame.grid(row=4, column=0, pady=0, sticky="ew")

        # Initialize the prompt lookup system
        prompt_lookup = PromptLookup(prompt_folder="data/prompts")
        prompt_interpreter = PromptInterpreter(prompt_lookup)

        # Create and configure the input field
        input_field = Text(frame, height=1, font=my_font)
        input_field.grid(row=7, column=0, padx=8, pady=(0, 8), sticky="ew")

        # Set up tab completion
        setup_prompt_completion(input_field, prompt_interpreter)

        def parse_variables(text):
            """Extract variables in the format {{var_name=value}} from text."""
            import re
            var_pattern = r'\{\{(\w+)=(.*?)\}\}'
            matches = re.finditer(var_pattern, text)
            variables = {}
            remaining_text = text

            for match in matches:
                var_name = match.group(1)
                var_value = match.group(2)
                variables[var_name] = var_value
                remaining_text = remaining_text.replace(match.group(0), '')

            return variables, remaining_text.strip()

        def process_prompt_content(prompt_data, provided_vars):
            """Process prompt content with provided variables."""
            if not prompt_data:
                return None

            content = prompt_data['content']
            required_vars = {var['name']: var for var in prompt_data.get('variables', [])}

            # Validate all required variables are provided
            missing_vars = []
            for var_name, var_info in required_vars.items():
                if var_name not in provided_vars:
                    if not var_info.get('default'):
                        missing_vars.append(var_name)

            if missing_vars:
                raise ValueError(f"Missing required variables: {', '.join(missing_vars)}")

            # Process variables
            for var_name, var_info in required_vars.items():
                placeholder = f"{{{var_name}}}"
                value = str(provided_vars.get(var_name, var_info.get('default', '')))
                # Replace the placeholder both with and without curly braces
                content = content.replace(placeholder, value)  # Replace {var_name}
                content = content.replace(f"{{{value}}}", value)  # Replace {value}

            return content

        def interpret_command_string(text):
            """Interpret a string that may contain multiple commands and additional text."""
            parts = text.split()
            results = []
            additional_text = []
            i = 0

            while i < len(parts):
                part = parts[i]

                if part.startswith('/'):  # This is a command
                    try:
                        # Try to interpret as a command
                        prompt_data = prompt_interpreter.interpret_input(part)

                        if prompt_data:
                            # Look ahead for variables
                            vars_text = ""
                            next_idx = i + 1
                            while next_idx < len(parts) and '{{' in parts[next_idx]:
                                vars_text += " " + parts[next_idx]
                                next_idx += 1

                            # Parse variables
                            provided_vars, remaining_text = parse_variables(vars_text)

                            try:
                                processed_content = process_prompt_content(prompt_data, provided_vars)
                                if processed_content:
                                    results.append(processed_content)

                                # Skip past the command and its variables
                                i = next_idx

                            except ValueError as e:
                                print(f"Error processing command: {str(e)}")
                                return None
                        else:
                            additional_text.append(part)
                            i += 1
                    except Exception as e:
                        additional_text.append(part)
                        i += 1
                else:
                    # If it's not a command, add to additional text
                    additional_text.append(part)
                    i += 1

                # If we have accumulated additional text and we're either at a command or the end
                if additional_text and (i >= len(parts) or (i < len(parts) and parts[i].startswith('/'))):
                    # Add the accumulated additional text as a separate result
                    text = " ".join(additional_text).strip()
                    if text:
                        results.append(f"ADDITIONAL_TEXT:{text}")
                    additional_text = []

            return results

        def handle_input(event=None):
            text = input_field.get("1.0", "end-1c").strip()

            try:
                results = interpret_command_string(text)

                if results:
                    for result in results:
                        if result.startswith("ADDITIONAL_TEXT:"):
                            print(result[16:])  # Print just the additional text
                        else:
                            print(f"Prompt Content: {result}")
                else:
                    print(f"Regular input: {text}")

                input_field.delete("1.0", "end")
                return "break"

            except Exception as e:
                print(f"Error: {str(e)}")
                return "break"

            return None

        # Bind the Return key to handle input
        input_field.bind("<Return>", handle_input)

        frame.grid_columnconfigure(0, weight=1)
    else:
        write_config_parameter(
            "options.view_options.is_interactive_view_visible", "false"
        )
        frame.grid_forget()


def toggle_arguments_view_visibility(frame):
    if show_arguments_view_var.get() == 1:
        write_config_parameter("options.view_options.is_arguments_view_visible", "true")
        frame.grid(row=5, column=0, pady=0, sticky="ew")
        entry_arguments_label = Label(frame, text=localization_data["entry_arguments"])
        entry_arguments_label.grid(row=0, column=0, padx=5, pady=0, sticky="w")
        entry_placeholder = ""
        entry_arguments_entry.insert(0, entry_placeholder)
        entry_arguments_entry.grid(row=0, column=1, sticky="e")
        Tooltip(entry_arguments_entry, localization_data["enter_arguments"])
        generate_stdin_check = Checkbutton(
            frame, text=localization_data["stdout"], variable=generate_stdin
        )
        generate_stdin_check.grid(row=0, column=2, sticky="e")
        Tooltip(generate_stdin_check, localization_data["generate_stdout"])
        see_stderr_check = Checkbutton(
            frame, text=localization_data["stderr"], variable=generate_stdin_err
        )
        see_stderr_check.grid(row=0, column=3, padx=10, sticky="e")
        Tooltip(see_stderr_check, localization_data["generate_stderr"])
        stdout_button = Button(
            frame, text=localization_data["see_stdout"], command=see_stdout
        )
        stdout_button.grid(column=2, row=1, padx=10, sticky="e")
        Tooltip(stdout_button, localization_data["see_stdout_tooltip"])
        stderr_button = Button(
            frame, text=localization_data["see_stderr"], command=see_stderr
        )
        stderr_button.grid(column=3, row=1, padx=10, sticky="e")
        Tooltip(stderr_button, localization_data["see_stderr_tooltip"])
    else:
        write_config_parameter(
            "options.view_options.is_arguments_view_visible", "false"
        )
        frame.grid_forget()


def toggle_run_view_visibility(frame):
    """ ""\"
    ""\"
    toggle_run_view_visibility

    Args:
        frame (Any): Description of frame.

    Returns:
        None: Description of return value.
    ""\"
    ""\" """
    if show_run_view_var.get() == 1:
        write_config_parameter("options.view_options.is_run_view_visible", "true")
        if get_operative_system() != "Windows":
            frame.grid(row=8, column=0, pady=0, sticky="nsew")
            Label(frame, text=localization_data["run_inmediately"]).grid(
                row=0, column=0, sticky="e", padx=5, pady=0
            )
            run_button = Button(frame, text=run_icon, command=run_script)
            run_button.grid(row=0, column=1, sticky="e", padx=5, pady=0)
            Tooltip(run_button, localization_data["run_script"])
        else:
            frame.grid(row=8, column=0, pady=0, sticky="nsew")
            Label(frame, text=localization_data["run_inmediately"]).grid(
                row=0, column=0, sticky="e", padx=5, pady=0
            )
            run_button = Button(frame, text=run_icon, command=run_script_windows)
            run_button.grid(row=0, column=1, sticky="e", padx=5, pady=0)
            Tooltip(run_button, localization_data["run_script"])
    else:
        write_config_parameter("options.view_options.is_run_view_visible", "false")
        frame.grid_forget()


def toggle_timeout_view_visibility(frame):
    """ ""\"
    ""\"
    toggle_timeout_view_visibility

    Args:
        frame (Any): Description of frame.

    Returns:
        None: Description of return value.
    ""\"
    ""\" """
    if show_timeout_view_var.get() == 1:
        write_config_parameter("options.view_options.is_timeout_view_visible", "true")
        if get_operative_system() != "Windows":
            frame.grid(row=9, column=0, pady=0, sticky="nsew")
            Label(frame, text=localization_data["script_timeout"]).grid(
                row=0, column=0, sticky="e", padx=5, pady=0
            )
            seconds_entry = Entry(frame, width=15)
            seconds_entry.grid(column=1, row=0, padx=(10, 0))
            Tooltip(seconds_entry, localization_data["number_of_seconds"])
            run_button = Button(
                frame,
                text=run_icon,
                command=lambda: run_script_with_timeout(
                    timeout_seconds=float(seconds_entry.get())
                ),
            )
            run_button.grid(row=0, column=2, sticky="e", padx=15, pady=0)
            Tooltip(run_button, localization_data["set_duration_for_script_execution"])
        else:
            frame.grid(row=9, column=0, pady=0, sticky="nsew")
            Label(frame, text=localization_data["script_timeout"]).grid(
                row=0, column=0, sticky="e", padx=5, pady=0
            )
            seconds_entry = Entry(frame, width=15)
            seconds_entry.grid(column=1, row=0, padx=(10, 0))
            Tooltip(seconds_entry, localization_data["number_of_seconds"])
            run_button = Button(
                frame,
                text=run_icon,
                command=lambda: run_script_with_timeout(
                    timeout_seconds=float(seconds_entry.get())
                ),
            )
            run_button.grid(row=0, column=2, sticky="e", padx=15, pady=0)
            Tooltip(run_button, localization_data["set_duration_for_script_execution"])
    else:
        write_config_parameter("options.view_options.is_timeout_view_visible", "false")
        frame.grid_forget()


def toggle_filesystem_view_visibility(frame):
    if show_filesystem_view_var.get() == 1:
        frame.grid(row=2, column=2, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
    else:
        frame.grid_remove()


def toggle_view_visibility(frame, view_var, config_option, elements_setup_callback=None):
    if view_var.get() == 1:
        write_config_parameter(f"options.view_options.{config_option}", "true")
        frame.grid(row=config_option_to_row_mapping[config_option], column=0, pady=0, sticky="ew")
        if elements_setup_callback:
            elements_setup_callback()
    else:
        write_config_parameter(f"options.view_options.{config_option}", "false")
        frame.grid_forget()


def add_view_section_to_menu(
    options_parameter_name,
    view_variable,
    menu_section,
    view_section_name,
    frame,
    function
):
    is_view_visible = read_config_parameter(
        f"options.view_options.{options_parameter_name}"
    )
    if isinstance(view_variable, BooleanVar):
        view_variable.set(
            is_view_visible if isinstance(is_view_visible, bool) else True
        )
    else:
        view_variable.set(1 if is_view_visible else 0)
    menu_section.add_checkbutton(
        label=view_section_name,
        onvalue=1,
        offvalue=0,
        variable=view_variable,
        command=lambda: toggle_view(
            frame, function, options_parameter_name, view_variable
        )
    )
    toggle_view(frame, function, options_parameter_name, view_variable)


def toggle_view(frame, function, options_parameter_name, view_variable):
    """ ""\"
    ""\"
    toggle_view

    Args:
        frame (Any): Description of frame.
        function (Any): Description of function.
        options_parameter_name (Any): Description of options_parameter_name.
        view_variable (Any): Description of view_variable.

    Returns:
        None: Description of return value.
    ""\"
    ""\" """
    function(frame)
    update_config(options_parameter_name, view_variable.get())


def update_config(option_name, value):
    """ ""\"
    ""\"
    update_config

    Args:
        option_name (Any): Description of option_name.
        value (Any): Description of value.

    Returns:
        None: Description of return value.
    ""\"
    ""\" """
    user_config_file = "data/user_config.json"
    try:
        with open(user_config_file, "r") as config_file:
            config_data = json.load(config_file)
    except (FileNotFoundError, json.JSONDecodeError):
        config_data = {"options": {"view_options": {}}}
    config_data["options"]["view_options"][option_name] = bool(value)
    with open(user_config_file, "w") as config_file:
        json.dump(config_data, config_file, indent=4)


from tkinter import Menu


def create_menu():
    global show_directory_view_var
    global show_file_view_var
    global show_arguments_view_var
    global show_run_view_var
    global show_timeout_view_var
    global show_interactive_view_var
    global show_filesystem_view_var
    global menu
    # Initialize the main menu
    # menu = Menu(root)
    root.config(menu=menu)

    # ----- File Menu -----
    file_menu = Menu(menu, tearoff=0)
    menu.add_cascade(label=localization_data["file"],
                     menu=file_menu,
                     underline=0)

    # File Operations
    file_menu.add_command(
        label=localization_data["new"],
        command=new,
        compound="left",
        image=image_new,
        accelerator="Ctrl+N",
        underline=0,
    )
    root.bind('<Control-n>', new)
    file_menu.add_command(
        label=localization_data["open"],
        command=open_script,
        compound="left",
        image=image_open,
        accelerator="Ctrl+O",
        underline=0,
    )
    root.bind('<Control-o>', open_script)

    # Uncomment if "Recent Files" functionality is implemented
    # file_menu.add_command(label="Recent files", command=open_recent_files_window, compound='left', image=None, accelerator='Ctrl+Shift+O', underline=0)
    '''file_menu.add_command(
        label="Close",
        command=duplicate,  # Assuming a function to close the current file
        compound="left",
        image=None,
        accelerator="Ctrl+W",
        underline=0,
    )
    root.bind('<Control-w>', duplicate)'''
    # Uncomment if "Close All" functionality is implemented
    # file_menu.add_command(label="Close All", command=close_all_files, compound='left', image=None, accelerator='Ctrl+Shift+W', underline=0)
    file_menu.add_command(
        label=localization_data["save"],
        command=save_script,
        compound="left",
        image=image_save,
        accelerator="Ctrl+S",
        underline=0,
    )
    root.bind('<Control-s>', save_script)
    # Uncomment if "Save All Files" functionality is implemented
    # file_menu.add_command(label="Save All Files", command=save_all_scripts, compound='left', image=image_save, accelerator='Ctrl+Shift+S', underline=0)
    file_menu.add_command(
        label=localization_data["save_as"],
        command=save_as_new_script,
        accelerator="Ctrl+Shift+S",
        underline=5,  # Underline the 'A' in "Save As..."
    )
    root.bind('<Control-Shift-s>', save_as_new_script)
    file_menu.add_command(
        label=localization_data["move_rename"],
        command=prompt_rename_file,  # TODO: Test
        accelerator="F2",
        underline=0,
    )
    root.bind('<F2>', prompt_rename_file)
    '''file_menu.add_separator()
    file_menu.add_command(
        label="Print...",
        command=duplicate,  # Assuming a function to print documents
        accelerator="Ctrl+P",
        underline=0,
    )
    root.bind('<Control-p>', duplicate)'''
    file_menu.add_separator()
    file_menu.add_command(
        label=localization_data["exit"],
        command=close,
        accelerator="Alt+F4",
        underline=0,
    )

    # ----- Edit Menu -----
    edit_menu = Menu(menu, tearoff=0)
    menu.add_cascade(label=localization_data["edit"], menu=edit_menu, underline=0)

    # Edit Operations
    edit_menu.add_command(
        label=localization_data["undo"],
        command=undo,
        compound="left",
        image=image_undo,
        accelerator="Ctrl+Z",
        underline=0,
    )
    edit_menu.add_command(
        label=localization_data["redo"],
        command=redo,
        compound="left",
        image=image_redo,
        accelerator="Ctrl+Y",
        underline=0,
    )
    edit_menu.add_separator()
    edit_menu.add_command(
        label=localization_data["cut"],
        command=cut,
        compound="left",
        image=image_cut,
        accelerator="Ctrl+X",
        underline=0,
    )
    edit_menu.add_command(
        label=localization_data["copy"],
        command=copy,
        compound="left",
        image=image_copy,
        accelerator="Ctrl+C",
        underline=0,
    )
    edit_menu.add_command(
        label=localization_data["paste"],
        command=paste,
        compound="left",
        image=image_paste,
        accelerator="Ctrl+V",
        underline=0,
    )
    '''edit_menu.add_command(
        label="Duplicate",
        command=duplicate,  # Assuming a function to duplicate content
        compound='left',
        image=image_duplicate,  # Assuming an image for duplicate
        accelerator='Ctrl+D',
        underline=0,
    )
    edit_menu.add_command(
        label="Select All",
        command=duplicate,  # Assuming a function to select all content
        compound='left',
        image=image_duplicate,  # Assuming an image for select all
        accelerator='Ctrl+A',
        underline=0,
    )'''
    edit_menu.add_separator()

    # Find Submenu
    find_submenu = Menu(edit_menu, tearoff=0)
    edit_menu.add_cascade(label=localization_data["find"], menu=find_submenu)
    find_submenu.add_command(
        label=localization_data["find"],
        command=open_search_window,
        compound="left",
        image=image_find,
        accelerator="Ctrl+F"
    )
    root.bind('<Control-f>', open_search_window)
    find_submenu.add_command(
        label=localization_data["find_and_replace"],
        command=open_search_replace_window,
        compound="left",
        image=image_duplicate,  # Assuming an image for find and replace
        accelerator="Ctrl+R",
    )
    root.bind('<Control-r>', open_search_replace_window)
    find_submenu.add_command(
        label=localization_data["find_in_files"],
        command=open_find_in_files_window,
        compound="left",
        image=image_duplicate,  # Assuming an image for find in files
        accelerator="Ctrl+H",
    )
    root.bind('<Control-h>', open_find_in_files_window)

    # ----- View Menu -----
    view_menu = Menu(menu, tearoff=0)
    menu.add_cascade(label=localization_data["view"], menu=view_menu, underline=0)

    # View Controls
    add_view_section_to_menu(
        "is_directory_view_visible",
        show_directory_view_var,
        view_menu,
        localization_data["is_directory_view_visible"],
        frm,
        toggle_directory_view_visibility
    )

    add_view_section_to_menu(
        "is_file_view_visible",
        show_file_view_var,
        view_menu,
        localization_data["is_file_view_visible"],
        script_frm,
        toggle_file_view_visibility
    )
    view_menu.add_separator()
    add_view_section_to_menu(
        "is_arguments_view_visible",
        show_arguments_view_var,
        view_menu,
        localization_data["is_arguments_view_visible"],
        content_frm,
        toggle_arguments_view_visibility
    )
    add_view_section_to_menu(
        "is_run_view_visible",
        show_run_view_var,
        view_menu,
        localization_data["is_run_view_visible"],
        run_frm,
        toggle_run_view_visibility
    )
    add_view_section_to_menu(
        "is_timeout_view_visible",
        show_timeout_view_var,
        view_menu,
        localization_data["is_timeout_view_visible"],
        line_frm,
        toggle_timeout_view_visibility
    )
    add_view_section_to_menu(
        "is_interactive_view_visible",
        show_interactive_view_var,
        view_menu,
        localization_data["is_interactive_view_visible"],
        interactive_frm,
        toggle_interactive_view_visibility
    )
    add_view_section_to_menu(
        "is_filesystem_view_visible",
        show_filesystem_view_var,
        view_menu,
        localization_data["is_filesystem_view_visible"],
        filesystem_frm,
        toggle_filesystem_view_visibility
    )

    # ----- Tools Menu -----
    tool_menu = Menu(menu, tearoff=0)
    menu.add_cascade(label=localization_data["tools"], menu=tool_menu, underline=0)

    # Tools and Utilities
    tool_menu.add_command(
        label=localization_data["ai_assistant"],
        command=open_ai_assistant_window,
        accelerator="Ctrl+Alt+A",
    )
    root.bind("<Control-Alt-a>", open_ai_assistant_window)

    #TODO: Convert to GENERATE_WINDOW: Text, Images, Audio, Music, Video, 3D Models, Personalized Avatars,
    # Interactive Content, Interactive Content, Application, Web...
    '''tool_menu.add_command(
        label="Generate Audio",
        command=open_audio_generation_window,
        accelerator="Ctrl+Alt+G",
    )
    tool_menu.add_command(
            label="Generate Image",
            command=open_image_generation_window,
            accelerator="Ctrl+Alt+G",
        )'''

    tool_menu.add_command(
        label=localization_data["calculator"],
        command=open_calculator_window,
        accelerator="Ctrl+Alt+C",
    )
    root.bind("<Control-Alt-c>", open_calculator_window)

    tool_menu.add_command(
        label=localization_data["translator"],
        command=open_translator_window,
        accelerator="F3",
    )
    root.bind("<F3>", open_translator_window)

    tool_menu.add_command(
        label=localization_data["prompt_enhancement"],
        command=open_prompt_enhancement_window,
        accelerator="Ctrl+Alt+P",
    )
    root.bind("<Control-Alt-p>", open_prompt_enhancement_window)

    tool_menu.add_command(
        label=localization_data["kanban_board"],
        command=open_kanban_window,
        accelerator="Ctrl+Alt+K",
    )
    root.bind("<Control-Alt-k>", open_kanban_window)

    tool_menu.add_command(
        label=localization_data["latex_markdown_editor"],
        command=open_latex_markdown_editor,
        accelerator="Ctrl+Alt+L",
    )
    root.bind("<Control-Alt-l>", open_latex_markdown_editor)

    tool_menu.add_command(
        label=localization_data["git_console"],
        command=open_git_window,
        accelerator="Ctrl+Alt+G",
    )
    root.bind("<Control-Alt-g>", open_git_window)

    tool_menu.add_command(
        label=localization_data["system_shell"],
        command=open_terminal_window,
        accelerator="Ctrl+Alt+B",
    )
    root.bind("<Control-Alt-b>", open_terminal_window)

    tool_menu.add_command(
        label=localization_data["python_shell"],
        command=open_python_terminal_window,
        accelerator="Ctrl+Alt+Y",
    )
    root.bind("<Control-Alt-y>", open_python_terminal_window)

    tool_menu.add_command(
        label=localization_data["notebooks"],
        command=open_ipython_notebook_window,
        accelerator="Ctrl+Alt+N",
    )
    root.bind("<Control-Alt-n>", open_ipython_notebook_window)

    tool_menu.add_command(
        label=localization_data["options"],
        command=create_settings_window,
        accelerator="Ctrl+,",
    )
    root.bind("<Control-,>", create_settings_window)

    tool_menu.add_separator()
    tool_menu.add_command(
        label=localization_data["open_scripts_studio_program_folder"],
        command=open_scriptsstudio_folder,
    )
    tool_menu.add_command(
        label=localization_data["open_scripts_studio_data_folder"],
        command=open_scriptsstudio_data_folder,
    )

    # ----- System Menu -----
    system_menu = Menu(menu, tearoff=0)
    menu.add_cascade(label=localization_data["system"], menu=system_menu, underline=0)

    # System Commands
    programs_submenu = Menu(system_menu, tearoff=0)
    system_menu.add_cascade(label=localization_data["programs"], menu=programs_submenu)
    if get_operative_system() == "Windows":
        programs_submenu.add_command(
            label=localization_data["open_winget_window"],
            command=open_winget_window,
            compound="left",
            accelerator="Ctrl+Alt+W",
        )
        root.bind("<Control-Alt-w>", open_winget_window)

    system_menu.add_command(
        label=localization_data["system_info"],
        command=open_system_info_window,
        accelerator="Ctrl+Alt+I",
    )
    root.bind("<Control-Alt-i>", open_system_info_window)

    # ----- Jobs Menu -----
    jobs_menu = Menu(menu, tearoff=0)
    menu.add_cascade(label=localization_data["jobs"], menu=jobs_menu, underline=0)

    # Jobs
    jobs_menu.add_command(
        label=localization_data["new_at"],
        command=open_new_at_task_window,
        # accelerator="Ctrl+Alt+Shift+A",
    )
    # root.bind("<Control-Alt-Shift-a>", open_new_at_task_window)

    jobs_menu.add_command(
        label=localization_data["new_crontab"],
        command=open_new_crontab_task_window,
        # accelerator="Ctrl+Alt+Shift+C",
    )
    # root.bind("<Control-Alt-Shift-c>", open_new_crontab_task_window)

    jobs_menu.add_separator()
    get_scheduled_tasks(jobs_menu)

    # ----- Help Menu -----
    help_menu = Menu(menu, tearoff=0)
    menu.add_cascade(label=localization_data["help"], menu=help_menu, underline=0)

    # Help and Support
    help_menu.add_command(
        label=localization_data["help_contents"],
        command=open_help_window,
        accelerator="F1",
    )
    root.bind("<F1>", open_help_window)
    help_menu.add_command(
        label=localization_data["shortcuts"],
        command=open_shortcuts_window,
        accelerator="F4",
    )
    root.bind("<F4>", open_shortcuts_window)
    help_menu.add_command(
        label=localization_data["mnemonics"],
        command=open_mnemonics_window,
        accelerator="F10",
    )
    root.bind("<F10>", open_mnemonics_window)
    help_menu.add_separator()
    help_menu.add_command(
        label=localization_data["report_problems"],
        command=report_url,
        accelerator="F9",
    )
    root.bind("<F9>", report_url)
    help_menu.add_separator()
    help_menu.add_command(
        label=localization_data["about_scripts_editor_about"],
        command=about,
        accelerator="Ctrl+G",
    )
    root.bind("<Control-g>", about)


def get_scheduled_tasks(submenu):
    if get_operative_system() == "Windows":
        submenu.add_command(
            label="Scheduled Tasks", command=open_scheduled_tasks_window
        )
    else:
        submenu.add_command(label="at", command=open_at_window)
        submenu.add_command(label="crontab", command=open_cron_window)
