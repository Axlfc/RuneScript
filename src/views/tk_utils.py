import customtkinter
from tkinter.ttk import Treeview
from src.controllers.parameters import (
    ensure_user_config,
    load_theme_setting,
    get_scriptsstudio_directory, read_config_parameter,
)
from src.localization import load_localization

from customtkinter import CTkLabel, CTkEntry
from tkinter import StringVar, IntVar, BooleanVar, messagebox, font
from customtkinter import CTkFrame, CTkTextbox
from tkinter import Menu
import os


ensure_user_config()
language_selected_option = read_config_parameter("options.editor_settings.language")
localization_data = load_localization(f"data/locales/{language_selected_option}.json")


PHASE_UI_LABELS = {
    "RED": "Write Test",
    "GREEN": "Write Code",
    "REFACTOR": "Refactor"
}

UI_TO_INTERNAL_PHASE = {v: k for k, v in PHASE_UI_LABELS.items()}


def configure_app():
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
get_scriptsstudio_directory()
current_theme = load_theme_setting()
if current_theme == "cosmo":
    customtkinter.set_appearance_mode("light")
else:
    customtkinter.set_appearance_mode("dark")
root = customtkinter.CTk()
# root.iconbitmap("src/views/icon.ico")
toolbar = CTkFrame(root)

# Create a new Font object with the desired font family and size
my_font_size = read_config_parameter("options.editor_settings.font_size")
my_font_family = read_config_parameter("options.editor_settings.font_family")
my_font = font.Font(family=my_font_family, size=my_font_size)

menu = Menu(root)
root.config(menu=menu)

frm = CTkFrame(root)
directory_label = CTkLabel(frm, text=os.getcwd(), anchor="center")
script_frm = CTkFrame(root)
script_name_label = CTkLabel(script_frm, text="Script Name: ", anchor="center")
script_text = CTkTextbox(
    root, wrap="word", height=20, width=60, undo=True
)
text = CTkTextbox(
    root,
    wrap="word",
    font=my_font,
    border_width=0,
    undo=True,
)
status_label_var = StringVar()
all_fonts = StringVar()
all_size = StringVar()
local_python_var = StringVar()
selected_agent_var = "Assistant"
entry_text = StringVar()
content_frm = CTkFrame(root)
entry_arguments_entry = CTkEntry(content_frm, textvariable=entry_text, width=40)
generate_stdin = IntVar()
generate_stdin_err = IntVar()
show_directory_view_var = IntVar()
show_scheduled_tasks_view_var = IntVar()
show_file_view_var = IntVar()
show_arguments_view_var = IntVar()
show_run_view_var = IntVar()
show_timeout_view_var = IntVar()
show_interactive_view_var = IntVar()
show_filesystem_view_var = IntVar()
persistent_agent_selection_var = IntVar()
interactive_frm = CTkFrame(root)
scrollbar_frm = CTkFrame(root)
run_frm = CTkFrame(root)
line_frm = CTkFrame(root)
one_time_frm = CTkFrame(root)
daily_frm = CTkFrame(root)
filesystem_frm = CTkFrame(root)
scheduled_tasks_frm = CTkFrame(root)
tree_frame = CTkFrame(filesystem_frm)
tree_frame.grid(row=0, column=0, sticky="nsew")
tree = Treeview(tree_frame, columns=("fullpath",), displaycolumns=())
configure_app()
