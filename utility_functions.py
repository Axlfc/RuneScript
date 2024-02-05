import tkinter
from tkinter import END, messagebox, colorchooser

from tk_utils import text, all_fonts, all_size, fontColor


def bold(event=None):
    """
        Toggles bold formatting on the entire text in a text widget.

        This function applies or removes bold formatting to all text in the text widget. If any text is already
        bold, it removes the bold formatting. Otherwise, it makes the entire text bold.

        Parameters:
        event (Event, optional): The event object (not used in the function, but necessary for binding).

        Returns:
        None
    """
    current_tags = text.tag_names()
    if "bold" in current_tags:
        # first char is bold, so unbold the range
        text.tag_delete("bold", 1.0, END)
    else:
        # first char is normal, so bold the whole selection
        text.tag_add("bold", 1.0, END)
    make_tag()


def italic(event=None):
    """
        Toggles italic formatting on the entire text in a text widget.

        This function applies or removes italic formatting to all text in the text widget. If any text is already
        italic, it switches to normal. Otherwise, it makes the entire text italic.

        Parameters:
        event (Event, optional): The event object (not used in the function, but necessary for binding).

        Returns:
        None
    """
    current_tags = text.tag_names()
    if "italic" in current_tags:
        text.tag_add("roman", 1.0, END)
        text.tag_delete("italic", 1.0, END)
    else:
        text.tag_add("italic", 1.0, END)
    make_tag()


def underline(event=None):
    """
        Toggles underline formatting on the entire text in a text widget.

        This function applies or removes underline formatting to all text in the text widget. If any text is
        already underlined, it removes the underline. Otherwise, it underlines the entire text.

        Parameters:
        event (Event, optional): The event object (not used in the function, but necessary for binding).

        Returns:
        None
    """
    current_tags = text.tag_names()
    if "underline" in current_tags:
        text.tag_delete("underline", 1.0, END)
    else:
        text.tag_add("underline", 1.0, END)
    make_tag()


def strike():
    """
        Toggles strikethrough formatting on the entire text in a text widget.

        This function applies or removes strikethrough formatting to all text in the text widget. If any text
        is already stricken through, it removes the strikethrough. Otherwise, it applies strikethrough to the
        entire text.

        Parameters:
        None

        Returns:
        None
    """
    current_tags = text.tag_names()
    if "overstrike" in current_tags:
        text.tag_delete("overstrike", "1.0", END)

    else:
        text.tag_add("overstrike", 1.0, END)

    make_tag()


def highlight():
    """
        Applies background color to the entire text in a text widget.

        This function opens a color chooser dialog and applies the selected color as the background color to all
        text in the text widget.

        Parameters:
        None

        Returns:
        None
    """
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


def align_center(event=None):
    """
        Aligns the entire text in a text widget to the center.

        This function centers all the text in the text widget. It removes any other alignment tags before
        applying the center alignment.

        Parameters:
        event (Event, optional): The event object (not used in the function, but necessary for binding).

        Returns:
        None
    """
    remove_align_tags()
    text.tag_configure("center", justify='center')
    text.tag_add("center", 1.0, "end")


def align_justify():
    remove_align_tags()


def align_left(event=None):
    remove_align_tags()
    text.tag_configure("left", justify='left')
    text.tag_add("left", 1.0, "end")


def align_right(event=None):
    remove_align_tags()
    text.tag_configure("right", justify='right')
    text.tag_add("right", 1.0, "end")


def change_font(event):
    """
        Changes the font family of the entire text in a text widget.

        This function changes the font family based on the selection from a dropdown or similar widget. The
        global variable 'current_font_family' is updated with the new font family.

        Parameters:
        event (Event): The event object (used for binding to a widget event).

        Returns:
        None
    """
    f = all_fonts.get()
    global current_font_family
    current_font_family = f
    make_tag()


def change_size(event):
    """
        Changes the font size of the entire text in a text widget.

        This function changes the font size based on the selection from a dropdown or similar widget. The global
        variable 'current_font_size' is updated with the new font size.

        Parameters:
        event (Event): The event object (used for binding to a widget event).

        Returns:
        None
    """
    sz = int(all_size.get())
    global current_font_size
    current_font_size = sz
    make_tag()


def make_tag():
    """
        Applies combined text formatting based on the current tags in a text widget.

        This function checks for the presence of formatting tags (bold, italic, underline, overstrike) and applies
        them together to the entire text in the text widget. It also applies the current font family and size.

        Parameters:
        None

        Returns:
        None
    """
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


def remove_align_tags():
    """
        Removes all alignment tags from a text widget.

        This function removes any existing alignment tags (center, left, right) from the text widget, effectively
        resetting the alignment.

        Parameters:
        None

        Returns:
        None
    """
    all_tags = text.tag_names(index=None)
    if "center" in all_tags:
        text.tag_remove("center", "1.0", END)
    if "left" in all_tags:
        text.tag_remove("left", "1.0", END)
    if "right" in all_tags:
        text.tag_remove("right", "1.0", END)


def validate_time(hour, minute):
    """
        Validates the given hour and minute to ensure they form a valid time.

        This function checks if the provided hour and minute values form a valid time (HH:MM format). It displays
        an error message if the time is invalid.

        Parameters:
        hour (str or int): The hour part of the time.
        minute (str or int): The minute part of the time.

        Returns:
        bool: True if the time is valid, False otherwise.
    """
    try:
        hour = int(hour)
        minute = int(minute)
        if not (0 <= hour < 24) or not (0 <= minute < 60):
            raise ValueError
        return True
    except ValueError:
        messagebox.showerror("Invalid Time", "Please enter a valid time in HH:MM format.")
        return False

