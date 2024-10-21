import tkinter
from tkinter import END, messagebox, colorchooser
from src.views.tk_utils import text, all_fonts, all_size, fontColor

def bold(event=None):
    current_tags = text.tag_names()
    if 'bold' in current_tags:
        text.tag_delete('bold', 1.0, END)
    else:
        text.tag_add('bold', 1.0, END)
    make_tag()

def italic(event=None):
    current_tags = text.tag_names()
    if 'italic' in current_tags:
        text.tag_add('roman', 1.0, END)
        text.tag_delete('italic', 1.0, END)
    else:
        text.tag_add('italic', 1.0, END)
    make_tag()

def underline(event=None):
    current_tags = text.tag_names()
    if 'underline' in current_tags:
        text.tag_delete('underline', 1.0, END)
    else:
        text.tag_add('underline', 1.0, END)
    make_tag()

def strike():
    current_tags = text.tag_names()
    if 'overstrike' in current_tags:
        text.tag_delete('overstrike', '1.0', END)
    else:
        text.tag_add('overstrike', 1.0, END)
    make_tag()

def highlight():
    color = colorchooser.askcolor(initialcolor='white')
    color_rgb = color[1]
    global fontBackground
    fontBackground = color_rgb
    current_tags = text.tag_names()
    if 'background_color_change' in current_tags:
        text.tag_delete('background_color_change', '1.0', END)
    else:
        text.tag_add('background_color_change', '1.0', END)
    make_tag()

def align_center(event=None):
    remove_align_tags()
    text.tag_configure('center', justify='center')
    text.tag_add('center', 1.0, 'end')

def align_justify():
    remove_align_tags()

def align_left(event=None):
    remove_align_tags()
    text.tag_configure('left', justify='left')
    text.tag_add('left', 1.0, 'end')

def align_right(event=None):
    remove_align_tags()
    text.tag_configure('right', justify='right')
    text.tag_add('right', 1.0, 'end')

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

def make_tag():
    current_tags = text.tag_names()
    if 'bold' in current_tags:
        weight = 'bold'
    else:
        weight = 'normal'
    if 'italic' in current_tags:
        slant = 'italic'
    else:
        slant = 'roman'
    if 'underline' in current_tags:
        underline = 1
    else:
        underline = 0
    if 'overstrike' in current_tags:
        overstrike = 1
    else:
        overstrike = 0
    big_font = tkinter.font.Font(text, text.cget('font'))
    big_font.configure(slant=slant, weight=weight, underline=underline, overstrike=overstrike, family=current_font_family, size=current_font_size)
    text.tag_config('BigTag', font=big_font, foreground=fontColor, background=fontBackground)
    if 'BigTag' in current_tags:
        text.tag_remove('BigTag', 1.0, END)
    text.tag_add('BigTag', 1.0, END)

def remove_align_tags():
    all_tags = text.tag_names(index=None)
    if 'center' in all_tags:
        text.tag_remove('center', '1.0', END)
    if 'left' in all_tags:
        text.tag_remove('left', '1.0', END)
    if 'right' in all_tags:
        text.tag_remove('right', '1.0', END)

def validate_time(hour, minute):
    try:
        hour = int(hour)
        minute = int(minute)
        if not 0 <= hour < 24 or not 0 <= minute < 60:
            raise ValueError
        return True
    except ValueError:
        messagebox.showerror('Invalid Time', 'Please enter a valid time in HH:MM format.')
        return False