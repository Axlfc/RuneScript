from crontab import CronTab
import subprocess
import tempfile
from time import sleep
import os
import re

'''def save(event=None):
    global file_name
    if file_name == "":
        path = filedialog.asksaveasfilename()
        file_name = path
    root.title(file_name + " - Script Editor")
    write = open(file_name, mode='w')
    write.write(text.get("1.0", END))'''

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


'''
def open_first_text_file(directory):
    text_files = get_text_files(directory)
    if text_files:
        file_path = os.path.join(directory, text_files[0])
        open_file(file_path)
'''


def get_text_files(directory):
    text_files = []
    for file in os.listdir(directory):
        if file.endswith(".txt"):
            text_files.append(file)
    return text_files


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
