import customtkinter
from tkinter.ttk import Treeview
from tkinter import ttk
from src.controllers.parameters import (
    ensure_user_config,
    load_theme_setting,
    get_scriptsstudio_directory, read_config_parameter, get_appearance_mode)
from src.localization import load_localization

from customtkinter import CTkLabel, CTkEntry
from tkinter import StringVar, IntVar, BooleanVar, messagebox, font, Frame
from src.config.fonts import AppFonts
from customtkinter import CTkFrame, CTkTextbox
from tkinter import Menu
from src.config.fonts import AppFonts
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


class EditorState:
    def __init__(self):
        self.file_name = ""
        self.last_saved_content = ""
        self.is_modified = False

    def normalize(self, content):
        if content is None:
            return ""
        # Remove trailing newlines for comparison
        return content.rstrip('\n')

    def update_original_content(self, content):
        self.last_saved_content = self.normalize(content)
        self.is_modified = False

    def check_modified(self, current_content):
        normalized_current = self.normalize(current_content)
        self.is_modified = (normalized_current != self.last_saved_content)
        return self.is_modified


editor_state = EditorState()

new_name = ""
context_menu = None
markdown_render_enabled = False
add_current_main_opened_script_var = False
include_selected_text_in_command = False
original_md_content = None
render_markdown_var = None
rendered_html_content = None
current_session = None
current_font_family = "Liberation Mono"
current_font_size = 12
fontColor = "#000000"
fontBackground = "#FFFFFF"
server_options = ["llama-cpp-python", "lmstudio", "ollama", "openai", "gemini"]
get_scriptsstudio_directory()
current_theme = load_theme_setting()
customtkinter.set_appearance_mode(get_appearance_mode(current_theme))
root = customtkinter.CTk()
# root.iconbitmap("src/views/icon.ico")
toolbar = CTkFrame(root)

# Create a new Font object with the desired font family and size
my_font_size = read_config_parameter("options.editor_settings.font_size")
my_font_family = read_config_parameter("options.editor_settings.font_family")
my_font = AppFonts.init_editor_font(my_font_family, my_font_size)

menu = Menu(root)
root.configure(menu=menu)

frm = CTkFrame(root)
directory_label = CTkLabel(frm, text=os.getcwd(), anchor="center")
script_frm = CTkFrame(root)
script_name_label = CTkLabel(script_frm, text="Script Name: ", anchor="center")
script_text = CTkTextbox(
    root, wrap="word", height=20, width=60, undo=True, font=my_font
)
text = CTkTextbox(
    root,
    font=('Consolas', 12),  # Formato: (nombre_fuente, tamaño_px)
    wrap='word',
    undo=True)

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
# Use a standard Frame for the tree container to ensure proper event propagation for ttk.Treeview
tree_frame = Frame(filesystem_frm)
tree_frame.grid(row=0, column=0, sticky="nsew")
tree = Treeview(tree_frame, columns=("fullpath"), displaycolumns=())
configure_app()

style = ttk.Style()
style.theme_use('clam')  # 'clam' theme allows for better customization of Treeview colors
if get_appearance_mode(current_theme) == "dark":
    style.configure("Treeview",
                    background="#2b2b2b",
                    foreground="white",
                    fieldbackground="#2b2b2b",
                    borderwidth=0)
    style.map("Treeview",
              background=[('selected', '#333333')],
              foreground=[('selected', 'white')])
else:
    style.configure("Treeview",
                    background="white",
                    foreground="black",
                    fieldbackground="white",
                    borderwidth=0)
