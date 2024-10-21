from tkinter import INSERT, SEL, END
from tkinter.constants import SEL_FIRST, SEL_LAST
from src.views.tk_utils import root, text, script_text

def duplicate(event=None):
    try:
        selected_text = text.get(SEL_FIRST, SEL_LAST)
        if selected_text:
            text.insert(INSERT, selected_text)
        else:
            print('No text is selected.')
    except Exception as e:
        print(f'No text is selected or other widget-specific error: {e}')

def undo():
    try:
        print('UNDO TRIGGERED')
        script_text.edit_undo()
    except Exception as e:
        print('ERROR:\t', e)

def redo():
    try:
        print('REDO TRIGGERED')
        script_text.edit_redo()
    except Exception as e:
        print('ERROR:\t', e)

def delete():
    text.delete(index1=SEL_FIRST, index2=SEL_LAST)

def select_all():
    text.tag_add('start', '1.0', 'end')

def cut():
    script_text.event_generate('<<Cut>>')

def copy():
    script_text.event_generate('<<Copy>>')

def paste():
    script_text.event_generate('<<Paste>>')

def duplicate():
    print('DUPLICAT')
    script_text.event_generate('<<Duplicate>>')