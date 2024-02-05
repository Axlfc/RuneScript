import os
import platform
from tkinter import Menu, Button, messagebox, filedialog, END

from PIL import Image, ImageTk

from edit_operations import copy, cut, paste, redo, undo, duplicate

from scheduled_tasks import open_cron_window, open_at_window, open_scheduled_tasks_window, open_new_at_task_window, \
    open_new_crontab_task_window
from script_tasks import analyze_csv_data, render_markdown_to_html, generate_html_from_markdown, \
    run_javascript_analysis, analyze_generic_text_data, render_latex_to_pdf, generate_latex_pdf, run_python_script, \
    change_interpreter

from tk_utils import toolbar, menu, root, script_name_label, script_text
from tool_functions import find_text, change_color, open_search_replace_dialog, open_terminal_window, \
    open_ai_assistant_window

house_icon = "🏠"
open_icon = "📂"
save_icon = "💾"
save_new_icon = "🆕"
undo_icon = "⮪"
redo_icon = "⮬"
run_icon = "▶"


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


# Help Menu
def about(event=None):
    messagebox.showinfo("About",
                        "ScriptsEditor\nCreated in Python using Tkinter\nAxlfc, 2023-2024")


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


def new(event=None):
    global file_name

    ans = messagebox.askquestion(title="Save File", message="Would you like to save this file?")
    if ans == "yes":
        save()

    file_name = ""
    script_text.delete('1.0', 'end')
    root.title("*New file - Script Editor")


def open_script():
    file_path = filedialog.askopenfilename(filetypes=file_types)
    if file_path:
        global file_extension
        file_extension = os.path.splitext(file_path)[1]
        print("Opening file with extension:", file_extension)
        open_file(file_path)
    set_modified_status(False)  # Reset the modification status


def open_file(file_path):
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


def update_title_with_filename(file_name):
    # Esta función actualizará el título de la ventana con el nuevo nombre de archivo
    base_name = os.path.basename(file_name)
    root.title(f"{base_name} - Scripts Editor")


def update_modification_status(event):
    set_modified_status(True)


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


def save_as():
    global file_name

    new_file_name = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
    if new_file_name:
        file_name = new_file_name
        save()
    else:
        messagebox.showinfo("Info", "File saving canceled.")


def close(event=None):
    save()
    root.quit()


def save_file(file_name, content):
    with open(file_name, "w") as file:
        file.write(content)
    messagebox.showinfo("Save", "Script saved successfully!")


def save_script():
    script_name = script_name_label.cget("text").split(": ")[-1]
    if script_name:
        script_content = script_text.get("1.0", "end")
        save_file(script_name, script_content)
        set_modified_status(False)  # Reset the modification status
    else:
        save_as_new_script()


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
duplicate_button = Button(name="toolbar_b7", borderwidth=1, command=duplicate, width=20, height=20)
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


def create_menu():
    # File menu.
    file_menu = Menu(menu)
    menu.add_cascade(label="File", menu=file_menu, underline=0)

    file_menu.add_command(label="New", command=new, compound='left', image=image_new, accelerator='Ctrl+N',
                          underline=0)  # command passed is here the method defined above.
    file_menu.add_command(label="Open", command=open_script, compound='left', image=image_open, accelerator='Ctrl+O',
                          underline=0)
    file_menu.add_separator()
    file_menu.add_command(label="Save", command=save_script, compound='left', image=image_save, accelerator='Ctrl+S',
                          underline=0)
    file_menu.add_command(label="Save As", command=save_as_new_script, accelerator='Ctrl+Shift+S', underline=1)
    # file_menu.add_command(label="Rename", command=rename, accelerator='Ctrl+Shift+R', underline=0)
    file_menu.add_separator()
    file_menu.add_command(label="Close", command=close, accelerator='Alt+F4', underline=0)

    # Edit Menu.
    edit_menu = Menu(menu)
    menu.add_cascade(label="Edit", menu=edit_menu, underline=0)

    edit_menu.add_command(label="Undo", command=undo, compound='left', image=image_undo, accelerator='Ctrl+Z', underline=0)
    edit_menu.add_command(label="Redo", command=redo, compound='left', image=image_redo, accelerator='Ctrl+Y', underline=0)

    edit_menu.add_separator()

    edit_menu.add_command(label="Cut", command=cut, compound='left', image=image_cut, accelerator='Ctrl+X', underline=0)
    edit_menu.add_command(label="Copy", command=copy, compound='left', image=image_copy, accelerator='Ctrl+C',
                          underline=1)
    edit_menu.add_command(label="Paste", command=paste, compound='left', image=image_paste, accelerator='Ctrl+P',
                          underline=0)
    edit_menu.add_command(label="Duplicate", command=duplicate, compound='left', image=image_duplicate, accelerator='Ctrl+D',
                          underline=0)
    # edit_menu.add_command(label="Delete", command=delete, underline=0)
    #edit_menu.add_separator()
    #edit_menu.add_command(label="Select All", command=select_all, accelerator='Ctrl+A', underline=0)
    #edit_menu.add_command(label="Clear All", command=delete_all, underline=6)

    # Tool Menu
    tool_menu = Menu(menu)
    menu.add_cascade(label="Tools", menu=tool_menu, underline=0)

    tool_menu.add_command(label="Change Color", command=change_color)
    tool_menu.add_command(label="Search", command=find_text, compound='left', image=image_find, accelerator='Ctrl+F')
    tool_menu.add_command(label="Search and Replace", command=open_search_replace_dialog, compound='left',
                          image=image_find, accelerator='Ctrl+R')
    tool_menu.add_separator()
    tool_menu.add_command(label="Terminal", command=open_terminal_window)
    tool_menu.add_command(label="AI Assistant", command=open_ai_assistant_window)

    # Jobs Menu
    jobs_menu = Menu(menu)
    menu.add_cascade(label="Jobs", menu=jobs_menu, underline=0)
    jobs_menu.add_command(label="New 'at'", command=open_new_at_task_window)
    jobs_menu.add_command(label="New 'crontab'", command=open_new_crontab_task_window)
    jobs_menu.add_separator()
    get_scheduled_tasks(jobs_menu)


    help_menu = Menu(menu)
    menu.add_cascade(label="Help", menu=help_menu, underline=0)
    help_menu.add_command(label="About", command=about, accelerator='Ctrl+H', underline=0)


def get_scheduled_tasks(submenu):
    if platform.system() == "Windows":
        submenu.add_command(label="Scheduled Tasks", command=open_scheduled_tasks_window)
    else:
        submenu.add_command(label="at", command=open_at_window)
        submenu.add_command(label="crontab", command=open_cron_window)


def create_submenu(parent_menu, title, entries):
    submenu = Menu(parent_menu, tearoff=0)
    parent_menu.add_cascade(label=title, menu=submenu)

    for label, command in entries.items():
        submenu.add_command(label=label, command=command)
