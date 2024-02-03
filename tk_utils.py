from tkinter import Toplevel, Label, Button, Tk, StringVar, IntVar, Frame, Menu, Text, Entry, Listbox, Scrollbar
from tkinter import END, INSERT, SEL_FIRST, SEL_LAST, SEL
from tkinter import ttk, scrolledtext, filedialog, simpledialog
import tkinter.messagebox as messagebox
import tkinter.colorchooser as colorchooser
from PIL import Image, ImageTk  # sudo apt-get install python3-pil python3-pil.imagetk
import tkinter
from crontab import CronTab  # pip install python-crontab
from winTaskScheduler import list_tasks, delete_task, at_function, crontab_function # Import the list_tasks function
from tkhtmlview import HTMLLabel  # Import HTMLLabel from tkhtmlview
import subprocess
import tempfile
import time
from time import sleep
import threading
import markdown
import queue
import os
import re

context_menu = None  # Define context_menu as a global variable

# MAIN MENU METHODS

file_name = ""  # Current file name.
current_font_family = "Liberation Mono"
current_font_size = 12
fontColor = '#000000'
fontBackground = '#FFFFFF'

new_name = ""  # Used for renaming the file

is_modified = False  # Added is_modified variable

file_types = [
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
        ("All Files", "*.*")
    ]

original_md_content = None
markdown_render_enabled = False
render_markdown_var = None


def make_tag():
    current_tags = text.tag_names()
    if "bold" in current_tags:
        weight = "bold"
    else:
        weight = "normal"

    if "italic" in current_tags:
        slant = "italic"
    else:
        slant = "roman"

    if "underline" in current_tags:
        underline = 1
    else:
        underline = 0

    if "overstrike" in current_tags:
        overstrike = 1
    else:
        overstrike = 0

    big_font = tkinter.font.Font(text, text.cget("font"))
    big_font.configure(slant=slant, weight=weight, underline=underline, overstrike=overstrike,
                       family=current_font_family, size=current_font_size)
    text.tag_config("BigTag", font=big_font, foreground=fontColor, background=fontBackground)
    if "BigTag" in current_tags:
        text.tag_remove("BigTag", 1.0, END)
    text.tag_add("BigTag", 1.0, END)


def new(event=None):
    global file_name

    ans = messagebox.askquestion(title="Save File", message="Would you like to save this file?")
    if ans == "yes":
        save()

    file_name = ""
    script_text.delete('1.0', 'end')
    root.title("*New file - Script Editor")


def open_file(file_path):
    global file_name, script_text
    file_name = file_path
    script_name_label.config(text=f"{os.path.basename(file_path)}")

    # Try opening the file with different encodings
    encodings = ['utf-8', 'cp1252', 'ISO-8859-1', 'utf-16']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                script_content = file.read()
                break
        except UnicodeDecodeError:
            pass
    else:
        # If all encodings fail, use 'utf-8' with 'replace' option
        with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
            script_content = file.read()

    script_text.delete("1.0", END)
    script_text.insert("1.0", script_content)

    # Update dynamic menu and title based on file extension
    ext = os.path.splitext(file_path)[1]
    update_menu_based_on_extension(ext)
    update_title_with_filename(file_path)


def open_script():
    file_path = filedialog.askopenfilename(filetypes=file_types)
    if file_path:
        global file_extension
        file_extension = os.path.splitext(file_path)[1]
        print("Opening file with extension:", file_extension)
        open_file(file_path)
    set_modified_status(False)  # Reset the modification status



'''def save(event=None):
    global file_name
    if file_name == "":
        path = filedialog.asksaveasfilename()
        file_name = path
    root.title(file_name + " - Script Editor")
    write = open(file_name, mode='w')
    write.write(text.get("1.0", END))'''


def save():
    global file_name

    if file_name:
        # Save the file
        with open(file_name, 'w') as file:
            file.write(script_text.get('1.0', 'end-1c'))

        # Update the window title
        root.title(file_name + " - Script Editor")
    else:
        save_as()

    # Remove the asterisk from the title
    root.title(root.title().replace('*', ''))


def update_modification_status(event):
    set_modified_status(True)


def on_text_change(event=None):
    global is_modified

    if not is_modified:
        is_modified = True
        root.title("*" + root.title())


'''def save_as(event=None):
    if file_name == "":
        save()
        return "break"
    f = filedialog.asksaveasfile(mode='w')
    if f is None:
        return
    text2save = str(text.get(1.0, END))
    f.write(text2save)
    f.close()'''


def save_as():
    global file_name

    new_file_name = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
    if new_file_name:
        file_name = new_file_name
        save()
    else:
        messagebox.showinfo("Info", "File saving canceled.")


new_name = ""  # Used for renaming the file


def rename(event=None):
    global file_name
    if file_name == "":
        # Prompt the user to enter the file path or select a file using a file dialog
        file_path = simpledialog.askstring("Rename", "Enter file path or select a file")
        if not file_path:
            # User cancelled the operation
            return

        print("File path:", file_path)
        if not os.path.exists(file_path):
            messagebox.showerror("Error", "File does not exist")
            return

        file_name = file_path

    # Extract the directory path and file name
    dir_path, old_name = os.path.split(file_name)
    new_name = simpledialog.askstring("Rename", "Enter new name")

    try:
        # Rename the file
        new_path = os.path.join(dir_path, new_name)
        os.rename(file_name, new_path)
        file_name = new_path
        root.title(file_name + " - Script Editor")
    except OSError as e:
        messagebox.showerror("Error", f"Failed to rename file: {e}")


def close(event=None):
    save()
    root.quit()


# EDIT MENU METHODS

def cut(event=None):
    # first clear the previous text on the clipboard.
    root.clipboard_clear()
    text.clipboard_append(string=text.selection_get())
    # index of the first and yhe last letter of our selection.
    text.delete(index1=SEL_FIRST, index2=SEL_LAST)


def copy(event=None):
    # first clear the previous text on the clipboard.
    print(text.index(SEL_FIRST))
    print(text.index(SEL_LAST))
    root.clipboard_clear()
    text.clipboard_append(string=text.selection_get())


def paste(event=None):
    # get gives everyting from the clipboard and paste it on the current cursor position
    # it does'nt removes it from the clipboard.
    text.insert(INSERT, root.clipboard_get())


def select_all(event=None):
    text.tag_add(SEL, "1.0", END)


def delete_all():
    text.delete(1.0, END)


def duplicate(event=None):
    selected_text = text.get("sel.first", "sel.last")
    text.insert("insert", selected_text)


def undo():
    script_text.edit_undo()


def redo():
    script_text.edit_redo()


def show_context_menu(event):
    try:
        context_menu.tk_popup(event.x_root, event.y_root)
    finally:
        context_menu.grab_release()


def delete():
    text.delete(index1=SEL_FIRST, index2=SEL_LAST)


# TOOLS MENU METHODS

def change_color():
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


# Adding Search Functionality

def check(value):
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


def open_search_replace_dialog():
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
    Button(search_replace_toplevel, text="Replace All", command=lambda: search_and_replace(search_entry_widget.get(), replace_entry_widget.get())).grid(row=2, column=1, sticky='e' + 'w', padx=2, pady=5)


# implementation of search dialog box - calling the check method to search and find_text_cancel_button to close it
def find_text(event=None):
    search_toplevel = Toplevel(root)
    search_toplevel.title('Find Text')
    search_toplevel.transient(root)
    search_toplevel.resizable(False, False)
    Label(search_toplevel, text="Find All:").grid(row=0, column=0, sticky='e')
    search_entry_widget = Entry(search_toplevel, width=25)
    search_entry_widget.grid(row=0, column=1, padx=2, pady=2, sticky='we')
    search_entry_widget.focus_set()
    Button(search_toplevel, text="Ok", underline=0, command=lambda: check(search_entry_widget.get())).grid(row=0,
                                                                                                           column=2,
                                                                                                           sticky='e' + 'w',
                                                                                                           padx=2,
                                                                                                           pady=5)
    Button(search_toplevel, text="Cancel", underline=0, command=lambda: find_text_cancel_button(search_toplevel)).grid(
        row=0, column=4, sticky='e' + 'w', padx=2, pady=2)


# remove search tags and destroys the search box
def find_text_cancel_button(search_toplevel):
    text.tag_remove('found', '1.0', END)
    search_toplevel.destroy()
    return "break"


# FORMAT BAR METHODS

def bold(event=None):
    current_tags = text.tag_names()
    if "bold" in current_tags:
        # first char is bold, so unbold the range
        text.tag_delete("bold", 1.0, END)
    else:
        # first char is normal, so bold the whole selection
        text.tag_add("bold", 1.0, END)
    make_tag()


def italic(event=None):
    current_tags = text.tag_names()
    if "italic" in current_tags:
        text.tag_add("roman", 1.0, END)
        text.tag_delete("italic", 1.0, END)
    else:
        text.tag_add("italic", 1.0, END)
    make_tag()


def underline(event=None):
    current_tags = text.tag_names()
    if "underline" in current_tags:
        text.tag_delete("underline", 1.0, END)
    else:
        text.tag_add("underline", 1.0, END)
    make_tag()


def strike():
    current_tags = text.tag_names()
    if "overstrike" in current_tags:
        text.tag_delete("overstrike", "1.0", END)

    else:
        text.tag_add("overstrike", 1.0, END)

    make_tag()


def highlight():
    color = colorchooser.askcolor(initialcolor='white')
    color_rgb = color[1]
    global fontBackground
    fontBackground = color_rgb
    current_tags = text.tag_names()
    if "background_color_change" in current_tags:
        text.tag_delete("background_color_change", "1.0", END)
    else:
        text.tag_add("background_color_change", "1.0", END)
    make_tag()


# To make align functions work properly
def remove_align_tags():
    all_tags = text.tag_names(index=None)
    if "center" in all_tags:
        text.tag_remove("center", "1.0", END)
    if "left" in all_tags:
        text.tag_remove("left", "1.0", END)
    if "right" in all_tags:
        text.tag_remove("right", "1.0", END)


# align_center
def align_center(event=None):
    remove_align_tags()
    text.tag_configure("center", justify='center')
    text.tag_add("center", 1.0, "end")


# align_justify
def align_justify():
    remove_align_tags()


# align_left
def align_left(event=None):
    remove_align_tags()
    text.tag_configure("left", justify='left')
    text.tag_add("left", 1.0, "end")


# align_right
def align_right(event=None):
    remove_align_tags()
    text.tag_configure("right", justify='right')
    text.tag_add("right", 1.0, "end")


# Font and size change functions - BINDED WITH THE COMBOBOX SELECTION
# change font and size are methods binded with combobox, calling fontit and sizeit
# called when <<combobox>> event is called

def change_font(event):
    f = all_fonts.get()
    global current_font_family
    current_font_family = f
    make_tag()


def change_size(event):
    sz = int(all_size.get())
    global current_font_size
    current_font_size = sz
    make_tag()


house_icon = "🏠"
open_icon = "📂"
save_icon = "💾"
save_new_icon = "🆕"
undo_icon = "⮪"
redo_icon = "⮬"
run_icon = "▶"

root = Tk()

# TOOLBAR
toolbar = Frame(root, pady=2)

# MENUBAR CREATION

menu = Menu(root)
root.config(menu=menu)

frm = ttk.Frame(root, padding=0)
directory_label = Label(frm, text=os.getcwd(), anchor="center")

script_frm = ttk.Frame(root, padding=0)
script_name_label = Label(script_frm, text="Script Name: ", anchor="center")

script_text = scrolledtext.ScrolledText(root, wrap="word", height=20, width=60, undo=True)
text = Text(wrap="word", font=("Liberation Mono", 12), background="white", borderwidth=0, highlightthickness=0,
            undo=True)

all_fonts = StringVar()

all_size = StringVar()

entry_text = StringVar()
content_frm = ttk.Frame(root, padding=0)
entry_arguments_entry = ttk.Entry(content_frm, textvariable=entry_text, width=40)

generate_stdin = IntVar()
generate_stdin_err = IntVar()

run_frm = ttk.Frame(root, padding=0)

line_frm = ttk.Frame(root, padding=0)

one_time_frm = ttk.Frame(root, padding=0)

daily_frm = ttk.Frame(root, padding=0)


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event):
        self.tooltip = Toplevel()
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = Label(self.tooltip, text=self.text, background="#ffffe0", relief="solid", borderwidth=1)
        label.pack()

    def leave(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


# TOOLBAR BUTTONS
# new
new_button = Button(name="toolbar_b2", borderwidth=1, command=new, width=20, height=20)
photo_new = Image.open("icons/new.png")
photo_new = photo_new.resize((18, 18), Image.LANCZOS)
image_new = ImageTk.PhotoImage(photo_new)
new_button.config(image=image_new)
new_button.pack(in_=toolbar, side="left", padx=4, pady=4)

# save
save_button = Button(name="toolbar_b1", borderwidth=1, command=save, width=20, height=20)
photo_save = Image.open("icons/save.png")
photo_save = photo_save.resize((18, 18), Image.LANCZOS)
image_save = ImageTk.PhotoImage(photo_save)
save_button.config(image=image_save)
save_button.pack(in_=toolbar, side="left", padx=4, pady=4)

# open
open_button = Button(name="toolbar_b3", borderwidth=1, command=open_file, width=20, height=20)
photo_open = Image.open("icons/open.png")
photo_open = photo_open.resize((18, 18), Image.LANCZOS)
image_open = ImageTk.PhotoImage(photo_open)
open_button.config(image=image_open)
open_button.pack(in_=toolbar, side="left", padx=4, pady=4)

# copy
copy_button = Button(name="toolbar_b4", borderwidth=1, command=copy, width=20, height=20)
photo_copy = Image.open("icons/copy.png")
photo_copy = photo_copy.resize((18, 18), Image.LANCZOS)
image_copy = ImageTk.PhotoImage(photo_copy)
copy_button.config(image=image_copy)
copy_button.pack(in_=toolbar, side="left", padx=4, pady=4)

# cut
cut_button = Button(name="toolbar_b5", borderwidth=1, command=cut, width=20, height=20)
photo_cut = Image.open("icons/cut.png")
photo_cut = photo_cut.resize((18, 18), Image.LANCZOS)
image_cut = ImageTk.PhotoImage(photo_cut)
cut_button.config(image=image_cut)
cut_button.pack(in_=toolbar, side="left", padx=4, pady=4)

# paste
paste_button = Button(name="toolbar_b6", borderwidth=1, command=paste, width=20, height=20)
photo_paste = Image.open("icons/paste.png")
photo_paste = photo_paste.resize((18, 18), Image.LANCZOS)
image_paste = ImageTk.PhotoImage(photo_paste)
paste_button.config(image=image_paste)
paste_button.pack(in_=toolbar, side="left", padx=4, pady=4)

# duplicate
duplicate_button = Button(name="toolbar_b7", borderwidth=1, command=paste, width=20, height=20)
photo_duplicate = Image.open("icons/duplicate.png")
photo_duplicate = photo_paste.resize((18, 18), Image.LANCZOS)
image_duplicate = ImageTk.PhotoImage(photo_paste)
duplicate_button.config(image=image_duplicate)
duplicate_button.pack(in_=toolbar, side="left", padx=4, pady=4)

# redo
redo_button = Button(name="toolbar_b8", borderwidth=1, command=redo, width=20, height=20)
photo_redo = Image.open("icons/redo.png")
photo_redo = photo_redo.resize((18, 18), Image.LANCZOS)
image_redo = ImageTk.PhotoImage(photo_redo)
redo_button.config(image=image_redo)
redo_button.pack(in_=toolbar, side="left", padx=4, pady=4)

# undo
undo_button = Button(name="toolbar_b9", borderwidth=1, command=undo, width=20, height=20)
photo_undo = Image.open("icons/undo.png")
photo_undo = photo_undo.resize((18, 18), Image.LANCZOS)
image_undo = ImageTk.PhotoImage(photo_undo)
undo_button.config(image=image_undo)
undo_button.pack(in_=toolbar, side="left", padx=4, pady=4)

# find
find_button = Button(name="toolbar_b10", borderwidth=1, command=find_text, width=20, height=20)
photo_find = Image.open("icons/find.png")
photo_find = photo_find.resize((18, 18), Image.LANCZOS)
image_find = ImageTk.PhotoImage(photo_find)
find_button.config(image=image_find)
find_button.pack(in_=toolbar, side="left", padx=4, pady=4)


# Help Menu
def about(event=None):
    messagebox.showinfo("About",
                        "ScriptsEditor\nCreated in Python using Tkinter\nAxlfc, 2023-2024")


def select_directory():
    directory = filedialog.askdirectory()
    if directory:
        os.chdir(directory)
        directory_label.config(text=f"{directory}")
        open_first_text_file(directory)


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


# Function to update menu based on file extension
def update_menu_based_on_extension(ext):
    print(f"Debug: Starting to update menu for extension: {ext}")
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
        # Add other file types and their corresponding menu creators here...
    }

    # Define file type labels
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
        # ... (add labels for other file types)
    }

    # Find the index of the Help menu
    help_menu_index = None
    for index in range(menu.index('end'), -1, -1):
        try:
            if 'Jobs' in menu.entrycget(index, 'label'):
                jobs_menu_index = index
                break
        except Exception as e:
            print(f"Debug: Skipping index {index} due to error: {e}")

    if jobs_menu_index is None:
        print("Debug: Jobs menu not found. Cannot insert dynamic menu correctly.")
        return  # Optionally, raise an exception or handle it as needed

    print(f"Debug: Found Jobs menu at index: {jobs_menu_index}")

    # Check if the dynamic menu already exists, if so, delete it
    dynamic_menu_index = None
    for index, item in enumerate(menu.winfo_children()):
        if isinstance(item, Menu) and item.winfo_name() == 'dynamic':
            dynamic_menu_index = index
            menu.delete(dynamic_menu_index)
            print(f"Debug: Deleted existing dynamic menu at index: {dynamic_menu_index}")
            break

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
    print(f"Debug: Inserted new dynamic menu '{label}' after Jobs menu at index: {jobs_menu_index + 1}")


def run_javascript_analysis():
    # Placeholder for JavaScript analysis logic
    messagebox.showinfo("JavaScript Analysis", "Analyzing JavaScript code.")


def analyze_generic_text_data():
    # Placeholder for generic text data analysis logic
    messagebox.showinfo("Text Data Analysis", "Analyzing generic text data.")


def render_markdown_to_html(markdown_text):
    messagebox.showinfo("Markdown Rendering", "Rendering Markdown to HTML.")
    return markdown.markdown(markdown_text)


def generate_html_from_markdown():
    # Placeholder for generating HTML from Markdown logic
    messagebox.showinfo("HTML Generation", "Generating HTML from Markdown.")


def generate_latex_pdf():
    # Placeholder for generating LaTeX PDF logic
    messagebox.showinfo("LaTeX PDF Generation", "Generating LaTeX PDF.")


def render_latex_to_pdf():
    # Placeholder for rendering LaTeX to PDF logic
    messagebox.showinfo("LaTeX Rendering", "Rendering LaTeX to PDF.")


def analyze_csv_data():
    # Placeholder for CSV analysis logic
    messagebox.showinfo("CSV Analysis", "Performing CSV analysis.")


def create_csv_menu(parent_menu):
    entries = {
        "Analyze Data": analyze_csv_data
    }
    create_submenu(parent_menu, "CSV", entries)


def create_bash_menu(parent_menu):
    parent_menu.add_command(label="Analyze Data")


def create_powershell_menu(parent_menu):
    parent_menu.add_command(label="Analyze Data")


def create_markdown_menu(parent_menu):
    entries = {
        "Render HTML": render_markdown_to_html,
        "Generate HTML": generate_html_from_markdown
    }
    create_submenu(parent_menu, "Markdown", entries)


def create_javascript_menu(parent_menu):
    entries = {
        "Analyze Data": run_javascript_analysis
    }
    create_submenu(parent_menu, "JavaScript", entries)


def create_html_menu(parent_menu):
    parent_menu.add_command(label="Analyze Data")


def create_css_menu(parent_menu):
    parent_menu.add_command(label="Analyze Data")


def create_java_menu(parent_menu):
    parent_menu.add_command(label="Analyze Data")


def create_cpp_menu(parent_menu):
    parent_menu.add_command(label="Analyze Data")


def create_generic_text_menu(parent_menu):
    entries = {
        "Analyze Data": analyze_generic_text_data
    }
    create_submenu(parent_menu, "Text", entries)


def create_latex_menu(parent_menu):
    entries = {
        "Render PDF": render_latex_to_pdf,
        "Generate PDF": generate_latex_pdf
    }
    create_submenu(parent_menu, "LaTeX", entries)


def create_python_menu(parent_menu):
    entries = {
        "Execute Python Script": run_python_script,
        "Change Interpreter": change_interpreter
        # Add more options as needed
    }
    create_submenu(parent_menu, "Interpreter", entries)


def create_submenu(parent_menu, title, entries):
    submenu = Menu(parent_menu, tearoff=0)
    parent_menu.add_cascade(label=title, menu=submenu)

    for label, command in entries.items():
        submenu.add_command(label=label, command=command)


def run_python_script():
    # Placeholder for running Python script logic
    messagebox.showinfo("Run Python Script", "Running Python script.")


def change_interpreter():
    # Placeholder for changing Python interpreter logic
    messagebox.showinfo("Change Interpreter", "Changing Python interpreter.")


def set_modified_status(value):
    global is_modified
    is_modified = value
    update_title()


def update_title():
    title = root.title()
    if is_modified and not title.startswith("*"):
        root.title("*" + title)
    elif not is_modified and title.startswith("*"):
        root.title(title[1:])


def save_script():
    script_name = script_name_label.cget("text").split(": ")[-1]
    if script_name:
        script_content = script_text.get("1.0", "end")
        save_file(script_name, script_content)
        set_modified_status(False)  # Reset the modification status
    else:
        save_as_new_script()


def remove_asterisk_from_title():
    title = root.title()
    if title.startswith("*"):
        root.title(title[1:])


from tkinter import filedialog, messagebox
import os


def save_as_new_script():
    file_path = filedialog.asksaveasfilename(filetypes=file_types, defaultextension=".txt")

    # Si el usuario no selecciona un archivo, cancela la operación
    if not file_path:
        return

    # Verifica si el nombre del archivo tiene un punto (indicando una extensión)
    if '.' not in os.path.basename(file_path):
        response = messagebox.askquestion("Confirmar Extensión",
                                          "No has especificado una extensión. ¿Quieres dejar el archivo sin extensión?",
                                          icon='warning')
        if response == 'no':
            return  # El usuario decide no guardar el archivo

    with open(file_path, "w") as file:
        content = script_text.get("1.0", "end-1c")
        file.write(content)
    update_script_name_label(file_path)


def update_script_name_label(file_path):
    base_name = os.path.basename(file_path)
    script_name_label.config(text=f"Nombre del Script: {base_name}")


def update_title_with_filename(file_name):
    # Esta función actualizará el título de la ventana con el nuevo nombre de archivo
    base_name = os.path.basename(file_name)
    root.title(f"{base_name} - Scripts Editor")


def save_file(file_name, content):
    with open(file_name, "w") as file:
        file.write(content)
    messagebox.showinfo("Save", "Script saved successfully!")


def colorize_text():
    script_content = script_text.get("1.0", "end")
    script_text.delete("1.0", "end")
    script_text.insert("1.0", script_content)


def see_stdout():
    stdout_window = Toplevel(root)
    stdout_window.title("Standard Output (stdout)")
    stdout_text = Text(stdout_window)
    stdout_text.pack()

    script_out_name = script_name_label.cget('text') + ".out"
    try:
        with open(script_out_name, "r") as f:
            stdout_text.insert("1.0", f.read())
    except FileNotFoundError:
        stdout_text.insert("1.0", "No stdout data available.")


def see_stderr():
    stderr_window = Toplevel(root)
    stderr_window.title("Standard Error (stderr)")
    stderr_text = Text(stderr_window)
    stderr_text.pack()

    script_err_name = script_name_label.cget('text') + ".err"
    try:
        with open(script_err_name, "r") as f:
            stderr_text.insert("1.0", f.read())
    except FileNotFoundError:
        stderr_text.insert("1.0", "No stderr data available.")

    # Configure the text widget to use red font color
    stderr_text.tag_configure("red", foreground="red")
    stderr_text.tag_add("red", "1.0", "end")


def run_script():
    script = script_text.get("1.0", "end-1c")
    arguments = entry_arguments_entry.get()
    generate_stdout = generate_stdin.get()
    generate_stderr = generate_stdin_err.get()

    try:
        # Execute the script with provided arguments
        # Use the subprocess module to run the script as a separate process
        # result = subprocess.run([script] + arguments.split(), capture_output=True, shell=True)
        # TODO "/"
        process = subprocess.Popen(["bash"] + [directory_label.cget('text') + "/" + script_name_label.cget('text')] + arguments.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout_data, stderr_data = process.communicate()

        # Print the stdout and stderr
        if generate_stdout:
            script_out_name = script_name_label.cget('text') + ".out"
            print(script_out_name)
            p = open(script_out_name, "w+")
            p.write(stdout_data.decode())

        if generate_stderr:
            script_err_name = script_name_label.cget('text') + ".err"
            p = open(script_err_name, "w+")
            p.write(stderr_data.decode())

        messagebox.showinfo("Script Execution", "Script executed successfully.")
    except Exception as e:
        messagebox.showerror("Script Execution", f"Error executing script:\n{str(e)}")


def run_script_with_timeout(timeout_seconds):
    script = script_text.get("1.0", "end-1c")
    arguments = entry_arguments_entry.get()
    generate_stdout = generate_stdin.get()
    generate_stderr = generate_stdin_err.get()

    try:
        # Execute the script with provided arguments
        # Use the subprocess module to run the script as a separate process
        # result = subprocess.run([script] + arguments.split(), capture_output=True, shell=True)
        # TODO "/"
        process = subprocess.Popen(
            ["bash"] + [directory_label.cget('text') + "/" + script_name_label.cget('text')] + arguments.split(),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        sleep(timeout_seconds)
        stdout_data, stderr_data = process.communicate()

        # Print the stdout and stderr
        if generate_stdout:
            script_out_name = script_name_label.cget('text') + ".out"
            print(script_out_name)
            p = open(script_out_name, "w+")
            p.write(stdout_data.decode())

        if generate_stderr:
            script_err_name = script_name_label.cget('text') + ".err"
            p = open(script_err_name, "w+")
            p.write(stderr_data.decode())

        messagebox.showinfo("Script Execution", "Script executed successfully.")
    except Exception as e:
        messagebox.showerror("Script Execution", f"Error executing script:\n{str(e)}")


def remove_selected_at_job(listbox):
    selected_indices = listbox.curselection()
    if not selected_indices:
        return

    selected_index = selected_indices[0]
    selected_item = listbox.get(selected_index)

    if "No AT jobs found for user" in selected_item:
        listbox.delete(selected_index)  # Delete the special message
    else:
        job_id = selected_item.split()[0]
        try:
            subprocess.run(["atrm", job_id], check=True)
            listbox.delete(selected_index)
        except subprocess.CalledProcessError:
            messagebox.showerror("Error", f"Failed to remove AT job {job_id}")

def run_script_once(schedule_time):
    script_path = os.path.join(directory_label.cget('text'), script_name_label.cget('text'))
    arguments = entry_arguments_entry.get()
    generate_stdout = generate_stdin.get()
    generate_stderr = generate_stdin_err.get()

    # Extract hour, minute, and AM/PM from the input time string
    match = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?', schedule_time)
    if not match:
        messagebox.showerror("Invalid Time", "Please enter a valid time in HH:MM AM/PM format.")
        return

    hour = int(match.group(1))
    minute = int(match.group(2))
    am_pm = match.group(3)

    # Adjust hour for 12-hour clock format
    if am_pm and am_pm.lower() == 'pm' and hour != 12:
        hour += 12

    if am_pm and am_pm.lower() == 'am' and hour == 12:
        hour = 0

    if not validate_time(hour, minute):
        return

    try:
        # Use the 'at' command to schedule the script execution and redirection
        at_time = f"{hour:02d}:{minute:02d}"

        stdout_redirect = f">{script_name_label.cget('text')}.out" if generate_stdout else "/dev/null"
        stderr_redirect = f"2>{script_name_label.cget('text')}.err" if generate_stderr else "/dev/null"

        at_command = f"atq; at {at_time} <<EOF\n{script_path} {arguments} {stdout_redirect} {stderr_redirect}\nEOF"

        process = subprocess.Popen(at_command, shell=True)
        process.wait()

        messagebox.showinfo("Script Scheduled", f"Script scheduled to run at {at_time}.")
    except Exception as e:
        messagebox.showerror("Error Scheduling Script", f"An error occurred while scheduling the script:\n{str(e)}")


def run_script_crontab(minute, hour, day, month, day_of_week):
    if not minute or not hour or not day or not month or not day_of_week:
        messagebox.showerror("Error Scheduling Script", "All cron schedule fields must be filled.")
        return

    # Build the cron schedule string
    cron_schedule = f"{minute} {hour} {day} {month} {day_of_week}"

    script_path = os.path.join(directory_label.cget('text'), script_name_label.cget('text'))
    arguments = entry_arguments_entry.get()

    generate_stdout = generate_stdin.get()
    generate_stderr = generate_stdin_err.get()

    # Determine the full path for .out and .err files based on the selected directory
    out_file = os.path.join(directory_label.cget('text'), f"{script_name_label.cget('text')}.out")
    err_file = os.path.join(directory_label.cget('text'), f"{script_name_label.cget('text')}.err")

    try:
        stdout_redirect = f">{out_file}" if generate_stdout else "/dev/null"
        stderr_redirect = f"2>{err_file}" if generate_stderr else "/dev/null"

        # Use the 'crontab' command to set up the script execution schedule
        crontab_command = f"(crontab -l; echo '{cron_schedule} {script_path} {arguments} {stdout_redirect} {stderr_redirect}') | crontab -"
        process = subprocess.Popen(crontab_command, shell=True)
        process.wait()

        messagebox.showinfo("Script Scheduled", f"Script scheduled with cron: {cron_schedule}")
    except Exception as e:
        messagebox.showerror("Error Scheduling Script", f"An error occurred while scheduling the script:\n{str(e)}")


def validate_time(hour, minute):
    try:
        hour = int(hour)
        minute = int(minute)
        if not (0 <= hour < 24) or not (0 <= minute < 60):
            raise ValueError
        return True
    except ValueError:
        messagebox.showerror("Invalid Time", "Please enter a valid time in HH:MM format.")
        return False


at_window = None
crontab_window = None


def open_at_window():
    def update_at_jobs():
        listbox.delete(0, END)
        populate_at_jobs(listbox)
        at_window.after(5000, update_at_jobs)

    global at_window
    at_window = Toplevel(root)
    at_window.title("AT Jobs")
    at_window.geometry("600x400")

    listbox = Listbox(at_window, width=80)
    listbox.pack(fill="both", expand=True)

    populate_at_jobs(listbox)

    remove_button = Button(at_window, text="Remove Selected", command=lambda: remove_selected_at_job(listbox))
    remove_button.pack(side="bottom")

    at_window.after(0, update_at_jobs)
    at_window.mainloop()


def populate_at_jobs(listbox):
    try:
        at_output = subprocess.check_output(["atq"], text=True).splitlines()
        if not at_output:
            username = subprocess.check_output(["whoami"], text=True).strip()  # Get the current user
            listbox.insert(END, f"No AT jobs found for user {username}.")
        else:
            for line in at_output:
                listbox.insert(END, line)
    except subprocess.CalledProcessError:
        messagebox.showerror("Error", "Failed to retrieve AT jobs")


def remove_selected_cron_job(listbox):
    selected_indices = listbox.curselection()
    if not selected_indices:
        return

    selected_index = selected_indices[0]
    selected_job = listbox.get(selected_index)

    try:
        # Create a temporary file to store modified crontab
        temp_file = tempfile.NamedTemporaryFile(delete=False)

        # Save the current crontab to the temporary file
        subprocess.run(["crontab", "-l"], text=True, stdout=temp_file)

        # Reset the file pointer to the beginning
        temp_file.seek(0)

        selected_job_bytes = selected_job.encode("utf-8")

        # Filter out the selected job and write to a new temporary file
        filtered_lines = [line for line in temp_file if selected_job_bytes not in line]

        temp_file.close()

        # Write the filtered content back to the temporary file
        with open(temp_file.name, "wb") as f:
            f.writelines(filtered_lines)

        # Load the modified crontab from the temporary file
        subprocess.run(["crontab", temp_file.name], check=True)

        # Delete the temporary file
        os.remove(temp_file.name)

        # Remove the item from the listbox
        listbox.delete(selected_index)

    except subprocess.CalledProcessError:
        messagebox.showerror("Error", "Failed to remove cron job")


def open_cron_window():
    def update_cron_jobs():
        listbox.delete(0, END)
        populate_cron_jobs(listbox)
        crontab_window.after(5000, update_cron_jobs)

    global crontab_window
    crontab_window = Toplevel(root)
    crontab_window.title("Cron Jobs")
    crontab_window.geometry("600x400")

    listbox = Listbox(crontab_window, width=80)
    listbox.pack(fill="both", expand=True)

    listbox.insert(END, "Loading cron jobs...")  # Initial message while loading
    populate_cron_jobs(listbox)

    remove_button = Button(crontab_window, text="Remove Selected", command=lambda: remove_selected_cron_job(listbox))
    remove_button.pack(side="bottom")

    crontab_window.after(0, update_cron_jobs)
    crontab_window.mainloop()


def populate_cron_jobs(listbox):
    try:
        cron_output = subprocess.check_output(["crontab", "-l"], text=True).splitlines()
        # print("hola" + cron_output)
        if not cron_output:
            username = subprocess.check_output(["whoami"], text=True).strip()  # Get the current user
            listbox.insert(END, f"No cron jobs found for user {username}.")
        else:
            for line in cron_output:
                listbox.insert(END, line)
    except subprocess.CalledProcessError:
        username = subprocess.check_output(["whoami"], text=True).strip()  # Get the current user
        listbox.insert(END, f"No cron jobs found for user {username}.")
        #messagebox.showwarning("Warning", "Failed to retrieve cron jobs")


def remove_selected_cron_job(listbox):
    selected_indices = listbox.curselection()
    if not selected_indices:
        return

    selected_index = selected_indices[0]
    selected_job = listbox.get(selected_index)

    try:
        # Create a temporary file to store modified crontab
        temp_file = tempfile.NamedTemporaryFile(delete=False)

        # Save the current crontab to the temporary file
        subprocess.run(["crontab", "-l"], text=True, stdout=temp_file)

        # Reset the file pointer to the beginning
        temp_file.seek(0)

        selected_job_bytes = selected_job.encode("utf-8")

        # Filter out the selected job and write to a new temporary file
        filtered_lines = [line for line in temp_file if selected_job_bytes not in line]

        temp_file.close()

        # Write the filtered content back to the temporary file
        with open(temp_file.name, "wb") as f:
            f.writelines(filtered_lines)

        # Load the modified crontab from the temporary file
        subprocess.run(["crontab", temp_file.name], check=True)

        # Delete the temporary file
        os.remove(temp_file.name)

        # Remove the item from the listbox
        listbox.delete(selected_index)

    except subprocess.CalledProcessError:
        messagebox.showerror("Error", "Failed to remove cron job")


def open_terminal_window():
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
                output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True, text=True, cwd=os.getcwd())
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


def show_selected_model():
    pass


def render_markdown_to_html(markdown_text):
    return markdown.markdown(markdown_text)


def open_ai_assistant_window():
    original_md_content = None
    global render_markdown_var

    def toggle_render_markdown(is_checked, text_widget):
        global original_md_content, markdown_render_enabled

        if is_checked:
            # Save the original Markdown content
            original_md_content = text_widget.get("1.0", "end-1c")
            # Render Markdown to HTML
            html_content = markdown.markdown(original_md_content)
            text_widget.delete("1.0", "end")
            text_widget.insert("1.0", html_content)
            markdown_render_enabled = True
        else:
            # Restore the original Markdown content
            text_widget.delete("1.0", "end")
            text_widget.insert("1.0", original_md_content)
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

    # Add 'Selected Model' Menu Item
    settings_menu.add_command(label="Selected Model", command=show_selected_model)

    # Checkbox Variable for 'Render Markdown to HTML'
    render_markdown_var = IntVar()
    settings_menu.add_checkbutton(
        label="Render Markdown to HTML",
        onvalue=1,
        offvalue=0,
        variable=render_markdown_var,
        command=lambda: toggle_render_markdown(render_markdown_var.get(), output_text)
    )

    # Create the output text widget
    output_text = scrolledtext.ScrolledText(ai_assistant_window, height=20, width=80)
    output_text.pack(fill='both', expand=True)

    # Initialize a list to store command history
    command_history = []
    # Initialize a pointer to the current position in the command history
    history_pointer = [0]

    status_label_var = StringVar()
    status_label = Label(ai_assistant_window, textvariable=status_label_var)
    status_label.pack()
    status_label_var.set("READY")  # Initialize the status label as "READY"

    output_text.insert(END, "> ")
    output_text.see(END)

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
                    output_text.insert(END, char)
                    output_text.see(END)
                    # Update the Tkinter window; use after method to ensure GUI updates
                    ai_assistant_window.after(10, lambda: ai_assistant_window.update_idletasks())

                    # Update the buffer with the latest character
                    output_buffer += char
                    output_buffer = output_buffer[-buffer_size:]  # Keep only the last 'buffer_size' characters

                    # Check if the last two characters are '> ' indicating the end of the response
                    if output_buffer == '> ':
                        break
                elif process.poll() is not None:
                    break  # Break if the subprocess has finished

        except Exception as e:
            output_text.insert(END, f"Error: {e}\n")
        finally:
            on_processing_complete()

    def on_processing_complete():
        print("Debug: Processing complete, re-enabling entry widget.")  # Debug print
        entry.config(state='normal')  # Re-enable the entry widget
        status_label_var.set("READY")  # Update label to show AI is processing

    def execute_ai_assistant_command():
        global process  # Define process as a global variable

        ai_command = entry.get()
        if ai_command.strip():
            output_text.insert(END, f"You: {ai_command}\n")
            output_text.see(END)
            entry.delete(0, END)
            entry.config(state='disabled')  # Disable entry while processing
            status_label_var.set("AI is thinking...")  # Update label to show AI is processing

            ai_script_path = r"C:\Users\AxelFC\Documents\git\UE5-python\Content\Python\src\text\ai_assistant.py"
            command = ['python', ai_script_path, ai_command]

            # Terminate existing subprocess if it exists
            if 'process' in globals() and process.poll() is None:
                process.terminate()

            try:
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                           bufsize=1)
                threading.Thread(target=stream_output, args=(process,)).start()
            except Exception as e:
                output_text.insert(END, f"Error: {e}\n")
                on_processing_complete()
        else:
            entry.config(state='normal')  # Re-enable the entry widget if no command is entered

    entry = Entry(ai_assistant_window, width=30)
    entry.pack(side='bottom', fill='x')
    entry.focus()
    entry.bind("<Return>", lambda event: execute_ai_assistant_command())
    entry.bind("<Up>", navigate_history)
    entry.bind("<Down>", navigate_history)

    ai_assistant_window.mainloop()

def open_scheduled_tasks_window():
    window = Toplevel()
    window.title("Scheduled Tasks")
    window.geometry("600x400")

    listbox = Listbox(window, width=80)
    listbox.pack(fill="both", expand=True)

    # This variable will hold the last selected task index
    last_selected_index = [None]

    def populate_tasks():
        # Remember the last selected item
        if listbox.curselection():
            last_selected_index[0] = listbox.curselection()[0]
        listbox.delete(0, END)
        tasks = list_tasks()  # Get the list of tasks
        for task in tasks:
            listbox.insert(END, task)
        # Set the selection back to the last selected item if it exists
        if last_selected_index[0] is not None and last_selected_index[0] < listbox.size():
            listbox.selection_set(last_selected_index[0])
            listbox.see(last_selected_index[0])

    def delete_selected_task():
        selection = listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "No task selected")
            return

        selected_task_info = listbox.get(selection[0])
        print("THE SELECTED_TASK_INFO IS:\n", selected_task_info)
        task_name = selected_task_info.split('\"')[1]
        try:
            delete_task(task_name)
            populate_tasks()  # Refresh the list
            last_selected_index[0] = None  # Reset the last selected index
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete task: {e}")

    def update_tasks():
        populate_tasks()
        window.after(5000, update_tasks)  # Schedule next update

    populate_tasks()  # Initial population of the list
    update_tasks()    # Start the periodic update

    delete_button = Button(window, text="Delete Selected", command=delete_selected_task)
    delete_button.pack()

    window.mainloop()


def open_new_at_task_window():
    # Create a new window
    new_task_window = Toplevel(root)
    new_task_window.title("New 'at' Task")
    new_task_window.geometry("400x150")

    # Add a label and entry for the task name
    Label(new_task_window, text="Task Name:").grid(row=0, column=0)
    task_name_entry = Entry(new_task_window)
    task_name_entry.grid(row=0, column=1)

    # Add a label and entry for the time
    Label(new_task_window, text="Time (HH:MM):").grid(row=1, column=0)
    time_entry = Entry(new_task_window)
    time_entry.grid(row=1, column=1)

    # Add a label and entry for the program path
    Label(new_task_window, text="Program Path:").grid(row=2, column=0)
    program_path_entry = Entry(new_task_window)
    program_path_entry.grid(row=2, column=1)

    # Function to handle creating an 'at' job
    def create_at_job():
        task_name = task_name_entry.get()
        time = time_entry.get()
        program_path = program_path_entry.get()
        # Here you would call the function to create the 'at' job with the given details
        try:
            at_function(task_name, time, program_path)
            messagebox.showinfo("Scheduled", f"Task '{task_name}' scheduled at {time} to run {program_path}")
        except Exception as e:
            messagebox.showerror("Task Execution", f"Error creating at task:\n{str(e)}")

    # Add buttons for creating 'at' and 'crontab' jobs
    Button(new_task_window, text="Create 'at' Job", command=create_at_job).grid(row=3, column=0)

    # Run the window's main event loop
    new_task_window.mainloop()


def open_new_crontab_task_window():
    # Create a new window
    new_cron_task_window = Toplevel(root)
    new_cron_task_window.title("New 'crontab' Task")
    new_cron_task_window.geometry("500x300")

    # Add label and entry for each crontab time field
    Label(new_cron_task_window, text="Name:").grid(row=0, column=0)
    name_entry = Entry(new_cron_task_window)
    name_entry.grid(row=0, column=1)

    # Add label and entry for each crontab time field
    Label(new_cron_task_window, text="Minute:").grid(row=1, column=0)
    minute_entry = Entry(new_cron_task_window)
    minute_entry.grid(row=1, column=1)

    Label(new_cron_task_window, text="Hour:").grid(row=2, column=0)
    hour_entry = Entry(new_cron_task_window)
    hour_entry.grid(row=2, column=1)

    Label(new_cron_task_window, text="Day (Month):").grid(row=3, column=0)
    day_month_entry = Entry(new_cron_task_window)
    day_month_entry.grid(row=3, column=1)

    Label(new_cron_task_window, text="Month:").grid(row=4, column=0)
    month_entry = Entry(new_cron_task_window)
    month_entry.grid(row=4, column=1)

    Label(new_cron_task_window, text="Day (Week):").grid(row=5, column=0)
    day_week_entry = Entry(new_cron_task_window)
    day_week_entry.grid(row=5, column=1)

    Label(new_cron_task_window, text="Script Path:").grid(row=6, column=0)
    script_path_entry = Entry(new_cron_task_window)
    script_path_entry.grid(row=6, column=1)

    # Function to handle creating a 'crontab' job
    def create_crontab_job():
        name = name_entry.get()
        minute = minute_entry.get()
        hour = hour_entry.get()
        day_month = day_month_entry.get()
        month = month_entry.get()
        day_week = day_week_entry.get()
        script_path = script_path_entry.get()

        # Validate fields
        if not all([name, minute, hour, day_month, month, day_week, script_path]):
            messagebox.showerror("Error", "All fields must be filled.")
            return

        # Here you would call the function to create the 'crontab' job with the given details
        crontab_function(name, minute, hour, day_month, month, day_week, script_path)
        messagebox.showinfo("Scheduled",
                            f"Crontab task scheduled to run script at {minute} {hour} {day_month} {month} {day_week}.")

    # Add button to create 'crontab' job
    Button(new_cron_task_window, text="Create 'crontab' Job", command=create_crontab_job).grid(row=7, column=0,
                                                                                               columnspan=2)

    # Run the window's main event loop
    new_cron_task_window.mainloop()