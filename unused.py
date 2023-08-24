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


'''def highlight():
    color = colorchooser.askcolor(initialcolor='white')
    color_rgb = color[1]
    global fontBackground
    fontBackground = color_rgb
    current_tags = text.tag_names()
    if "background_color_change" in current_tags:
        text.tag_delete("background_color_change", "1.0", END)
    else:
        text.tag_add("background_color_change", "1.0", END)
    make_tag()'''