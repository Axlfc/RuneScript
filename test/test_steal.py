#!/usr/bin/python3

from tkinter import *
import tkinter.filedialog as filedialog  # filedialog allows user to select where they want to save the file.
import tkinter.font
import tkinter.colorchooser as colorchooser
import tkinter.ttk
import tkinter.simpledialog as simpledialog
import tkinter.messagebox as messagebox
from PIL import Image, ImageTk  # sudo apt-get install python3-pil python3-pil.imagetk
import os
import tkinter.messagebox as messagebox
from tkinter.filedialog import askopenfilename

from tk_utils import *

# creating the root of the window.
root = Tk()
root.title("Untitled* - Script Editor")
root.geometry("600x550")

# setting resizable window
root.resizable(True, True)
root.minsize(600, 550)  # minimimum size possible

# --------------- METHODS ---------------- #

# MAIN MENU METHODS

file_name = ""  # Current file name.
current_font_family = "Liberation Mono"
current_font_size = 12
fontColor = '#000000'
fontBackground = '#FFFFFF'


# ------------- CREATING - MENUBAR AND ITS MENUS, TOOLS BAR, FORMAT BAR, STATUS BAR AND TEXT AREA -----------#

# TOOLBAR
toolbar = Frame(root, pady=2)

# TOOLBAR BUTTONS
# new
new_button = Button(name="toolbar_b2", borderwidth=1, command=new, width=20, height=20)
photo_new = Image.open("../icons/new.png")
photo_new = photo_new.resize((18, 18), Image.ANTIALIAS)
image_new = ImageTk.PhotoImage(photo_new)
new_button.config(image=image_new)
new_button.pack(in_=toolbar, side="left", padx=4, pady=4)

# save
save_button = Button(name="toolbar_b1", borderwidth=1, command=save, width=20, height=20)
photo_save = Image.open("../icons/save.png")
photo_save = photo_save.resize((18, 18), Image.ANTIALIAS)
image_save = ImageTk.PhotoImage(photo_save)
save_button.config(image=image_save)
save_button.pack(in_=toolbar, side="left", padx=4, pady=4)

# open
open_button = Button(name="toolbar_b3", borderwidth=1, command=open_file, width=20, height=20)
photo_open = Image.open("../icons/open.png")
photo_open = photo_open.resize((18, 18), Image.ANTIALIAS)
image_open = ImageTk.PhotoImage(photo_open)
open_button.config(image=image_open)
open_button.pack(in_=toolbar, side="left", padx=4, pady=4)

# copy
copy_button = Button(name="toolbar_b4", borderwidth=1, command=copy, width=20, height=20)
photo_copy = Image.open("../icons/copy.png")
photo_copy = photo_copy.resize((18, 18), Image.ANTIALIAS)
image_copy = ImageTk.PhotoImage(photo_copy)
copy_button.config(image=image_copy)
copy_button.pack(in_=toolbar, side="left", padx=4, pady=4)

# cut
cut_button = Button(name="toolbar_b5", borderwidth=1, command=cut, width=20, height=20)
photo_cut = Image.open("../icons/cut.png")
photo_cut = photo_cut.resize((18, 18), Image.ANTIALIAS)
image_cut = ImageTk.PhotoImage(photo_cut)
cut_button.config(image=image_cut)
cut_button.pack(in_=toolbar, side="left", padx=4, pady=4)

# paste
paste_button = Button(name="toolbar_b6", borderwidth=1, command=paste, width=20, height=20)
photo_paste = Image.open("../icons/paste.png")
photo_paste = photo_paste.resize((18, 18), Image.ANTIALIAS)
image_paste = ImageTk.PhotoImage(photo_paste)
paste_button.config(image=image_paste)
paste_button.pack(in_=toolbar, side="left", padx=4, pady=4)

# redo
redo_button = Button(name="toolbar_b7", borderwidth=1, command=redo, width=20, height=20)
photo_redo = Image.open("../icons/redo.png")
photo_redo = photo_redo.resize((18, 18), Image.ANTIALIAS)
image_redo = ImageTk.PhotoImage(photo_redo)
redo_button.config(image=image_redo)
redo_button.pack(in_=toolbar, side="left", padx=4, pady=4)

# undo
undo_button = Button(name="toolbar_b8", borderwidth=1, command=undo, width=20, height=20)
photo_undo = Image.open("../icons/undo.png")
photo_undo = photo_undo.resize((18, 18), Image.ANTIALIAS)
image_undo = ImageTk.PhotoImage(photo_undo)
undo_button.config(image=image_undo)
undo_button.pack(in_=toolbar, side="left", padx=4, pady=4)

# find
find_button = Button(name="toolbar_b9", borderwidth=1, command=find_text, width=20, height=20)
photo_find = Image.open("../icons/find.png")
photo_find = photo_find.resize((18, 18), Image.ANTIALIAS)
image_find = ImageTk.PhotoImage(photo_find)
find_button.config(image=image_find)
find_button.pack(in_=toolbar, side="left", padx=4, pady=4)

# FORMATTING BAR
formattingbar = Frame(root, padx=2, pady=2)

# FORMATTING BAR COMBOBOX - FOR FONT AND SIZE
# font combobox
all_fonts = StringVar()
font_menu = tkinter.ttk.Combobox(formattingbar, textvariable=all_fonts, state="readonly")
font_menu.pack(in_=formattingbar, side="left", padx=4, pady=4)
font_menu['values'] = (
'Courier', 'Helvetica', 'Liberation Mono', 'OpenSymbol', 'Century Schoolbook L', 'DejaVu Sans Mono', 'Ubuntu Condensed',
'Ubuntu Mono', 'Lohit Punjabi', 'Mukti Narrow', 'Meera', 'Symbola', 'Abyssinica SIL')
font_menu.bind('<<ComboboxSelected>>', change_font)
font_menu.current(2)

# size combobox
all_size = StringVar()
size_menu = tkinter.ttk.Combobox(formattingbar, textvariable=all_size, state='readonly', width=5)
size_menu.pack(in_=formattingbar, side="left", padx=4, pady=4)
size_menu['values'] = ('10', '12', '14', '16', '18', '20', '22', '24', '26', '28', '30')
size_menu.bind('<<ComboboxSelected>>', change_size)
size_menu.current(1)

# FORMATBAR BUTTONS
# bold
bold_button = Button(name="formatbar_b1", borderwidth=1, command=bold, width=20, height=20, pady=10, padx=10)
photo_bold = Image.open("../icons/bold.png")
photo_bold = photo_bold.resize((18, 18), Image.ANTIALIAS)
image_bold = ImageTk.PhotoImage(photo_bold)
bold_button.config(image=image_bold)
bold_button.pack(in_=formattingbar, side="left", padx=4, pady=4)

# italic
italic_button = Button(name="formatbar_b2", borderwidth=1, command=italic, width=20, height=20)
photo_italic = Image.open("../icons/italic.png")
photo_italic = photo_italic.resize((18, 18), Image.ANTIALIAS)
image_italic = ImageTk.PhotoImage(photo_italic)
italic_button.config(image=image_italic)
italic_button.pack(in_=formattingbar, side="left", padx=4, pady=4)

# underline
underline_button = Button(name="formatbar_b3", borderwidth=1, command=underline, width=20, height=20)
photo_underline = Image.open("../icons/underline.png")
photo_underline = photo_underline.resize((18, 18), Image.ANTIALIAS)
image_underline = ImageTk.PhotoImage(photo_underline)
underline_button.config(image=image_underline)
underline_button.pack(in_=formattingbar, side="left", padx=4, pady=4)

# strike
strike_button = Button(name="formatbar_b4", borderwidth=1, command=strike, width=20, height=20)
photo_strike = Image.open("../icons/strike.png")
photo_strike = photo_strike.resize((18, 18), Image.ANTIALIAS)
image_strike = ImageTk.PhotoImage(photo_strike)
strike_button.config(image=image_strike)
strike_button.pack(in_=formattingbar, side="left", padx=4, pady=4)

# font_color
font_color_button = Button(name="formatbar_b5", borderwidth=1, command=change_color, width=20, height=20)
photo_font_color = Image.open("../icons/font-color.png")
photo_font_color = photo_font_color.resize((18, 18), Image.ANTIALIAS)
image_font_color = ImageTk.PhotoImage(photo_font_color)
font_color_button.config(image=image_font_color)
font_color_button.pack(in_=formattingbar, side="left", padx=4, pady=4)

# highlight
highlight_button = Button(name="formatbar_b6", borderwidth=1, command=highlight, width=20, height=20)
photo_highlight = Image.open("../icons/highlight.png")
photo_highlight = photo_highlight.resize((18, 18), Image.ANTIALIAS)
image_highlight = ImageTk.PhotoImage(photo_highlight)
highlight_button.config(image=image_highlight)
highlight_button.pack(in_=formattingbar, side="left", padx=4, pady=4)

# align_center
align_center_button = Button(name="formatbar_b7", borderwidth=1, command=align_center, width=20, height=20)
photo_align_center = Image.open("../icons/align-center.png")
photo_align_center = photo_align_center.resize((18, 18), Image.ANTIALIAS)
image_align_center = ImageTk.PhotoImage(photo_align_center)
align_center_button.config(image=image_align_center)
align_center_button.pack(in_=formattingbar, side="left", padx=4, pady=4)

# align_justify
align_justify_button = Button(name="formatbar_b8", borderwidth=1, command=align_justify, width=20, height=20)
photo_align_justify = Image.open("../icons/align-justify.png")
photo_align_justify = photo_align_justify.resize((18, 18), Image.ANTIALIAS)
image_align_justify = ImageTk.PhotoImage(photo_align_justify)
align_justify_button.config(image=image_align_justify)
align_justify_button.pack(in_=formattingbar, side="left", padx=4, pady=4)

# align_left
align_left_button = Button(name="formatbar_b9", borderwidth=1, command=align_left, width=20, height=20)
photo_align_left = Image.open("../icons/align-left.png")
photo_align_left = photo_align_left.resize((18, 18), Image.ANTIALIAS)
image_align_left = ImageTk.PhotoImage(photo_align_left)
align_left_button.config(image=image_align_left)
align_left_button.pack(in_=formattingbar, side="left", padx=4, pady=4)

# align_right
align_right_button = Button(name="formatbar_b10", borderwidth=1, command=align_right, width=20, height=20)
photo_align_right = Image.open("../icons/align-right.png")
photo_align_right = photo_align_right.resize((18, 18), Image.ANTIALIAS)
image_align_right = ImageTk.PhotoImage(photo_align_right)
align_right_button.config(image=image_align_right)
align_right_button.pack(in_=formattingbar, side="left", padx=4, pady=4)

# STATUS BAR
status = Label(root, text="", bd=1, relief=SUNKEN, anchor=W)

# CREATING TEXT AREA - FIRST CREATED A FRAME AND THEN APPLIED TEXT OBJECT TO IT.
text_frame = Frame(root, borderwidth=1, relief="sunken")
text = Text(wrap="word", font=("Liberation Mono", 12), background="white", borderwidth=0, highlightthickness=0,
            undo=True)
text.pack(in_=text_frame, side="left", fill="both", expand=True)  # pack text object.

# PACK TOOLBAR, FORMATBAR, STATUSBAR AND TEXT FRAME.
toolbar.pack(side="top", fill="x")
formattingbar.pack(side="top", fill="x")
status.pack(side="bottom", fill="x")
text_frame.pack(side="bottom", fill="both", expand=True)
text.focus_set()

# MENUBAR CREATION

menu = Menu(root)
root.config(menu=menu)

# File menu.
file_menu = Menu(menu)
menu.add_cascade(label="File", menu=file_menu, underline=0)

file_menu.add_command(label="New", command=new, compound='left', image=image_new, accelerator='Ctrl+N',
                      underline=0)  # command passed is here the method defined above.
file_menu.add_command(label="Open", command=open_file, compound='left', image=image_open, accelerator='Ctrl+O',
                      underline=0)
file_menu.add_separator()
file_menu.add_command(label="Save", command=save, compound='left', image=image_save, accelerator='Ctrl+S', underline=0)
file_menu.add_command(label="Save As", command=save_as, accelerator='Ctrl+Shift+S', underline=1)
file_menu.add_command(label="Rename", command=rename, accelerator='Ctrl+Shift+R', underline=0)
file_menu.add_separator()
file_menu.add_command(label="Close", command=close, accelerator='Alt+F4', underline=0)

# Edit Menu.
edit_menu = Menu(menu)
menu.add_cascade(label="Edit", menu=edit_menu, underline=0)

edit_menu.add_command(label="Undo", command=undo, compound='left', image=image_undo, accelerator='Ctrl+Z', underline=0)
edit_menu.add_command(label="Redo", command=redo, compound='left', image=image_redo, accelerator='Ctrl+Y', underline=0)
edit_menu.add_separator()
edit_menu.add_command(label="Cut", command=cut, compound='left', image=image_cut, accelerator='Ctrl+X', underline=0)
edit_menu.add_command(label="Copy", command=copy, compound='left', image=image_copy, accelerator='Ctrl+C', underline=1)
edit_menu.add_command(label="Paste", command=paste, compound='left', image=image_paste, accelerator='Ctrl+P',
                      underline=0)
edit_menu.add_command(label="Delete", command=delete, underline=0)
edit_menu.add_separator()
edit_menu.add_command(label="Select All", command=select_all, accelerator='Ctrl+A', underline=0)
edit_menu.add_command(label="Clear All", command=delete_all, underline=6)

# Tool Menu
tool_menu = Menu(menu)
menu.add_cascade(label="Tools", menu=tool_menu, underline=0)

tool_menu.add_command(label="Change Color", command=change_color)
tool_menu.add_command(label="Search", command=find_text, compound='left', image=image_find, accelerator='Ctrl+F')


# Help Menu
def about(event=None):
    messagebox.showinfo("About",
                        "Text Editor\nCreated in Python using Tkinter\nCopyright with Amandeep and Harmanpreet, 2017")


help_menu = Menu(menu)
menu.add_cascade(label="Help", menu=help_menu, underline=0)
help_menu.add_command(label="About", command=about, accelerator='Ctrl+H', underline=0)

# ----- BINDING ALL KEYBOARD SHORTCUTS ---------- #
text.bind('<Control-n>', new)
text.bind('<Control-N>', new)

text.bind('<Control-o>', open_file)
text.bind('<Control-O>', open_file)

text.bind('<Control-s>', save)
text.bind('<Control-S>', save)

text.bind('<Control-Shift-s>', save_as)
text.bind('<Control-Shift-S>', save_as)

text.bind('<Control-r>', rename)
text.bind('<Control-R>', rename)

text.bind('<Alt-F4>', close)
text.bind('<Alt-F4>', close)

text.bind('<Control-x>', cut)
text.bind('<Control-X>', cut)

text.bind('<Control-c>', copy)
text.bind('<Control-C>', copy)

text.bind('<Control-p>', paste)
text.bind('<Control-P>', paste)

text.bind('<Control-a>', select_all)
text.bind('<Control-A>', select_all)

text.bind('<Control-h>', about)
text.bind('<Control-H>', about)

text.bind('<Control-f>', find_text)
text.bind('<Control-F>', find_text)

text.bind('<Control-Shift-i>', italic)
text.bind('<Control-Shift-I>', italic)

text.bind('<Control-b>', bold)
text.bind('<Control-B>', bold)

text.bind('<Control-u>', underline)
text.bind('<Control-U>', underline)

text.bind('<Control-Shift-l>', align_left)
text.bind('<Control-Shift-L>', align_left)

text.bind('<Control-Shift-r>', align_right)
text.bind('<Control-Shift-R>', align_right)

text.bind('<Control-Shift-c>', align_center)
text.bind('<Control-Shift-C>', align_center)


# ---------- SETTING EVENTS FOR THE STATUS BAR -------------- #
def on_enter(event, str):
    status.configure(text=str)


def on_leave(event):
    status.configure(text="")


new_button.bind("<Enter>", lambda event, str="New, Command - Ctrl+N": on_enter(event, str))
new_button.bind("<Leave>", on_leave)

save_button.bind("<Enter>", lambda event, str="Save, Command - Ctrl+S": on_enter(event, str))
save_button.bind("<Leave>", on_leave)

open_button.bind("<Enter>", lambda event, str="Open, Command - Ctrl+O": on_enter(event, str))
open_button.bind("<Leave>", on_leave)

copy_button.bind("<Enter>", lambda event, str="Copy, Command - Ctrl+C": on_enter(event, str))
copy_button.bind("<Leave>", on_leave)

cut_button.bind("<Enter>", lambda event, str="Cut, Command - Ctrl+X": on_enter(event, str))
cut_button.bind("<Leave>", on_leave)

paste_button.bind("<Enter>", lambda event, str="Paste, Command - Ctrl+P": on_enter(event, str))
paste_button.bind("<Leave>", on_leave)

undo_button.bind("<Enter>", lambda event, str="Undo, Command - Ctrl+Z": on_enter(event, str))
undo_button.bind("<Leave>", on_leave)

redo_button.bind("<Enter>", lambda event, str="Redo, Command - Ctrl+Y": on_enter(event, str))
redo_button.bind("<Leave>", on_leave)

find_button.bind("<Enter>", lambda event, str="Find, Command - Ctrl+F": on_enter(event, str))
find_button.bind("<Leave>", on_leave)

bold_button.bind("<Enter>", lambda event, str="Bold, Command - Ctrl+B": on_enter(event, str))
bold_button.bind("<Leave>", on_leave)

italic_button.bind("<Enter>", lambda event, str="Italic, Command - Ctrl+Shift+I": on_enter(event, str))
italic_button.bind("<Leave>", on_leave)

underline_button.bind("<Enter>", lambda event, str="Underline, Command - Ctrl+U": on_enter(event, str))
underline_button.bind("<Leave>", on_leave)

align_justify_button.bind("<Enter>", lambda event, str="Justify": on_enter(event, str))
align_justify_button.bind("<Leave>", on_leave)

align_left_button.bind("<Enter>", lambda event, str="Align Left, Command - Control-Shift-L": on_enter(event, str))
align_left_button.bind("<Leave>", on_leave)

align_right_button.bind("<Enter>", lambda event, str="Align Right, Command - Control-Shift-R": on_enter(event, str))
align_right_button.bind("<Leave>", on_leave)

align_center_button.bind("<Enter>", lambda event, str="Align Center, Command - Control-Shift-C": on_enter(event, str))
align_center_button.bind("<Leave>", on_leave)

strike_button.bind("<Enter>", lambda event, str="Strike": on_enter(event, str))
strike_button.bind("<Leave>", on_leave)

font_color_button.bind("<Enter>", lambda event, str="Font Color": on_enter(event, str))
font_color_button.bind("<Leave>", on_leave)

highlight_button.bind("<Enter>", lambda event, str="Highlight": on_enter(event, str))
highlight_button.bind("<Leave>", on_leave)

strike_button.bind("<Enter>", lambda event, str="Strike": on_enter(event, str))
strike_button.bind("<Leave>", on_leave)

# MAINLOOP OF THE PROGRAM
root.mainloop()


