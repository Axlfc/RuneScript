from ttkbootstrap import Style
from src.localization import localization_data
from tkinter import Label, StringVar, IntVar, Frame
from tkinter import scrolledtext, Text, Entry, Menu
from tkinter import Scrollbar, HORIZONTAL
import os


def configure_app():
    width = 485
    height = int(width * (1 + 4 ** 0.5) / 2)

    # root.title("Untitled* - Script Editor")
    root.title(localization_data['scripts_editor'])
    root.geometry(f"{width}x{height}")

    # setting resizable window
    root.resizable(True, True)
    root.minsize(width, height)  # minimimum size possible

    root.grid_rowconfigure(2, weight=1)
    root.columnconfigure(0, weight=1)


new_name = ""
last_saved_content = None  # This will hold the content of the text editor after the last save or when a new file is opened.
context_menu = None
is_modified = False
markdown_render_enabled = False
add_current_main_opened_script_var = False
include_selected_text_in_command = False
original_md_content = None
render_markdown_var = None
rendered_html_content = None


file_name = ""  # Current file name.
current_font_family = "Liberation Mono"
current_font_size = 12
fontColor = '#000000'
fontBackground = '#FFFFFF'
server_options = ["lmstudio", "ollama", "openai"]

style = Style(theme="cosmo")

root = style.master

root.iconbitmap("src/views/icon.ico")

toolbar = Frame(root, pady=2)

menu = Menu(root)
root.config(menu=menu)

frm = Frame(root)
directory_label = Label(frm, text=os.getcwd(), anchor="center")

script_frm = Frame(root)
script_name_label = Label(script_frm, text="Script Name: ", anchor="center")

script_text = scrolledtext.ScrolledText(root, wrap="word", height=20, width=60, undo=True)
text = Text(wrap="word", font=(current_font_family, 12), background="white", borderwidth=0, highlightthickness=0,
            undo=True)

all_fonts = StringVar()

all_size = StringVar()

selected_agent_var = StringVar()

entry_text = StringVar()
content_frm = Frame(root)
entry_arguments_entry = Entry(content_frm, textvariable=entry_text, width=40)

generate_stdin = IntVar()
generate_stdin_err = IntVar()

interactive_frm = Frame(root)

scrollbar_frm = Frame(root)

run_frm = Frame(root)

line_frm = Frame(root)

one_time_frm = Frame(root)

daily_frm = Frame(root)

configure_app()
