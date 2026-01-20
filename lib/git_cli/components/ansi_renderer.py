import re
from tkinter import END


class AnsiRenderer:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.define_ansi_tags(text_widget)

    def define_ansi_tags(self, text_widget):
        tags = {
            "added": {"background": "light green", "foreground": "black"},
            "removed": {"background": "light coral", "foreground": "black"},
            "changed": {"foreground": "cyan"},
            "commit": {"foreground": "yellow"},
            "author": {"foreground": "green"},
            "date": {"foreground": "magenta"},
            "error": {"foreground": "red"},
            "green": {"foreground": "green"},
            "yellow": {"foreground": "yellow"},
            "blue": {"foreground": "blue"},
            "magenta": {"foreground": "magenta"},
            "cyan": {"foreground": "cyan"},
            "modified": {"foreground": "orange"},
            "modified_multiple": {"foreground": "dark orange"},
            "untracked": {"foreground": "red"},
            "deleted": {"foreground": "red"},
            "renamed": {"foreground": "blue"},
            "copied": {"foreground": "purple"},
            "unmerged": {"foreground": "yellow"},
            "ignored": {"foreground": "gray"},
            "addition": {"foreground": "green"},
            "deletion": {"foreground": "red"},
            "info": {"foreground": "blue"}
        }

        for tag, config in tags.items():
            text_widget.tag_configure(tag, **config)

    def apply_ansi_styles(self, text_widget, text):
        ansi_escape = re.compile("\\x1B\\[([0-9;]*[mK])")
        lines = text.splitlines()
        for line in lines:
            cleaned_line = ansi_escape.sub("", line)
            if cleaned_line.startswith("commit "):
                text_widget.insert("end", "commit ", "commit")
                text_widget.insert("end", cleaned_line[7:] + "\n")
            elif cleaned_line.startswith("Author: "):
                text_widget.insert("end", "Author: ", "author")
                text_widget.insert("end", cleaned_line[8:] + "\n")
            elif cleaned_line.startswith("Date: "):
                text_widget.insert("end", "Date: ", "date")
                text_widget.insert("end", cleaned_line[6:] + "\n")
            elif (cleaned_line.startswith("+ ") or cleaned_line.startswith("+")
                  and not cleaned_line.startswith("+++")):
                text_widget.insert("end", cleaned_line + "\n", "added")
            elif (cleaned_line.startswith("- ") or cleaned_line.startswith("-")
                  and not cleaned_line.startswith("---")):
                text_widget.insert("end", cleaned_line + "\n", "removed")
            elif cleaned_line.startswith("@@ "):
                parts = cleaned_line.split("@@")
                if len(parts) >= 3:
                    text_widget.insert("end", parts[0])
                    text_widget.insert("end", "@@" + parts[1] + "@@", "changed")
                    text_widget.insert("end", "".join(parts[2:]) + "\n")
                else:
                    text_widget.insert("end", cleaned_line + "\n")
            else:
                text_widget.insert("end", cleaned_line + "\n")

    def insert_ansi_text(self, widget, text, tag=""):
        ansi_escape = re.compile("\\x1B\\[(?P<code>\\d+(;\\d+)*)m")
        segments = ansi_escape.split(text)
        tag = None
        for i, segment in enumerate(segments):
            if i % 2 == 0:
                widget.insert(END, segment, tag)
            else:
                codes = list(map(int, segment.split(";")))
                tag = self.get_ansi_tag(codes)
                if tag:
                    widget.tag_configure(tag, **self.get_ansi_style(tag))

    def get_ansi_tag(self, codes):
        fg_map = {
            30: "black",
            31: "red",
            32: "green",
            33: "yellow",
            34: "blue",
            35: "magenta",
            36: "cyan",
            37: "white",
            90: "bright_black",
            91: "bright_red",
            92: "bright_green",
            93: "bright_yellow",
            94: "bright_blue",
            95: "bright_magenta",
            96: "bright_cyan",
            97: "bright_white",
        }
        bg_map = {
            40: "bg_black",
            41: "bg_red",
            42: "bg_green",
            43: "bg_yellow",
            44: "bg_blue",
            45: "bg_magenta",
            46: "bg_cyan",
            47: "bg_white",
            100: "bg_bright_black",
            101: "bg_bright_red",
            102: "bg_bright_green",
            103: "bg_bright_yellow",
            104: "bg_bright_blue",
            105: "bg_bright_magenta",
            106: "bg_bright_cyan",
            107: "bg_bright_white",
        }
        styles = []
        for code in codes:
            if code in fg_map:
                styles.append(fg_map[code])
            elif code in bg_map:
                styles.append(bg_map[code])
            elif code == 1:
                styles.append("bold")
            elif code == 4:
                styles.append("underline")
        return "_".join(styles) if styles else None

    def get_ansi_style(self, tag):
        styles = {
            "black": {"foreground": "black"},
            "red": {"foreground": "red"},
            "green": {"foreground": "green"},
            "yellow": {"foreground": "yellow"},
            "blue": {"foreground": "blue"},
            "magenta": {"foreground": "magenta"},
            "cyan": {"foreground": "cyan"},
            "white": {"foreground": "white"},
            "bright_black": {"foreground": "gray"},
            "bright_red": {"foreground": "lightcoral"},
            "bright_green": {"foreground": "lightgreen"},
            "bright_yellow": {"foreground": "lightyellow"},
            "bright_blue": {"foreground": "lightblue"},
            "bright_magenta": {"foreground": "violet"},
            "bright_cyan": {"foreground": "lightcyan"},
            "bright_white": {"foreground": "white"},
            "bg_black": {"background": "black"},
            "bg_red": {"background": "red"},
            "bg_green": {"background": "green"},
            "bg_yellow": {"background": "yellow"},
            "bg_blue": {"background": "blue"},
            "bg_magenta": {"background": "magenta"},
            "bg_cyan": {"background": "cyan"},
            "bg_white": {"background": "white"},
            "bg_bright_black": {"background": "gray"},
            "bg_bright_red": {"background": "lightcoral"},
            "bg_bright_green": {"background": "lightgreen"},
            "bg_bright_yellow": {"background": "lightyellow"},
            "bg_bright_blue": {"background": "lightblue"},
            "bg_bright_magenta": {"background": "violet"},
            "bg_bright_cyan": {"background": "lightcyan"},
            "bg_bright_white": {"background": "white"},
            "bold": {"font": ("TkDefaultFont", 10, "bold")},
            "underline": {"font": ("TkDefaultFont", 10, "underline")},
        }
        style = {}
        for part in tag.split("_"):
            if part in styles:
                style.update(styles[part])
        return style
