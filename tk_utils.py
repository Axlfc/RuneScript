from tkinter import Toplevel, Label, Button, Tk, StringVar, IntVar, Frame, Menu, Text, Entry
from tkinter import END, INSERT, SEL_FIRST, SEL_LAST, SEL
from tkinter import ttk, scrolledtext, filedialog, simpledialog
import tkinter.messagebox as messagebox
import tkinter.colorchooser as colorchooser
from PIL import Image, ImageTk  # sudo apt-get install python3-pil python3-pil.imagetk
import tkinter
from crontab import CronTab
import subprocess

import os

context_menu = None  # Define context_menu as a global variable

# MAIN MENU METHODS

file_name = ""  # Current file name.
current_font_family = "Liberation Mono"
current_font_size = 12
fontColor = '#000000'
fontBackground = '#FFFFFF'

new_name = ""  # Used for renaming the file

is_modified = False  # Added is_modified variable


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


def open_file(event=None):
    new()
    file = filedialog.askopenfile()
    global file_name
    file_name = file.name
    text.insert(INSERT, file.read())


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

    if is_modified == False:
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


def delete():
    if text.tag_ranges("sel"):
        text.tag_add("sel", SEL_FIRST, SEL_LAST)
        text.delete(SEL_FIRST, SEL_LAST)


def undo():
    text.edit_undo()


def redo():
    text.edit_redo()


def select_all(event=None):
    text.tag_add(SEL, "1.0", END)


def delete_all():
    text.delete(1.0, END)


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


def duplicate(event=None):
    selected_text = text.get("sel.first", "sel.last")
    text.insert("insert", selected_text)


def show_context_menu(event):
    try:
        context_menu.tk_popup(event.x_root, event.y_root)
    finally:
        context_menu.grab_release()



def delete():
    text.delete(index1=SEL_FIRST, index2=SEL_LAST)


def undo():
    text.edit_undo()


def redo():
    text.edit_redo()


def select_all(event=None):
    text.tag_add("sel", "1.0", "end")


def delete_all():
    text.delete(1.0, END)


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
    text.tag_remove('found', '1.0', END)
    text.tag_config('found', foreground='red')
    list_of_words = value.split(' ')
    for word in list_of_words:
        idx = '1.0'
        while idx:
            idx = text.search(word, idx, nocase=1, stopindex=END)
            if idx:
                lastidx = '%s+%dc' % (idx, len(word))
                text.tag_add('found', idx, lastidx)
                print(lastidx)
                idx = lastidx


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
directory_label = Label(frm, text=os.getcwd(), anchor="center", justify="center")

script_frm = ttk.Frame(root, padding=0)
script_name_label = Label(script_frm, text="Script Name: ")

script_text = scrolledtext.ScrolledText(root, wrap="word", height=20, width=60)
text = Text(wrap="word", font=("Liberation Mono", 12), background="white", borderwidth=0, highlightthickness=0,
            undo=True)

entry_text = StringVar()
content_frm = ttk.Frame(root, padding=0)
entry_arguments_entry = ttk.Entry(content_frm, textvariable=entry_text, width=40)

generate_stdin = IntVar()
see_stderr = IntVar()

run_frm = ttk.Frame(root, padding=0)

program_frm = ttk.Frame(root, padding=0)
program_frm.grid(row=5, column=0, pady=0, sticky="e")  # Set sticky to "e" for right alignment

hour_entry = ttk.Entry(program_frm, width=2)
minute_entry = ttk.Entry(program_frm, width=2)


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
photo_new = photo_new.resize((18, 18), Image.ANTIALIAS)
image_new = ImageTk.PhotoImage(photo_new)
new_button.config(image=image_new)
new_button.pack(in_=toolbar, side="left", padx=4, pady=4)

# save
save_button = Button(name="toolbar_b1", borderwidth=1, command=save, width=20, height=20)
photo_save = Image.open("icons/save.png")
photo_save = photo_save.resize((18, 18), Image.ANTIALIAS)
image_save = ImageTk.PhotoImage(photo_save)
save_button.config(image=image_save)
save_button.pack(in_=toolbar, side="left", padx=4, pady=4)

# open
open_button = Button(name="toolbar_b3", borderwidth=1, command=open_file, width=20, height=20)
photo_open = Image.open("icons/open.png")
photo_open = photo_open.resize((18, 18), Image.ANTIALIAS)
image_open = ImageTk.PhotoImage(photo_open)
open_button.config(image=image_open)
open_button.pack(in_=toolbar, side="left", padx=4, pady=4)

# copy
copy_button = Button(name="toolbar_b4", borderwidth=1, command=copy, width=20, height=20)
photo_copy = Image.open("icons/copy.png")
photo_copy = photo_copy.resize((18, 18), Image.ANTIALIAS)
image_copy = ImageTk.PhotoImage(photo_copy)
copy_button.config(image=image_copy)
copy_button.pack(in_=toolbar, side="left", padx=4, pady=4)

# cut
cut_button = Button(name="toolbar_b5", borderwidth=1, command=cut, width=20, height=20)
photo_cut = Image.open("icons/cut.png")
photo_cut = photo_cut.resize((18, 18), Image.ANTIALIAS)
image_cut = ImageTk.PhotoImage(photo_cut)
cut_button.config(image=image_cut)
cut_button.pack(in_=toolbar, side="left", padx=4, pady=4)

# paste
paste_button = Button(name="toolbar_b6", borderwidth=1, command=paste, width=20, height=20)
photo_paste = Image.open("icons/paste.png")
photo_paste = photo_paste.resize((18, 18), Image.ANTIALIAS)
image_paste = ImageTk.PhotoImage(photo_paste)
paste_button.config(image=image_paste)
paste_button.pack(in_=toolbar, side="left", padx=4, pady=4)

# duplicate
duplicate_button = Button(name="toolbar_b7", borderwidth=1, command=paste, width=20, height=20)
photo_duplicate = Image.open("icons/duplicate.png")
photo_duplicate = photo_paste.resize((18, 18), Image.ANTIALIAS)
image_duplicate = ImageTk.PhotoImage(photo_paste)
duplicate_button.config(image=image_duplicate)
duplicate_button.pack(in_=toolbar, side="left", padx=4, pady=4)

# redo
redo_button = Button(name="toolbar_b8", borderwidth=1, command=redo, width=20, height=20)
photo_redo = Image.open("icons/redo.png")
photo_redo = photo_redo.resize((18, 18), Image.ANTIALIAS)
image_redo = ImageTk.PhotoImage(photo_redo)
redo_button.config(image=image_redo)
redo_button.pack(in_=toolbar, side="left", padx=4, pady=4)

# undo
undo_button = Button(name="toolbar_b9", borderwidth=1, command=undo, width=20, height=20)
photo_undo = Image.open("icons/undo.png")
photo_undo = photo_undo.resize((18, 18), Image.ANTIALIAS)
image_undo = ImageTk.PhotoImage(photo_undo)
undo_button.config(image=image_undo)
undo_button.pack(in_=toolbar, side="left", padx=4, pady=4)

# find
find_button = Button(name="toolbar_b10", borderwidth=1, command=find_text, width=20, height=20)
photo_find = Image.open("icons/find.png")
photo_find = photo_find.resize((18, 18), Image.ANTIALIAS)
image_find = ImageTk.PhotoImage(photo_find)
find_button.config(image=image_find)
find_button.pack(in_=toolbar, side="left", padx=4, pady=4)


# Help Menu
def about(event=None):
    messagebox.showinfo("About",
                        "ScriptsEditor\nCreated in Python using Tkinter\nAxlfc, 2023")


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


def open_script():
    file_path = filedialog.askopenfilename(filetypes=[("All Files", "*.*"), ("Python Scripts", "*.py"), ("Shell Scripts", "*.sh"), ("Text Files", "*.txt"), ("TeX Files", "*.tex")])
    if file_path:
        open_file(file_path)
    set_modified_status(False)  # Reset the modification status


def open_file(file_path):
    script_name_label.config(text=f"{os.path.basename(file_path)}")
    with open(file_path, "r") as file:
        script_content = file.read()
    script_text.delete("1.0", "end")
    script_text.insert("1.0", script_content)
    colorize_text()


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


def save_as_new_script():
    file_types = [("Python Scripts", "*.py"),
                  ("Shell Scripts", "*.sh"),
                  ("Text Files", "*.txt"),
                  ("LaTeX Files", "*.tex"),
                  ("All Files", "*.*")]
    file = filedialog.asksaveasfile(filetypes=file_types)
    if file is not None:
        # Get the selected file type
        selected_extension = file.name.split('.')[-1]
        # Append the selected extension to the file name
        file_path = file.name + '.' + selected_extension
        # Implement your save logic here using the file_path
        file.close()


def save_file(file_name, content):
    with open(file_name, "w") as file:
        file.write(content)
    messagebox.showinfo("Save", "Script saved successfully!")


def colorize_text():
    script_content = script_text.get("1.0", "end")
    script_text.delete("1.0", "end")
    script_text.insert("1.0", script_content)


def run_script():
    script = script_text.get("1.0", "end-1c")
    #print(script)
    arguments = entry_arguments_entry.get()
    generate_stdout = generate_stdin.get()
    generate_stderr = see_stderr.get()

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


def execute_once():
    hour = hour_entry.get()
    minute = minute_entry.get()

    if validate_time(hour, minute):
        time_str = f"{hour}:{minute}"
        messagebox.showinfo("Execute Once", f"Scheduling script to run at {time_str} (HH:MM)")

        # Prepare the 'at' command
        script = script_text.get("1.0", "end-1c")
        arguments = entry_arguments_entry.get()
        command = f"echo '{script} {arguments}' | at {time_str}"

        # Execute the 'at' command
        try:
            subprocess.run(command, shell=True, check=True)
            messagebox.showinfo("Execute Once", f"Script scheduled to run at {time_str} successfully.")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Execute Once", f"Error scheduling script:\n{e}")


def program_daily():
    hour = hour_entry.get()
    minute = minute_entry.get()

    if validate_time(hour, minute):
        time_str = f"{hour}:{minute}"
        messagebox.showinfo("Program Daily", f"Scheduling script to run daily at {time_str} (HH:MM)")

        # Get the user's crontab
        cron = CronTab(user=True)

        # Create a new cron job
        job = cron.new(command='python script.py')  # Replace 'script.py' with the actual script file name

        # Set the schedule to run daily at the specified time
        job.setall(f"{minute} {hour} * * *")

        # Write the cron job to the crontab
        cron.write()

        messagebox.showinfo("Program Daily", f"Script scheduled to run daily at {time_str} successfully.")


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
