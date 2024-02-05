from tkinter import Label, Tk, StringVar, IntVar, Frame, Menu, Text, Entry
from tkinter import scrolledtext
import os


new_name = ""  # Used for renaming the file
context_menu = None  # Define context_menu as a global variable

# MAIN MENU METHODS

file_name = ""  # Current file name.
current_font_family = "Liberation Mono"
current_font_size = 12
fontColor = '#000000'
fontBackground = '#FFFFFF'

new_name = ""  # Used for renaming the file

is_modified = False  # Added is_modified variable
markdown_render_enabled = False
original_md_content = None
render_markdown_var = None
rendered_html_content = None


root = Tk()

toolbar = Frame(root, pady=2)

menu = Menu(root)
root.config(menu=menu)

frm = Frame(root)
directory_label = Label(frm, text=os.getcwd(), anchor="center")

script_frm = Frame(root)
script_name_label = Label(script_frm, text="Script Name: ", anchor="center")

script_text = scrolledtext.ScrolledText(root, wrap="word", height=20, width=60, undo=True)
text = Text(wrap="word", font=("Liberation Mono", 12), background="white", borderwidth=0, highlightthickness=0,
            undo=True)

all_fonts = StringVar()

all_size = StringVar()

entry_text = StringVar()
content_frm = Frame(root)
entry_arguments_entry = Entry(content_frm, textvariable=entry_text, width=40)

generate_stdin = IntVar()
generate_stdin_err = IntVar()

run_frm = Frame(root)

line_frm = Frame(root)

one_time_frm = Frame(root)

daily_frm = Frame(root)


at_window = None
crontab_window = None
