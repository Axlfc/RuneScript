from tkinter import INSERT, SEL, END
from tkinter.constants import SEL_FIRST, SEL_LAST
from src.views.tk_utils import root, text, script_text


def duplicate(event=None):
    """ ""\"
    Duplicates the currently selected text.
    ""\" """
    try:
        selected_text = text.get(SEL_FIRST, SEL_LAST)
        if selected_text:
            text.insert(INSERT, selected_text)
        else:
            print("No text is selected.")
    except Exception as e:
        print(f"No text is selected or other widget-specific error: {e}")


def undo():
    """ ""\"
    Undoes the last action in the script text editor.

    This function reverts the last change made in the script text editor, typically used for undoing edits.

    Parameters:
    None

    Returns:
    None
    ""\" """
    try:
        print("UNDO TRIGGERED")
        script_text.edit_undo()
    except Exception as e:
        print("ERROR:\t", e)


def redo():
    """ ""\"
    Redoes the last undone action in the script text editor.

    If actions were previously undone using the undo function, this function allows redoing those actions.

    Parameters:
    None

    Returns:
    None
    ""\" """
    try:
        print("REDO TRIGGERED")
        script_text.edit_redo()
    except Exception as e:
        print("ERROR:\t", e)


def delete():
    """ ""\"
    Deletes the currently selected text in the editor.

    This function removes the text that is currently selected within the editor.

    Parameters:
    None

    Returns:
    None
    ""\" """
    text.delete(index1=SEL_FIRST, index2=SEL_LAST)


def select_all():
    """ ""\"
    select_all

    Args:
        None

    Returns:
        None: Description of return value.
    ""\" """
    text.tag_add("start", "1.0", "end")


def cut():
    """ ""\"
    Cuts the selected text from the script editor to the clipboard.

    This function removes the currently selected text from the document and places it on the clipboard,
    allowing it to be pasted elsewhere.

    Parameters:
    None

    Returns:
    None
    ""\" """
    script_text.event_generate("<<Cut>>")


def copy():
    """ ""\"
    Copies the selected text from the script editor to the clipboard.

    This function copies the currently selected text to the clipboard without removing it from the document.

    Parameters:
    None

    Returns:
    None
    ""\" """
    script_text.event_generate("<<Copy>>")


def paste():
    """ ""\"
    Pastes text from the clipboard into the script editor at the cursor's current location.

    This function inserts the contents of the clipboard into the document at the current cursor position.

    Parameters:
    None

    Returns:
    None
    ""\" """
    script_text.event_generate("<<Paste>>")


def duplicate():
    """ ""\"
    Duplicates the selected text in the script editor.

    This function creates a copy of the selected text and inserts it immediately after the current selection.

    Parameters:
    None

    Returns:
    None
    ""\" """
    print("DUPLICAT")
    script_text.event_generate("<<Duplicate>>")
