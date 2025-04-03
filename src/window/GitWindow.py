import subprocess
import re
import os
from tkinter import *
from tkinter import scrolledtext, Menu, Frame, Button, Entry, Label, Toplevel, Listbox, Text, SUNKEN, END, W

from src.views.tk_utils import my_font


class GitWindow:
    def __init__(self, repo_dir=None):
        self.repo_dir = repo_dir
        self.command_history = []
        self.history_pointer = [0]
        self.create_window()
        self.setup_ui()
        self.execute_command("status --porcelain -u")

    def create_window(self):
        self.terminal_window = Toplevel()
        self.terminal_window.title("Git Console")
        self.terminal_window.geometry("600x512")

        # Setup menubar
        self.menubar = Menu(self.terminal_window)
        self.terminal_window.config(menu=self.menubar)
        self.setup_git_menu()
        self.setup_branch_menu()

    def setup_ui(self):
        # Output text area
        self.output_text = scrolledtext.ScrolledText(self.terminal_window, height=20, width=80)
        self.output_text.pack(fill="both", expand=True)

        # Status bar
        self.status_bar = Label(self.terminal_window, text="Checking branch...", bd=1, relief=SUNKEN, anchor=W)
        self.status_bar.pack(side="top", fill="x")
        self.update_status()

        # Top frame with commit list
        self.setup_commit_list()

        # Button frame
        self.setup_button_frame()

        # Context menu
        self.setup_context_menu()

        # Define ANSI tags
        self.define_ansi_tags(self.output_text)

    def setup_git_menu(self):
        self.git_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Git", menu=self.git_menu)
        git_icons = {
            "status": "📊",
            "add": "➕",
            "commit": "💾",
            "push": "⬆️",
            "pull": "⬇️",
            "fetch": "🔄",
            "merge": "🔀",
            "branch": "🌿",
            "checkout": "✨",
            "reset": "⏮️",
            "stash": "📦",
        }
        for command, icon in git_icons.items():
            self.git_menu.add_command(
                label=f"{icon} {command.capitalize()}",
                command=lambda c=command: self.execute_command(c)
            )

    def setup_branch_menu(self):
        self.branch_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Branch", menu=self.branch_menu)
        self.populate_branch_menu()

    def setup_commit_list(self):
        top_frame = Frame(self.terminal_window)
        top_frame.pack(fill="both", expand=True)

        commit_scrollbar = Scrollbar(top_frame)
        commit_scrollbar.pack(side="right", fill="y")

        self.commit_list = Listbox(top_frame, yscrollcommand=commit_scrollbar.set)
        self.commit_list.pack(side="left", fill="both", expand=True)
        commit_scrollbar.config(command=self.commit_list.yview)

        self.commit_list.bind("<Button-3>", self.commit_list_context_menu)
        self.update_commit_list(self.commit_list)

    def setup_button_frame(self):
        button_frame = Frame(self.terminal_window)
        button_frame.pack(fill="both", expand=False)

        common_commands = ["commit", "push", "pull", "fetch"]
        git_icons = {"commit": "💾", "push": "⬆️", "pull": "⬇️", "fetch": "🔄"}

        for command in common_commands:
            button = Button(
                button_frame,
                text=f"{git_icons[command]} {command.capitalize()}",
                command=lambda c=command: self.execute_command(c)
            )
            button.pack(side="left")

        self.entry = Entry(button_frame, width=80)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.focus()

        self.entry.bind("<Return>", lambda event: self.execute_command(self.entry.get()))
        self.entry.bind("<Up>", self.navigate_history)
        self.entry.bind("<Down>", self.navigate_history)

    def setup_context_menu(self):
        self.context_menu = Menu(self.output_text)
        self.output_text.bind(
            "<Button-3>",
            lambda event: self.context_menu.tk_popup(event.x_root, event.y_root)
        )
        self.context_menu.add_command(label="Git Add", command=self.add_selected_text_to_git_staging)
        self.context_menu.add_command(label="Git Status", command=lambda: self.execute_command("status"))
        self.context_menu.add_command(label="Git Unstage", command=self.unstage_selected_text)
        self.context_menu.add_command(label="Git Diff", command=self.show_git_diff)

    def execute_command(self, command):
        if command.strip():
            self.command_history.append(command)
            self.history_pointer[0] = len(self.command_history)
            directory = self.repo_dir or os.getcwd()
            git_command = f'git -C "{directory}" {command}'
            try:
                if command == "status --porcelain -u":
                    self.update_output_text(self.output_text)
                else:
                    output = subprocess.check_output(
                        git_command, stderr=subprocess.STDOUT, shell=True, text=True
                    )
                    self.insert_ansi_text(self.output_text, f"{git_command}\n{output}\n")
            except subprocess.CalledProcessError as e:
                self.insert_ansi_text(self.output_text, f"Error: {e.output}\n", "error")
            self.entry.delete(0, END)
            self.output_text.see(END)

    def populate_branch_menu(self):
        self.branch_menu.delete(0, END)
        try:
            branches_output = subprocess.check_output(
                ["git", "branch", "--all"], text=True
            )
            branches = list(
                filter(None, [branch.strip() for branch in branches_output.split("\n")])
            )
            active_branch = next(
                (branch[2:] for branch in branches if branch.startswith("*")), None
            )
            for branch in branches:
                is_active = branch.startswith("*")
                branch_name = branch[2:] if is_active else branch
                display_name = f"✓ {branch_name}" if is_active else branch_name
                self.branch_menu.add_command(
                    label=display_name,
                    command=lambda b=branch_name: self.checkout_branch(b)
                )
        except subprocess.CalledProcessError as e:
            self.insert_ansi_text(
                self.output_text, f"Error fetching branches: {e.output}\n", "error"
            )

    def update_commit_list(self, commit_list):
        command = 'git log --no-merges --color --graph --pretty=format:"%h %d %s - <%an (%cr)>" --abbrev-commit --branches'
        output = subprocess.check_output(command, shell=True, text=True)
        commit_list.delete(0, END)
        self.apply_visual_styles(commit_list)
        current_commit = self.get_current_checkout_commit()
        short_hash_number_commit = current_commit[:7]
        for line in output.split("\n"):
            line = line[2:]
            if short_hash_number_commit in line:
                commit_list.insert(END, f"* {line}")
            else:
                commit_list.insert(END, line)
        self.apply_visual_styles(commit_list)

    def apply_visual_styles(self, commit_list):
        current_commit = self.get_current_checkout_commit()
        for i in range(commit_list.size()):
            item = commit_list.get(i)
            if current_commit in item:
                commit_list.itemconfig(i, {"bg": "yellow"})
            elif item.startswith("*"):
                commit_list.itemconfig(i, {"fg": "green"})
            else:
                commit_list.itemconfig(i, {"fg": "gray"})

    def commit_list_context_menu(self, event):
        context_menu = Menu(self.commit_list, tearoff=0)
        context_menu.add_command(
            label="Checkout",
            command=lambda: self.checkout_commit(
                self.commit_list.get(self.commit_list.curselection())
            )
        )
        context_menu.add_command(
            label="View Details",
            command=lambda: self.view_commit_details(
                self.commit_list.get(self.commit_list.curselection())
            )
        )
        context_menu.post(event.x_root, event.y_root)

    def checkout_commit(self, commit_info):
        commit_hash = commit_info.split(" ")[0]
        try:
            self.execute_command(f"checkout {commit_hash}")
            self.update_status(commit_hash)
            self.update_commit_list(self.commit_list)
        except subprocess.CalledProcessError as e:
            self.insert_ansi_text(
                self.output_text, f"Error checking out commit: {e.output}\n", "error"
            )
        self.apply_visual_styles(self.commit_list)

    def view_commit_details(self, commit_hash):
        try:
            commit_hash_number = commit_hash[:7]
            output = subprocess.check_output(
                ["git", "show", "--color=always", commit_hash_number], text=True
            )
            details_window = Toplevel()
            details_window.title(f"{commit_hash}")
            text_widget = scrolledtext.ScrolledText(details_window)
            self.define_ansi_tags(text_widget)
            self.apply_ansi_styles(text_widget, output)
            text_widget.config(state=DISABLED)
            text_widget.pack(fill="both", expand=True)
        except subprocess.CalledProcessError as e:
            error_window = Toplevel()
            error_window.title("Error")
            Label(
                error_window, text=f"Failed to fetch commit details: {e.output}"
            ).pack(pady=20, padx=20)

    def get_current_checkout_commit(self):
        current_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
        self.update_status()
        return current_commit

    def checkout_branch(self, branch):
        self.execute_command(f"checkout {branch}")
        self.populate_branch_menu()
        self.update_commit_list(self.commit_list)
        self.update_status()

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

    def navigate_history(self, event):
        if self.command_history:
            if event.keysym == "Up":
                self.history_pointer[0] = max(0, self.history_pointer[0] - 1)
            elif event.keysym == "Down":
                self.history_pointer[0] = min(len(self.command_history), self.history_pointer[0] + 1)
            command = (
                self.command_history[self.history_pointer[0]]
                if self.history_pointer[0] < len(self.command_history)
                else ""
            )
            self.entry.delete(0, END)
            self.entry.insert(0, command)

    def add_selected_text_to_git_staging(self):
        selected_text = self.output_text.get("sel.first", "sel.last")
        if selected_text:
            self.execute_command(f"add -f {selected_text}")

    def unstage_selected_text(self):
        selected_text = self.output_text.get("sel.first", "sel.last")
        if selected_text:
            self.execute_command(f"reset -- {selected_text}")

    def get_git_status(self):
        return subprocess.check_output(
            ["git", "status", "--porcelain", "-u"], text=True
        )

    def show_git_diff(self):
        git_diff_command = "git diff --color"
        try:
            output = subprocess.check_output(
                git_diff_command, shell=True, stderr=subprocess.STDOUT
            )
            output = output.decode("utf-8", errors="replace")
            diff_window = Toplevel(self.terminal_window)
            diff_window.title("Git Diff")
            diff_window.geometry("800x600")
            diff_text = Text(diff_window, height=20, width=80, font=my_font)
            diff_text.pack(fill="both", expand=True)
            self.define_ansi_tags(diff_text)
            ansi_escape = re.compile("\\x1B\\[[0-?]*[ -/]*[@-~]")
            for line in output.split("\n"):
                line_clean = ansi_escape.sub("", line)
                if line.startswith("+"):
                    diff_text.insert(END, line_clean + "\n", "addition")
                elif line.startswith("-"):
                    diff_text.insert(END, line_clean + "\n", "deletion")
                elif line.startswith("@"):
                    diff_text.insert(END, line_clean + "\n", "info")
                else:
                    diff_text.insert(END, line_clean + "\n")
            diff_text.config(state="disabled")
        except subprocess.CalledProcessError as e:
            self.output_text.insert(END, f"Error: {e.output}\n", "error")

    def update_output_text(self, output_text_widget):
        git_status = self.get_git_status()
        self.define_ansi_tags(output_text_widget)
        if git_status == "":
            output_text_widget.insert("end", "Your branch is up to date.\n\n")
        else:
            for line in git_status.split("\n"):
                status = line[:2]
                filename = line[3:]
                if status in [" M", "M "]:
                    output_text_widget.insert("end", status, "modified")
                    output_text_widget.insert("end", " <" + filename + ">\n")
                elif status == "MM":
                    output_text_widget.insert("end", status, "modified_multiple")
                    output_text_widget.insert("end", " " + filename + "\n")
                elif status == "??":
                    output_text_widget.insert("end", status, "untracked")
                    output_text_widget.insert("end", " " + filename + "\n")
                elif status == "A ":
                    output_text_widget.insert("end", status, "added")
                    output_text_widget.insert("end", " " + filename + "\n")
                elif status in [" D", "D "]:
                    output_text_widget.insert("end", status, "deleted")
                    output_text_widget.insert("end", " " + filename + "\n")
                elif status == "R ":
                    output_text_widget.insert("end", status, "renamed")
                    output_text_widget.insert("end", " " + filename + "\n")
                elif status == "C ":
                    output_text_widget.insert("end", status, "copied")
                    output_text_widget.insert("end", " " + filename + "\n")
                elif status == "U ":
                    output_text_widget.insert("end", status, "unmerged")
                    output_text_widget.insert("end", " " + filename + "\n")
                elif status == "!!":
                    output_text_widget.insert("end", status, "ignored")
                    output_text_widget.insert("end", " " + filename + "\n")
                else:
                    output_text_widget.insert("end", status)
                    output_text_widget.insert("end", " " + filename + "\n")
                try:
                    if status in [" M", "M "]:
                        git_diff_command = f"git diff --color {filename}"
                        diff_output = subprocess.check_output(
                            git_diff_command, shell=True, stderr=subprocess.STDOUT
                        )
                        diff_output = diff_output.decode("utf-8", errors="replace")
                        ansi_escape = re.compile("\\x1B\\[[0-?]*[ -/]*[@-~]")
                        for diff_line in diff_output.split("\n")[1:]:
                            line_clean = ansi_escape.sub("", diff_line)
                            self.apply_ansi_styles(self.output_text, line_clean)
                        output_text_widget.insert("end", " </" + filename + ">\n\n")
                except subprocess.CalledProcessError as e:
                    self.output_text.insert(END, f"Error: {e.output}\n", "error")

    def update_status(self, commit_hash="HEAD"):
        try:
            branch_name = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", commit_hash], text=True
            ).strip()
            if branch_name != "HEAD":
                self.status_bar.config(text=f"Current branch: {branch_name}")
            else:
                commit_short_hash = subprocess.check_output(
                    ["git", "rev-parse", "--short", commit_hash], text=True
                ).strip()
                self.status_bar.config(text=f"Current commit: {commit_short_hash}")
        except subprocess.CalledProcessError:
            self.status_bar.config(text="Error: Invalid identifier")

