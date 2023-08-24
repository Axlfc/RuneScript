from tk_utils import *

def cut():
    set_modified_status(True)
    script_text.event_generate("<<Cut>>")


def copy():
    set_modified_status(True)
    script_text.event_generate("<<Copy>>")


def paste():
    set_modified_status(True)
    script_text.event_generate("<<Paste>>")


def duplicate():
    set_modified_status(True)
    script_text.event_generate("<<Duplicate>>")

