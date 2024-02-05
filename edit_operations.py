from tkinter import INSERT, SEL, END
from tkinter.constants import SEL_FIRST, SEL_LAST

from tk_utils import root, text, script_text


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


def delete():
    text.delete(index1=SEL_FIRST, index2=SEL_LAST)