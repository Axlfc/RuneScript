import customtkinter
from tkinter.ttk import Treeview
from tkinter import ttk
from src.controllers.parameters import (
    ensure_user_config,
    load_theme_setting,
    get_scriptsstudio_directory, read_config_parameter, get_appearance_mode,
    get_theme_path)
from src.localization import load_localization

from customtkinter import CTkLabel, CTkEntry
from tkinter import StringVar, IntVar, BooleanVar, messagebox, font, Frame
from src.config.fonts import AppFonts
from customtkinter import CTkFrame, CTkTextbox
from tkinter import Menu
from src.config.fonts import AppFonts
import os


def verify_theme_integrity():
    """
    Verifies that the currently loaded theme has all necessary keys to avoid KeyErrors.
    """
    try:
        theme = customtkinter.ThemeManager.theme
        required = {
            "CTkFrame": ["fg_color", "top_fg_color", "border_color", "corner_radius", "border_width"],
            "CTkLabel": ["text_color", "corner_radius"],
            "CTkButton": ["fg_color", "hover_color", "text_color", "corner_radius", "border_width"],
            "CTkEntry": ["fg_color", "border_color", "text_color", "corner_radius", "border_width"],
            "CTkCheckBox": ["fg_color", "border_color", "text_color", "corner_radius", "border_width", "checkmark_color"],
            "CTkSwitch": ["fg_color", "progress_color", "button_color", "corner_radius", "border_width"],
            "CTkRadioButton": ["fg_color", "border_color", "text_color", "corner_radius", "border_width_checked"],
            "CTkProgressBar": ["fg_color", "progress_color", "corner_radius"],
            "CTkSlider": ["fg_color", "progress_color", "button_color", "corner_radius"],
            "CTkOptionMenu": ["fg_color", "button_color", "corner_radius"],
            "CTkComboBox": ["fg_color", "border_color", "button_color", "corner_radius"],
            "CTkScrollbar": ["fg_color", "button_color", "corner_radius"],
            "CTkTextbox": ["fg_color", "border_color", "text_color", "corner_radius"]
        }

        for widget, keys in required.items():
            if widget not in theme:
                print(f"DEBUG: Theme validation failed - Missing widget class: {widget}")
                return False
            for key in keys:
                if key not in theme[widget]:
                    print(f"DEBUG: Theme validation failed - Widget '{widget}' missing key: '{key}'")
                    return False
        return True
    except Exception as e:
        print(f"DEBUG: Theme integrity check encountered an error: {e}")
        return False


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
        # Normalize line endings to \n and remove ALL trailing newlines for comparison
        return content.replace('\r\n', '\n').replace('\r', '\n').rstrip('\n')

    def update_original_content(self, content):
        self.last_saved_content = self.normalize(content)
        self.is_modified = False

    def check_modified(self, current_content):
        normalized_current = self.normalize(current_content)
        self.is_modified = (normalized_current != self.last_saved_content)
        return self.is_modified


editor_state = EditorState()
tab_manager = None

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
print(f"DEBUG: Loading theme: {current_theme}")
theme_path = get_theme_path(current_theme)
print(f"DEBUG: Theme path: {theme_path}")

try:
    customtkinter.set_default_color_theme(theme_path)
    if not verify_theme_integrity():
        print(f"DEBUG: Theme '{current_theme}' is incomplete. Falling back to 'blue'.")
        customtkinter.set_default_color_theme("blue")
except Exception as e:
    print(f"DEBUG: Failed to load theme '{current_theme}': {e}. Falling back to 'blue'.")
    customtkinter.set_default_color_theme("blue")

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
class WidgetProxy:
    def __init__(self, initial_widget):
        self.__dict__['_widget'] = initial_widget

    def set_widget(self, widget):
        self.__dict__['_widget'] = widget

    def __getattr__(self, name):
        return getattr(self._widget, name)

    def __setattr__(self, name, value):
        if name == '_widget':
            self.__dict__['_widget'] = value
        else:
            setattr(self._widget, name, value)

    def __hash__(self):
        return hash(self._widget)

    def __eq__(self, other):
        return self._widget == other


_script_text = CTkTextbox(
    root, wrap="word", height=20, width=60, undo=True, font=my_font
)
script_text = WidgetProxy(_script_text)

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
status_bar = CTkFrame(root, height=25, corner_radius=0)
status_label = CTkLabel(status_bar, textvariable=status_label_var, font=("Segoe UI", 10))
progress_bar = customtkinter.CTkProgressBar(status_bar, width=150)
cancel_button = customtkinter.CTkButton(status_bar, text="Cancel", width=60, height=18, font=("Segoe UI", 10), fg_color="red", hover_color="#8B0000")
# Use a standard Frame for the tree container to ensure proper event propagation for ttk.Treeview
tree_frame = Frame(filesystem_frm)
tree_frame.grid(row=0, column=0, sticky="nsew")
tree = Treeview(tree_frame, columns=("fullpath"), displaycolumns=())
configure_app()

style = ttk.Style()
style.theme_use('clam')  # 'clam' theme allows for better customization of Treeview colors

def update_treeview_style():
    is_dark = customtkinter.get_appearance_mode().lower() == "dark"
    try:
        theme = customtkinter.ThemeManager.theme
        bg_color = theme["CTkFrame"]["fg_color"][1 if is_dark else 0]
        fg_color = theme["CTkLabel"]["text_color"][1 if is_dark else 0]
        selected_color = theme["CTkButton"]["fg_color"][1 if is_dark else 0]
    except:
        bg_color = "#2b2b2b" if is_dark else "white"
        fg_color = "white" if is_dark else "black"
        selected_color = "#333333" if is_dark else "#eeeeee"

    style.configure("Treeview",
                    background=bg_color,
                    foreground=fg_color,
                    fieldbackground=bg_color,
                    borderwidth=0)
    style.map("Treeview",
              background=[('selected', selected_color)],
              foreground=[('selected', fg_color)])

update_treeview_style()

# Global list of windows that should be updated when the theme changes
registered_windows = []

def register_window_for_theme(window):
    if window not in registered_windows:
        registered_windows.append(window)

def unregister_window_for_theme(window):
    if window in registered_windows:
        registered_windows.remove(window)

def apply_theme(theme_name, mode=None):
    """
    Apply theme and appearance mode to the application.
    """
    from src.controllers.parameters import get_theme_path, get_appearance_mode

    # 1. Update appearance mode (works immediately for CTk widgets)
    if mode is None:
        mode = get_appearance_mode(theme_name)
    customtkinter.set_appearance_mode(mode)

    # 2. Update color theme
    theme_path = get_theme_path(theme_name)
    try:
        customtkinter.set_default_color_theme(theme_path)
        if not verify_theme_integrity():
            print(f"DEBUG: Theme '{theme_name}' is incomplete. Falling back to 'blue'.")
            customtkinter.set_default_color_theme("blue")
    except Exception as e:
        print(f"Error setting default color theme: {e}. Falling back to 'blue'.")
        customtkinter.set_default_color_theme("blue")

    # 3. Update Treeview style (non-CTk)
    update_treeview_style()

    # 4. Refresh some critical components
    try:
        from src.views.app_layers import line_numbers
        if line_numbers and line_numbers.winfo_exists():
            line_numbers.redraw()
    except:
        pass

    # 5. Refresh tabs
    try:
        if tab_manager:
            tab_manager.refresh_tab_bar()
    except:
        pass

    # 6. Update all registered windows/widgets that might need manual refreshing
    for window in registered_windows[:]:
        try:
            if hasattr(window, "winfo_exists") and window.winfo_exists():
                # If it's a CTk widget, it might already have updated its appearance,
                # but we might need to trigger custom logic.
                if hasattr(window, "refresh_theme"):
                    window.refresh_theme()
            else:
                registered_windows.remove(window)
        except:
            registered_windows.remove(window)

    # Force a redraw of the root
    root.update()
