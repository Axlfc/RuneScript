#!/usr/bin/python3
from tkinter import Toplevel, Label, Button, Tk, StringVar, IntVar, Frame, Menu, Text, Entry, Listbox
from tkinter import END, INSERT, SEL_FIRST, SEL_LAST, SEL
from tkinter import ttk, scrolledtext, filedialog, simpledialog
import tkinter.messagebox as messagebox
import tkinter.colorchooser as colorchooser
from PIL import Image, ImageTk  # sudo apt-get install python3-pil python3-pil.imagetk
import tkinter
import os
from files import *


class MainWindow:

    def __init__(self):
        context_menu = None  # Define context_menu as a global variable

        # MAIN MENU METHODS

        file_name = ""  # Current file name.
        current_font_family = "Liberation Mono"
        current_font_size = 12
        fontColor = '#000000'
        fontBackground = '#FFFFFF'

        new_name = ""  # Used for renaming the file

        is_modified = False  # Added is_modified variable

        new_name = ""  # Used for renaming the file

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

        script_text = scrolledtext.ScrolledText(root, wrap="word", height=20, width=60)
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

        # TOOLBAR BUTTONS
        # new
        new_button = Button(name="toolbar_b2", borderwidth=1, command=new, width=20, height=20)
        photo_new = Image.open("icons/new.png")
        photo_new = photo_new.resize((18, 18), Image.NEAREST)
        image_new = ImageTk.PhotoImage(photo_new)
        new_button.config(image=image_new)
        new_button.pack(in_=toolbar, side="left", padx=4, pady=4)

        # save
        save_button = Button(name="toolbar_b1", borderwidth=1, command=save, width=20, height=20)
        photo_save = Image.open("icons/save.png")
        photo_save = photo_save.resize((18, 18), Image.NEAREST)
        image_save = ImageTk.PhotoImage(photo_save)
        save_button.config(image=image_save)
        save_button.pack(in_=toolbar, side="left", padx=4, pady=4)

        # open
        open_button = Button(name="toolbar_b3", borderwidth=1, command=open_file, width=20, height=20)
        photo_open = Image.open("icons/open.png")
        photo_open = photo_open.resize((18, 18), Image.NEAREST)
        image_open = ImageTk.PhotoImage(photo_open)
        open_button.config(image=image_open)
        open_button.pack(in_=toolbar, side="left", padx=4, pady=4)

        # copy
        copy_button = Button(name="toolbar_b4", borderwidth=1, command=copy, width=20, height=20)
        photo_copy = Image.open("icons/copy.png")
        photo_copy = photo_copy.resize((18, 18), Image.NEAREST)
        image_copy = ImageTk.PhotoImage(photo_copy)
        copy_button.config(image=image_copy)
        copy_button.pack(in_=toolbar, side="left", padx=4, pady=4)

        # cut
        cut_button = Button(name="toolbar_b5", borderwidth=1, command=cut, width=20, height=20)
        photo_cut = Image.open("icons/cut.png")
        photo_cut = photo_cut.resize((18, 18), Image.NEAREST)
        image_cut = ImageTk.PhotoImage(photo_cut)
        cut_button.config(image=image_cut)
        cut_button.pack(in_=toolbar, side="left", padx=4, pady=4)

        # paste
        paste_button = Button(name="toolbar_b6", borderwidth=1, command=paste, width=20, height=20)
        photo_paste = Image.open("icons/paste.png")
        photo_paste = photo_paste.resize((18, 18), Image.NEAREST)
        image_paste = ImageTk.PhotoImage(photo_paste)
        paste_button.config(image=image_paste)
        paste_button.pack(in_=toolbar, side="left", padx=4, pady=4)

        # duplicate
        duplicate_button = Button(name="toolbar_b7", borderwidth=1, command=paste, width=20, height=20)
        photo_duplicate = Image.open("icons/duplicate.png")
        photo_duplicate = photo_paste.resize((18, 18), Image.NEAREST)
        image_duplicate = ImageTk.PhotoImage(photo_paste)
        duplicate_button.config(image=image_duplicate)
        duplicate_button.pack(in_=toolbar, side="left", padx=4, pady=4)

        # redo
        redo_button = Button(name="toolbar_b8", borderwidth=1, command=redo, width=20, height=20)
        photo_redo = Image.open("icons/redo.png")
        photo_redo = photo_redo.resize((18, 18), Image.NEAREST)
        image_redo = ImageTk.PhotoImage(photo_redo)
        redo_button.config(image=image_redo)
        redo_button.pack(in_=toolbar, side="left", padx=4, pady=4)

        # undo
        undo_button = Button(name="toolbar_b9", borderwidth=1, command=undo, width=20, height=20)
        photo_undo = Image.open("icons/undo.png")
        photo_undo = photo_undo.resize((18, 18), Image.NEAREST)
        image_undo = ImageTk.PhotoImage(photo_undo)
        undo_button.config(image=image_undo)
        undo_button.pack(in_=toolbar, side="left", padx=4, pady=4)

        # find
        find_button = Button(name="toolbar_b10", borderwidth=1, command=find_text, width=20, height=20)
        photo_find = Image.open("icons/find.png")
        photo_find = photo_find.resize((18, 18), Image.NEAREST)
        image_find = ImageTk.PhotoImage(photo_find)
        find_button.config(image=image_find)
        find_button.pack(in_=toolbar, side="left", padx=4, pady=4)

        at_window = None
        crontab_window = None

        # root.title("Untitled* - Script Editor")
        root.title("Scripts Editor")
        root.geometry("600x800")

        # setting resizable window
        root.resizable(True, True)
        root.minsize(600, 800)  # minimimum size possible

        is_modified = False

        create_menu()

        create_directory_line()

        create_open_script_line()

        create_content_file_window()

        # Open first text file if exists when changing directory
        open_first_text_file(os.getcwd())

        create_arguments_lines()

        create_immediately_run_line()

        create_execute_in_line()

        create_execute_one_time_with_format()

        create_program_daily_with_format()

        root.grid_rowconfigure(2, weight=1)
        root.columnconfigure(0, weight=1)

        root.mainloop()
