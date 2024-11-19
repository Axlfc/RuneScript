import json
import shutil
from tkinter.ttk import Treeview
from ttkbootstrap import Style
from src.controllers.parameters import (
    ensure_user_config,
    load_theme_setting,
    get_scriptsstudio_directory, read_config_parameter,
)
from src.localization import load_localization

from tkinter import Label, StringVar, IntVar, Frame, BooleanVar, messagebox, font
from tkinter import scrolledtext, Text, Entry, Menu
import os

ensure_user_config()
language_selected_option = read_config_parameter("options.editor_settings.language")
localization_data = load_localization(f"data/locales/{language_selected_option}.json")


def ensure_user_config():
    user_config_file = "data/user_config.json"
    default_config_file = "data/config.json"

    if not os.path.exists(user_config_file):
        if os.path.exists(default_config_file):
            shutil.copy(default_config_file, user_config_file)
        else:
            # Create a minimal default config if no default file exists
            os.makedirs(os.path.dirname(user_config_file), exist_ok=True)
            default_config = {"options": {"view_options": {}, "language_selected": "en"}}
            with open(user_config_file, "w") as file:
                json.dump(default_config, file, indent=4)


def configure_app():
    """ ""\"
    configure_app

    Args:
        None

    Returns:
        None: Description of return value.
    ""\" """
    width = 800
    height = 600
    root.title(localization_data["scripts_editor"])
    root.geometry(f"{width}x{height}")
    root.resizable(True, True)
    root.minsize(width, height)
    root.grid_rowconfigure(2, weight=1)
    root.columnconfigure(0, weight=1)


SIMILARITY_THRESHOLD = 0.8

new_name = ""
last_saved_content = None
context_menu = None
is_modified = False
markdown_render_enabled = False
add_current_main_opened_script_var = False
include_selected_text_in_command = False
original_md_content = None
render_markdown_var = None
rendered_html_content = None
current_session = None
file_name = ""
current_font_family = "Liberation Mono"
current_font_size = 12
fontColor = "#000000"
fontBackground = "#FFFFFF"
server_options = ["llama-cpp-python", "lmstudio", "ollama", "openai", "gemini"]
ensure_user_config()
get_scriptsstudio_directory()
style = Style()
current_theme = load_theme_setting()
try:
    style.theme_use(current_theme)
except Exception as e:
    messagebox.showerror(
        "Theme Error", f"The theme '{current_theme}' is not available. ({e})"
    )
    style.theme_use("cosmo")
root = style.master
root.iconbitmap("src/views/icon.ico")
toolbar = Frame(root, pady=2)

# Create a new Font object with the desired font family and size
my_font_size = read_config_parameter("options.editor_settings.font_size")
my_font_family = read_config_parameter("options.editor_settings.font_family")
my_font = font.Font(family=my_font_family, size=my_font_size)

menu = Menu(root)
root.config(menu=menu)

frm = Frame(root)
directory_label = Label(frm, text=os.getcwd(), anchor="center")
script_frm = Frame(root)
script_name_label = Label(script_frm, text="Script Name: ", anchor="center")
script_text = scrolledtext.ScrolledText(
    root, wrap="word", height=20, width=60, undo=True
)
text = Text(
    wrap="word",
    font=my_font,
    background="white",
    borderwidth=0,
    highlightthickness=0,
    undo=True,
)
status_label_var = StringVar()
all_fonts = StringVar()
all_size = StringVar()
local_python_var = BooleanVar()
local_python_var.set(True)
selected_agent_var = "Assistant"
entry_text = StringVar()
content_frm = Frame(root)
entry_arguments_entry = Entry(content_frm, textvariable=entry_text, width=40)
generate_stdin = IntVar()
generate_stdin_err = IntVar()
show_directory_view_var = IntVar()
show_file_view_var = IntVar()
show_arguments_view_var = IntVar()
show_run_view_var = IntVar()
show_timeout_view_var = IntVar()
show_interactive_view_var = IntVar()
show_filesystem_view_var = IntVar()
interactive_frm = Frame(root)
scrollbar_frm = Frame(root)
run_frm = Frame(root)
line_frm = Frame(root)
one_time_frm = Frame(root)
daily_frm = Frame(root)
filesystem_frm = Frame(root)
tree_frame = Frame(filesystem_frm)
tree_frame.grid(row=0, column=0, sticky="nsew")
tree = Treeview(tree_frame, columns=("fullpath",), displaycolumns=())
configure_app()
