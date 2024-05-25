import json
import multiprocessing
import os
import subprocess
import threading
from tkinter import colorchooser, END, Toplevel, Label, Entry, Button, scrolledtext, IntVar, Menu, StringVar, \
    messagebox, OptionMenu, Checkbutton, Scrollbar, Canvas, Frame, VERTICAL, font, filedialog, Listbox, ttk
import webview  # pywebview

import markdown
from tkhtmlview import HTMLLabel
from tkinterhtml import HtmlFrame

from src.models.script_operations import get_operative_system
from src.views.edit_operations import cut, copy, paste, duplicate
from src.views.tk_utils import text, script_text, root, style, server_options
from src.controllers.utility_functions import make_tag
from src.views.ui_elements import Tooltip

THEME_SETTINGS_FILE = "data/theme_settings.json"


def load_themes_from_json(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data.get('themes', [])
    except FileNotFoundError:
        messagebox.showerror("Error", "Themes file not found.")
        return []
    except json.JSONDecodeError:
        messagebox.showerror("Error", "Error decoding themes file.")
        return []


def open_change_theme_window():
    themes = load_themes_from_json("data/themes.json")

    theme_window = Toplevel(root)
    theme_window.title("Change Theme")
    theme_window.geometry("300x250")

    Label(theme_window, text="Select Theme:").pack(pady=10)

    # Dropdown for theme selection
    selected_theme = StringVar()
    selected_theme.set(themes[0])  # default value
    theme_dropdown = OptionMenu(theme_window, selected_theme, *themes)
    theme_dropdown.pack()

    def apply_theme():
        chosen_theme = selected_theme.get()
        style.theme_use(chosen_theme)
        save_theme_setting(chosen_theme)  # Save the selected theme to the file

    Button(theme_window, text="Apply", command=apply_theme).pack(pady=20)


def save_theme_setting(theme_name):
    """
    Saves the given theme name to a settings file.
    """
    settings = {'theme': theme_name}
    with open(THEME_SETTINGS_FILE, 'w') as file:
        json.dump(settings, file)


def load_theme_setting():
    """
    Loads the theme name from the settings file.
    If the file does not exist, it returns the default theme.
    """
    if os.path.exists(THEME_SETTINGS_FILE):
        with open(THEME_SETTINGS_FILE, 'r') as file:
            settings = json.load(file)
            return settings.get('theme', 'superhero')  # Replace 'default' with your actual default theme
    return 'superhero'  # Replace 'default' with your actual default theme


def change_color():
    """
        Changes the text color in the application's text widget.

        This function opens a color chooser dialog, allowing the user to select a new color for the text.
        It then applies this color to the text within the text widget.

        Parameters:
        None

        Returns:
        None
    """
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
    make_tag()


def colorize_text():
    """
        Applies color to the text in the script text widget.

        This function retrieves the current content of the script text widget, deletes it, and reinserts it,
        applying the currently selected color.

        Parameters:
        None

        Returns:
        None
    """
    script_content = script_text.get("1.0", "end")
    script_text.delete("1.0", "end")
    script_text.insert("1.0", script_content)


def check(value):
    """
        Highlights all occurrences of a specified value in the script text widget.

        This function searches for the given value in the script text widget and applies a 'found' tag with a
        yellow background to each occurrence.

        Parameters:
        value (str): The string to be searched for in the text widget.

        Returns:
        None
    """
    script_text.tag_remove('found', '1.0', END)

    if value:
        script_text.tag_config('found', background='yellow')
        idx = '1.0'
        while idx:
            idx = script_text.search(value, idx, nocase=1, stopindex=END)
            if idx:
                lastidx = f"{idx}+{len(value)}c"
                script_text.tag_add('found', idx, lastidx)
                idx = lastidx


def search_and_replace(search_text, replace_text):
    """
        Replaces all occurrences of a specified search text with a replacement text in the script text widget.

        This function finds each occurrence of the search text and replaces it with the provided replacement text.

        Parameters:
        search_text (str): The text to be replaced.
        replace_text (str): The text to replace the search text.

        Returns:
        None
    """
    if search_text:
        start_index = '1.0'
        while True:
            start_index = script_text.search(search_text, start_index, nocase=1, stopindex=END)
            if not start_index:
                break
            end_index = f"{start_index}+{len(search_text)}c"
            script_text.delete(start_index, end_index)
            script_text.insert(start_index, replace_text)
            start_index = end_index


def find_text(event=None):
    """
        Opens a dialog for finding text within the script text widget.

        This function creates a new window with an entry field where the user can input a text string
        to find in the script text widget.

        Parameters:
        event (Event, optional): The event that triggered this function.

        Returns:
        None
    """
    search_toplevel = Toplevel(root)
    search_toplevel.title('Find Text')
    search_toplevel.transient(root)
    search_toplevel.resizable(False, False)
    Label(search_toplevel, text="Find All:").grid(row=0, column=0, sticky='e')
    search_entry_widget = Entry(search_toplevel, width=25)
    search_entry_widget.grid(row=0, column=1, padx=2, pady=2, sticky='we')
    search_entry_widget.focus_set()
    Button(search_toplevel,
           text="Ok",
           underline=0,
           command=lambda: check(search_entry_widget.get())).grid(row=0,
                                                                  column=2,
                                                                  sticky='e' + 'w',
                                                                  padx=2,
                                                                  pady=5
                                                                  )
    Button(search_toplevel,
           text="Cancel",
           underline=0,
           command=lambda: find_text_cancel_button(search_toplevel)).grid(row=0,
                                                                          column=4,
                                                                          sticky='e' + 'w',
                                                                          padx=2,
                                                                          pady=2
                                                                          )


# remove search tags and destroys the search box
def find_text_cancel_button(search_toplevel):
    """
        Removes search highlights and closes the search dialog.

        This function is called to close the search dialog and remove any search highlights
        from the text widget.

        Parameters:
        search_toplevel (Toplevel): The top-level widget of the search dialog.

        Returns:
        None
    """
    text.tag_remove('found', '1.0', END)
    search_toplevel.destroy()
    return "break"


def open_search_replace_dialog():
    """
        Opens a dialog for searching and replacing text within the script text widget.

        This function creates a new window with fields for inputting the search and replace texts
        and a button to execute the replacement.

        Parameters:
        None

        Returns:
        None
    """
    search_replace_toplevel = Toplevel(root)
    search_replace_toplevel.title('Search and Replace')
    search_replace_toplevel.transient(root)
    search_replace_toplevel.resizable(False, False)

    # Campo de búsqueda
    Label(search_replace_toplevel, text="Find:").grid(row=0, column=0, sticky='e')
    search_entry_widget = Entry(search_replace_toplevel, width=25)
    search_entry_widget.grid(row=0, column=1, padx=2, pady=2, sticky='we')

    # Campo de reemplazo
    Label(search_replace_toplevel, text="Replace:").grid(row=1, column=0, sticky='e')
    replace_entry_widget = Entry(search_replace_toplevel, width=25)
    replace_entry_widget.grid(row=1, column=1, padx=2, pady=2, sticky='we')

    # Botones
    Button(
        search_replace_toplevel,
        text="Replace All",
        command=lambda: search_and_replace(search_entry_widget.get(),
                                           replace_entry_widget.get())).grid(row=2,
                                                                             column=1,
                                                                             sticky='e' + 'w',
                                                                             padx=2,
                                                                             pady=5
                                                                             )


def open_ipython_terminal_window():
    print("OPEN IPYTHON TERMINAL")


def create_settings_window():
    print("CREATING SETTINGS WINDOWS")
    settings_window = Toplevel()
    settings_window.title("ScriptsEditor Settings")
    settings_window.geometry("600x400")

    default_config_file = "data/config.json"
    user_config_file = "data/user_config.json"

    # Load configuration options from user_config.json if available; otherwise, fallback to config.json
    if os.path.exists(user_config_file):
        config_file_to_use = user_config_file
    else:
        config_file_to_use = default_config_file

    try:
        with open(config_file_to_use, 'r') as config_file:
            config_data = json.load(config_file)
    except FileNotFoundError:
        messagebox.showerror("Error", f"Config file ({config_file_to_use}) not found.")
        return
    except json.JSONDecodeError:
        messagebox.showerror("Error", f"Error decoding config file ({config_file_to_use}).")
        return

    # Create a canvas widget to contain settings
    canvas = Canvas(settings_window, width=580, height=380)
    canvas.pack(side='left', fill='both', expand=True)

    # Add a scrollbar to the canvas
    scrollbar = Scrollbar(settings_window, orient='vertical', command=canvas.yview)
    scrollbar.pack(side='right', fill='y')

    # Configure the canvas to use the scrollbar
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

    # Create a frame inside the canvas to hold settings
    settings_frame = Frame(canvas)
    canvas.create_window((0, 0), window=settings_frame, anchor='nw')

    # Display settings based on config data
    setting_entries = {}

    for section, options in config_data.items():
        section_label = Label(settings_frame, text=f"{section.capitalize()} Settings", font=("Arial", 12, "bold"))
        section_label.pack(pady=10, anchor='w')

        for option_name, default_value in options.items():
            if option_name.lower() == 'last_selected_llm_server_provider':
                #  TO-DO: Here we need to link the same configs as the ai_assistant ai_server_settings so it has similar behavior and also writes the fields in the settings accordingly and is updated flawlessly.
                pass
            if option_name.lower() == 'font_family':
                print("SETTING UP FONTS!")
                # Create dropdown for font family selection
                font_families = font.families()
                default_font = default_value if default_value in font_families else 'Courier New'  # Default to Courier New if not found
                var = StringVar(value=default_font)
                font_label = Label(settings_frame, text="Font Family")
                font_label.pack(anchor='w', padx=20, pady=5)
                font_dropdown = OptionMenu(settings_frame, var, *font_families)
                font_dropdown.pack(anchor='w', padx=20)
                setting_entries[(section, option_name)] = var
            elif isinstance(default_value, bool):
                # Create checkbox for boolean options
                var = IntVar(value=default_value)
                checkbox = Checkbutton(settings_frame, text=option_name.capitalize(), variable=var)
                checkbox.pack(anchor='w', padx=20)
                setting_entries[(section, option_name)] = var
            elif isinstance(default_value, str) or isinstance(default_value, int):
                # Create entry field for string or integer options
                entry_label = Label(settings_frame, text=option_name.capitalize())
                entry_label.pack(anchor='w', padx=20, pady=5)
                entry = Entry(settings_frame)
                if user_config_file == user_config_file:  # Prefer user_config.json if available
                    entry.insert(END, str(default_value))
                else:
                    entry.insert(END, str(config_data[section][option_name]))
                entry.pack(anchor='w', padx=20)
                setting_entries[(section, option_name)] = entry
            else:
                # Handle other types (e.g., lists, nested dicts) accordingly
                pass

    def save_settings():
        # Save settings to user_config.json
        updated_config_data = {}

        for (section, option_name), widget in setting_entries.items():
            value = widget.get()

            if isinstance(value, str) and value.isdigit():
                value = int(value)

            updated_config_data.setdefault(section, {})[option_name] = value

        with open(user_config_file, 'w') as user_config:
            json.dump(updated_config_data, user_config, indent=4)

        messagebox.showinfo("Settings Saved", "Settings saved successfully!")

    def reset_settings():
        # Reset settings to defaults
        for (section, option_name), widget in setting_entries.items():
            default_value = config_data[section][option_name]

            if isinstance(widget, IntVar):
                widget.set(default_value)
            elif isinstance(widget, Entry):
                widget.delete(0, END)
                widget.insert(END, str(default_value))

        # Delete user_config.json if it exists
        if os.path.exists(user_config_file):
            os.remove(user_config_file)
            messagebox.showinfo("Reset Settings", "Settings reset to defaults. User configuration file deleted.")

        # Display updated values in the settings window
        for (section, option_name), widget in setting_entries.items():
            updated_value = config_data[section][option_name]

            if isinstance(widget, Entry):
                widget.delete(0, END)
                widget.insert(END, str(updated_value))
            elif isinstance(widget, IntVar):
                widget.set(updated_value)

    # Save button to save changes
    save_button = Button(settings_frame, text="Save Settings", command=save_settings)
    save_button.pack(pady=20)

    # Reset button to reset settings
    reset_button = Button(settings_frame, text="Reset Settings", command=reset_settings)
    reset_button.pack(pady=10)

    # Bind the scrollbar to the canvas
    canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))


def open_terminal_window():
    """
        Opens a new window functioning as a terminal within the application.

        This function creates a top-level window that simulates a terminal, allowing users to
        enter and execute commands with output displayed in the window.

        Parameters:
        None

        Returns:
        None
    """
    terminal_window = Toplevel()
    terminal_window.title("Python Terminal")
    terminal_window.geometry("600x400")

    # Create a ScrolledText widget to display terminal output
    output_text = scrolledtext.ScrolledText(terminal_window, height=20, width=80)
    output_text.pack(fill='both', expand=True)

    # Initialize a list to store command history
    command_history = []
    # Initialize a pointer to the current position in the command history
    history_pointer = [0]

    # Function to execute the command from the entry widget
    def execute_command(event=None):
        # Get the command from entry widget
        command = entry.get()
        if command.strip():
            # Add command to history and reset history pointer
            command_history.append(command)
            history_pointer[0] = len(command_history)

            try:
                # Run the command and get the output
                output = subprocess.check_output(command,
                                                 stderr=subprocess.STDOUT,
                                                 shell=True,
                                                 text=True,
                                                 cwd=os.getcwd())
                output_text.insert(END, f"{command}\n{output}\n")
            except subprocess.CalledProcessError as e:
                # If there's an error, print it to the output widget
                output_text.tag_configure("error", foreground="red")
                output_text.insert(END, f"Error: {e.output}", "error")
            # Clear the entry widget
            entry.delete(0, END)
            output_text.see(END)  # Auto-scroll to the bottom

    # Function to navigate the command history
    def navigate_history(event):
        if command_history:
            # UP arrow key pressed
            if event.keysym == 'Up':
                history_pointer[0] = max(0, history_pointer[0] - 1)
            # DOWN arrow key pressed
            elif event.keysym == 'Down':
                history_pointer[0] = min(len(command_history), history_pointer[0] + 1)
            # Get the command from history
            command = command_history[history_pointer[0]] if history_pointer[0] < len(command_history) else ''
            # Set the command to the entry widget
            entry.delete(0, END)
            entry.insert(0, command)

    # Create an Entry widget for typing commands
    entry = Entry(terminal_window, width=80)
    entry.pack(side='bottom', fill='x')
    entry.focus()
    entry.bind("<Return>", execute_command)
    # Bind the UP and DOWN arrow keys to navigate the command history
    entry.bind("<Up>", navigate_history)
    entry.bind("<Down>", navigate_history)


def read_config_parameter(parameter_name):
    """
    Read a specific parameter from user_config.json (if available) or config.json.

    Parameters:
    - parameter_name: Name of the parameter to read.

    Returns:
    - The value of the parameter if found, otherwise None.
    """
    try:
        # Try to read from user_config.json first
        with open("data/user_config.json", 'r') as user_config_file:
            user_config_data = json.load(user_config_file)
            if parameter_name in user_config_data:
                return user_config_data[parameter_name]
    except FileNotFoundError:
        pass  # No user_config.json file found, continue to read from config.json

    # Read from config.json
    with open("data/config.json", 'r') as config_file:
        config_data = json.load(config_file)
        if parameter_name in config_data:
            return config_data[parameter_name]

    # Parameter not found in both user_config.json and config.json
    return None


def write_config_parameter(parameter_name, parameter_value):
    """
    Write a parameter and its value to user_config.json, creating the file if necessary.

    Parameters:
    - parameter_name: Name of the parameter to write.
    - parameter_value: Value to assign to the parameter.

    Returns:
    - True if the parameter was successfully written, otherwise False.
    """
    user_config_file_path = "data/user_config.json"
    default_config_file_path = "data/config.json"

    # Check if user_config.json exists and is not empty
    if os.path.exists(user_config_file_path) and os.path.getsize(user_config_file_path) > 0:
        try:
            # Read existing user_config.json
            with open(user_config_file_path, 'r') as user_config_file:
                user_config_data = json.load(user_config_file)
        except Exception as e:
            print(f"Error reading user_config.json: {e}")
            return False
    else:
        # Copy data from config.json to user_config.json
        try:
            with open(default_config_file_path, 'r') as default_config_file:
                config_data = json.load(default_config_file)
                user_config_data = {"options": config_data["options"]}  # Only copy the 'options' object
        except Exception as e:
            print(f"Error copying data from config.json: {e}")
            return False

        # Write the initial user_config.json
        try:
            with open(user_config_file_path, 'w') as user_config_file:
                json.dump(user_config_data, user_config_file, indent=4)
        except Exception as e:
            print(f"Error writing user_config.json: {e}")
            return False

    # Update the specific parameter value within the options object
    if 'options' not in user_config_data:
        user_config_data['options'] = {}

    user_config_data['options'][parameter_name] = parameter_value

    # Write the updated user_config_data to user_config.json
    try:
        with open(user_config_file_path, 'w') as user_config_file:
            json.dump(user_config_data, user_config_file, indent=4)
        return True
    except Exception as e:
        print(f"Error writing user_config.json: {e}")
        return False


def open_ai_server_settings_window():
    def toggle_display(selected_server):
        # Get server details from llm_server_providers.json based on selected server
        print("SERVER DETAILS:\n", server_details)

        if selected_server in server_details:
            print("SELECTED SERVER:\t", selected_server)
            server_url_entry.delete(0, END)
            server_url_entry.insert(0, server_details[selected_server]["server_url"])

            api_key_entry.delete(0, END)
            api_key_entry.insert(0, server_details[selected_server]["api_key"])

        if selected_server == "lmstudio":
            server_url_entry.grid()
            # api_key_entry.grid()
        elif selected_server == "ollama":
            server_url_entry.grid()
            # api_key_entry.grid()
        elif selected_server == "openai":
            server_url_entry.grid()
            api_key_entry.grid()
        else:
            server_url_entry.grid_remove()
            api_key_entry.grid_remove()

    # Load server details from llm_server_providers.json
    with open("data/llm_server_providers.json", 'r') as server_file:
        server_details = json.load(server_file)

    settings_window = Toplevel()
    settings_window.title("AI Server Settings")
    settings_window.geometry("400x300")

    Label(settings_window, text="Select Server:").grid(row=0, column=0)
    selected_server = StringVar(settings_window)
    selected_server.set(read_config_parameter("options").get("last_selected_llm_server_provider", "lmstudio"))  # Set default selection

    # Dropdown menu options based on available servers in llm_server_providers.json
    server_options = list(server_details.keys())
    server_dropdown = OptionMenu(settings_window, selected_server, *server_options)
    server_dropdown.grid(row=0, column=1)

    Label(settings_window, text="Server URL:").grid(row=1, column=0)
    server_url_entry = Entry(settings_window, width=25)
    server_url_entry.grid(row=1, column=1)

    Label(settings_window, text="API Key:").grid(row=2, column=0)
    api_key_entry = Entry(settings_window, width=25)
    api_key_entry.grid(row=2, column=1)

    # Initial display based on default selection
    toggle_display(selected_server.get())

    # Callback function to handle dropdown selection changes
    def on_server_selection_change(*args):
        toggle_display(selected_server.get())

    # Bind the callback function to the dropdown selection
    selected_server.trace("w", on_server_selection_change)

    def save_ai_server_settings(server_url, api_key):
        # Save settings to user_config.json
        write_config_parameter("last_selected_llm_server_provider", selected_server.get())
        write_config_parameter("server_url", server_url)
        write_config_parameter("api_key", api_key)
        messagebox.showinfo("AI Server Settings", "Settings saved successfully!")

    Button(settings_window, text="Save", command=lambda: save_ai_server_settings(server_url_entry.get(), api_key_entry.get())).grid(row=3, column=0, columnspan=2)


def add_current_main_opened_script(include_main_script):
    global include_main_script_in_command
    include_main_script_in_command = include_main_script


def add_current_selected_text(include_selected_text):
    global include_selected_text_in_command
    include_selected_text_in_command = include_selected_text


def open_ai_assistant_window():
    """
    Opens a window for interacting with an AI assistant.

    This function creates a new window where users can input commands or queries, and the AI assistant
    processes and displays the results. It also provides options for rendering Markdown to HTML.

    Parameters:
    None

    Returns:
    None
    """
    global original_md_content, markdown_render_enabled, rendered_html_content
    original_md_content = ""
    rendered_html_content = ""
    markdown_render_enabled = False

    ai_assistant_window = Toplevel()
    ai_assistant_window.title("AI Assistant")
    ai_assistant_window.geometry("600x400")

    # Create a Menu Bar
    menu_bar = Menu(ai_assistant_window)
    ai_assistant_window.config(menu=menu_bar)

    # Create a 'Settings' Menu
    settings_menu = Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Settings", menu=settings_menu)
    menu_bar.add_command(label="AI Server Settings", command=open_ai_server_settings_window)
    # menu_bar.add_command(label="Manage Servers", command=manage_servers)
    render_markdown_var = IntVar()
    settings_menu.add_checkbutton(
        label="Toggle Markdown-to-HTML Rendering",
        onvalue=1,
        offvalue=0,
        variable=render_markdown_var,
        command=lambda: toggle_render_markdown(render_markdown_var.get())
    )

    add_current_main_opened_script_var = IntVar()
    settings_menu.add_checkbutton(
        label="Include Main Script in AI Context",
        onvalue=1,
        offvalue=0,
        variable=add_current_main_opened_script_var,
        command=lambda: add_current_main_opened_script(add_current_main_opened_script_var.get())
    )

    add_current_selected_text_var = IntVar()
    settings_menu.add_checkbutton(
        label="Include Selected Text from Script",
        onvalue=1,
        offvalue=0,
        variable=add_current_selected_text_var,
        command=lambda: add_current_selected_text(add_current_selected_text_var.get())
    )

    # --- Session List with Sessions and Documents Sections ---

    session_list_frame = Frame(ai_assistant_window)  # Frame to hold the entire session_list structure
    session_list_frame.pack(side="left", fill="y")

    # --- Sessions Section ---
    Label(session_list_frame, text="SESSIONS", font=("Helvetica", 10, "bold")).pack(fill="x")

    sessions_list = Listbox(session_list_frame)  # Scrollable list for sessions
    sessions_list.pack(fill="both", expand=True)

    # --- Visual Separator ---
    ttk.Separator(session_list_frame, orient="horizontal").pack(fill="x", pady=5)

    # --- Documents Section ---
    Label(session_list_frame, text="DOCUMENTS", font=("Helvetica", 10, "bold")).pack(fill="x")

    documents_list = Listbox(session_list_frame)  # Scrollable list for documents
    documents_list.pack(fill="both", expand=True)

    # Function to refresh the documents list
    def refresh_documents_list():
        documents_list.delete(0, END)
        for doc_path in document_paths:
            doc_name = os.path.basename(doc_path)
            documents_list.insert(END, doc_name)

    # Function to add a new document
    def add_new_document():
        file_path = filedialog.askopenfilename(
            initialdir=".",
            title="Select a PDF document",
            filetypes=(("PDF files", "*.pdf"), ("all files", "*.*"))
        )
        if file_path:
            document_paths.append(file_path)
            refresh_documents_list()

    # List to store document paths (no local copies)
    document_paths = []

    # Populate the documents_list initially (you can start with an empty list)
    refresh_documents_list()

    # Create Right-Click Context Menu for Documents List
    documents_context_menu = Menu(ai_assistant_window, tearoff=0)
    documents_context_menu.add_command(label="Add New Document", command=add_new_document)

    def show_documents_context_menu(event):
        documents_context_menu.post(event.x_root, event.y_root)

    documents_list.bind("<Button-3>", show_documents_context_menu)

    # Create the output text widget
    output_text = scrolledtext.ScrolledText(ai_assistant_window, height=20, width=80)
    output_text.pack(fill='both', expand=True)

    html_display = HTMLLabel(ai_assistant_window, html="")
    html_display.pack(side='left', fill='both', expand=False)
    html_display.pack_forget()  # Initially hide the HTML display

    entry = Entry(ai_assistant_window, width=30)
    entry.pack(side='bottom', fill='x')
    Tooltip(entry, "Input text prompt")

    status_label_var = StringVar()
    status_label = Label(ai_assistant_window, textvariable=status_label_var)
    status_label.pack(side='bottom')  # This will keep the status label at the bottom
    status_label_var.set("READY")  # Initialize the status label as "READY"

    output_text.insert(END, "> ")

    entry.focus()

    def on_md_content_change(event=None):
        global original_md_content
        original_md_content = script_text.get("1.0", END)
        if markdown_render_enabled:
            update_html_content()

    def update_html_content():
        global rendered_html_content
        rendered_html_content = markdown.markdown(original_md_content)
        html_display.set_html(rendered_html_content)

    def update_html_content_thread():
        global rendered_html_content
        rendered_html_content = markdown.markdown(original_md_content)
        html_display.set_html(rendered_html_content)

    def toggle_render_markdown(is_checked):
        global markdown_render_enabled
        markdown_render_enabled = bool(is_checked)

        if markdown_render_enabled:
            threading.Thread(target=update_html_content_thread).start()
            output_text.pack_forget()
            html_display.pack(fill='both', expand=True)
        else:
            output_text.delete("1.0", "end")
            output_text.insert("1.0", original_md_content)
            html_display.pack_forget()
            output_text.pack(fill='both', expand=True)

    def navigate_history(event):
        if command_history:
            # UP arrow key pressed
            if event.keysym == 'Up':
                history_pointer[0] = max(0, history_pointer[0] - 1)
            # DOWN arrow key pressed
            elif event.keysym == 'Down':
                history_pointer[0] = min(len(command_history), history_pointer[0] + 1)
            # Get the command from history
            command = command_history[history_pointer[0]] if history_pointer[0] < len(command_history) else ''
            # Set the command to the entry widget
            entry.delete(0, END)
            entry.insert(0, command)

    def stream_output(process):
        try:
            output_buffer = ""  # Initialize an empty buffer
            buffer_size = 2  # Set the size of the buffer to hold the last two characters

            while True:
                char = process.stdout.read(1)  # Read one character at a time
                if char:
                    global original_md_content
                    original_md_content += char

                    if markdown_render_enabled:
                        update_html_content()
                    else:
                        output_text.insert(END, char)
                        output_text.see(END)

                    # Update buffer
                    output_buffer += char
                    output_buffer = output_buffer[-buffer_size:]

                    if output_buffer == '> ':
                        break
                elif process.poll() is not None:
                    break
        except Exception as e:
            output_text.insert(END, f"Error: {e}\n")
        finally:
            on_processing_complete()

    def on_processing_complete():
        entry.config(state='normal')  # Re-enable the entry widget
        status_label_var.set("READY")  # Update label to show AI is processing

    def execute_ai_assistant_command(opened_script_var, selected_text_var, ai_command):
        global original_md_content

        if ai_command.strip():
            script_content = ""
            if selected_text_var.get():
                # Use only selected text from the main script window
                try:
                    script_content = "```\n" + script_text.get(script_text.tag_ranges("sel")[0],
                                                               script_text.tag_ranges("sel")[1]) + "```\n\n"
                except:
                    messagebox.showerror("Error", "No text selected in main script window.")
                    return
            elif opened_script_var.get():
                # Use full content of the main script window
                script_content = "```\n" + script_text.get("1.0", END) + "```\n\n"

            combined_command = f"{script_content}{ai_command}"

            # Insert the user command with a newline and a visual separator
            original_md_content += f"\n{combined_command}\n"
            original_md_content += "-" * 80 + "\n"  # A line of dashes as a separator
            output_text.insert("end", f"You: {combined_command}\n")
            output_text.insert("end", "-" * 80 + "\n")
            entry.delete(0, END)
            entry.config(state='disabled')  # Disable entry while processing
            status_label_var.set("AI is thinking...")  # Update label to show AI is processing

            ai_script_path = 'src\\models\\ai_assistant.py'
            # ai_script_path = r"C:\Users\user\Documents\git\UE5-python\Content\Python\src\text\ai_assistant.py"
            command = create_ai_command(ai_script_path, combined_command)

            process_ai_command(command)
        else:
            entry.config(state='normal')  # Re-enable the entry widget if no command is entered

    def create_ai_command(ai_script_path, user_prompt):
        if get_operative_system() != "Windows":
            return ['python3', ai_script_path, user_prompt]
        else:
            return ['python', ai_script_path, user_prompt]

    def process_ai_command(command):
        global process

        try:
            # Terminate existing subprocess if it exists
            if 'process' in globals() and process.poll() is None:
                process.terminate()

            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                       encoding='utf-8', bufsize=1)
            threading.Thread(target=stream_output, args=(process,)).start()

        except Exception as e:
            output_text.insert(END, f"Error: {e}\n")
            on_processing_complete()
        finally:
            update_html_content()

    def read_ai_command(command_name, user_prompt):
        # Path to commands.json file
        commands_file = "data/commands.json"
        try:
            # Load commands data from commands.json
            with open(commands_file, 'r') as f:
                commands_data = json.load(f)

            # Helper function to find the command in a submenu recursively
            def find_command(commands, command_name):
                for command in commands:
                    if command['name'] == command_name:
                        return command
                    if 'submenu' in command:
                        result = find_command(command['submenu'], command_name)
                        if result:
                            return result
                return None

            # Find the matching command
            matching_command = find_command(commands_data['customCommands'], command_name)

            if matching_command:
                # Extract the original prompt from the matching command
                original_prompt = matching_command.get("prompt", "")

                # Replace '{{{ input }}}' with the user-provided prompt
                formatted_prompt = original_prompt.replace("{{{ input }}}", user_prompt)

                # Return the formatted prompt
                return formatted_prompt
            else:
                return f"Command '{command_name}' not found."

        except FileNotFoundError:
            return f"Error: File '{commands_file}' not found."
        except json.JSONDecodeError:
            return f"Error: Failed to decode JSON from '{commands_file}'."

    def ai_assistant_rightclick_menu(command):
        selected_text = output_text.get("sel.first", "sel.last")
        if selected_text.strip():
            fix_user_prompt = read_ai_command(command, selected_text)
            execute_ai_assistant_command(add_current_main_opened_script_var, add_current_selected_text_var,
                                         fix_user_prompt)

    def nlp_custom():
        selected_text = output_text.get("sel.first", "sel.last")
        if selected_text.strip():
            # print(selected_text)
            print(read_ai_command("code-optimize", selected_text))
            #  TODO: Add custom command window

    def show_context_menu(event):
        # Load commands from JSON file
        commands_file = "data/commands.json"

        def load_commands():
            try:
                with open(commands_file, 'r') as f:
                    commands_data = json.load(f)
                return commands_data['customCommands']
            except (FileNotFoundError, json.JSONDecodeError) as e:
                messagebox.showerror("Error", f"Failed to load commands: {e}")
                return []

        def add_commands_to_menu(menu, commands):
            for command in commands:
                if 'submenu' in command:
                    submenu = Menu(menu, tearoff=0)
                    menu.add_cascade(label=command['name'], menu=submenu)
                    add_commands_to_menu(submenu, command['submenu'])
                else:
                    if command['name'] == "---":
                        menu.add_separator()
                    else:
                        menu.add_command(label=command['description'],
                                         command=lambda cmd=command: ai_assistant_rightclick_menu(cmd['name']))
                        if 'description' in command:
                            Tooltip(menu, command['description'])

        # Create the context menu
        context_menu = Menu(root, tearoff=0)
        # TODO: Use locales

        context_menu.add_command(label="Cut", command=cut)
        context_menu.add_command(label="Copy", command=copy)
        context_menu.add_command(label="Paste", command=paste)
        context_menu.add_command(label="Duplicate", command=duplicate)
        context_menu.add_command(label="Select All", command=duplicate)
        context_menu.add_separator()

        # Load and add custom commands from JSON
        custom_commands = load_commands()
        add_commands_to_menu(context_menu, custom_commands)

        context_menu.add_separator()
        context_menu.add_command(label="Custom AI request", command=nlp_custom)

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

    output_text.bind("<Button-3>", show_context_menu)

    output_text.bind("<<TextModified>>", on_md_content_change)
    output_text.see(END)

    entry.bind("<Return>", lambda event: execute_ai_assistant_command(
        add_current_main_opened_script_var,
        add_current_selected_text_var,
        entry.get())
               )

    entry.bind("<Up>", navigate_history)
    entry.bind("<Down>", navigate_history)

    # Initialize a list to store command history
    command_history = []
    # Initialize a pointer to the current position in the command history
    history_pointer = [0]

    ai_assistant_window.mainloop()


# Define _create_webview_process at the top level
def _create_webview_process(title, url):
    webview.create_window(title, url, width=800, height=600, text_select=True, zoomable=True)
    webview.start(private_mode=True)


def open_webview(title, url):
    webview_process = multiprocessing.Process(target=_create_webview_process, args=(title, url,))
    webview_process.start()


def open_url_in_webview(url):
    webview.create_window("My Web Browser", url, width=800, height=600, text_select=True, zoomable=True,
                          easy_drag=True, confirm_close=True, background_color="#1f1f1f")
    webview.start(private_mode=True)


def on_go_button_clicked(entry, window):
    url = entry.get()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url  # Prepend 'https://' if not present
    on_close(window)
    webview_process = multiprocessing.Process(target=open_url_in_webview, args=(url,))
    webview_process.start()


def create_url_input_window():
    # Change this to Toplevel
    window = Toplevel(root)  # Use the existing root from Tkinter
    window.title("Enter URL")

    entry = Entry(window, width=50)
    entry.insert(0, "https://duckduckgo.com")
    entry.pack(padx=10, pady=10)
    entry.focus()

    go_button = Button(window, text="Go", command=lambda: on_go_button_clicked(entry, window))
    go_button.pack(pady=5)

    window.bind('<Return>', lambda event: on_go_button_clicked(entry, window))


def on_enter(event, entry, window):
    """Event handler to trigger navigation when Enter key is pressed."""
    on_go_button_clicked(entry, window)


def on_close(window):
    # Terminate the subprocesses here if any
    # Clean up resources
    window.destroy()
