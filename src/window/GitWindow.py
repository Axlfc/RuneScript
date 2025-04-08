import subprocess
import re
import os
from tkinter import *
from tkinter import scrolledtext, Menu, Frame, Button, Entry, Label, Toplevel, Listbox, Text, SUNKEN, END, W

from lib.git_cli.components.git_menu import GitMenuManager
from src.views.tk_utils import my_font

from lib.git_cli.components.ansi_renderer import AnsiRenderer
from lib.git_cli.commands.dispatcher import CommandDispatcher
from lib.git_cli.components.commit_list import CommitListView
from lib.git_cli.components.branch_menu import BranchMenuManager
from lib.git_cli.components.command_entry import CommandEntryView

from pathlib import Path


class GitWindow:
    def __init__(self, repo_dir=None):
        self.repo_dir = Path(repo_dir or os.getcwd())
        self.dispatcher = CommandDispatcher(repo_dir=str(self.repo_dir))
        self.command_history = []
        self.history_pointer = [0]

        self.create_window()
        self.setup_ui()  # Aquí se crean self.output_text, self.button_frame y self.commit_frame.

        # Ahora que self.output_text ya existe, creamos el ansi_renderer
        self.ansi_renderer = AnsiRenderer(self.output_text)
        self.ansi_renderer.define_ansi_tags(self.output_text)

        # Inicializar el resto de los componentes que dependen de GitWindow
        self.commit_list_view = CommitListView(self.commit_frame, self)
        self.command_entry_view = CommandEntryView(self.button_frame, self)
        self.git_menu_manager = GitMenuManager(self.menubar, self)
        self.branch_menu_manager = BranchMenuManager(self.menubar, self)
        self.git_menu_manager.setup_git_menu()

        # Asignar los bindings de navegación del entry
        self.entry.bind("<Up>", self.command_entry_view.navigate_history)
        self.entry.bind("<Down>", self.command_entry_view.navigate_history)

        self.execute_command("status --porcelain -u")
        # self.terminal_window.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_window(self):
        self.terminal_window = Toplevel()
        self.terminal_window.title("Git Console")
        self.terminal_window.geometry("600x512")

        # Setup menubar
        self.menubar = Menu(self.terminal_window)
        self.terminal_window.config(menu=self.menubar)

    def setup_ui(self):
        # Output text area
        self.output_text = scrolledtext.ScrolledText(self.terminal_window, height=20, width=80)
        self.output_text.pack(fill="both", expand=True)

        # Status bar
        self.status_bar = Label(self.terminal_window, text="Checking branch...", bd=1, relief=SUNKEN, anchor=W)
        self.status_bar.pack(side="top", fill="x")

        # Crear el contenedor para la lista de commits
        self.commit_frame = Frame(self.terminal_window)
        self.commit_frame.pack(fill="both", expand=True)

        # Button frame
        self.setup_button_frame()

        # Context menu
        self.setup_context_menu()

        self.update_status()

    def setup_commit_list(self):
        top_frame = Frame(self.terminal_window)
        top_frame.pack(fill="both", expand=True)

        commit_scrollbar = Scrollbar(top_frame)
        commit_scrollbar.pack(side="right", fill="y")

        self.commit_list = Listbox(top_frame, yscrollcommand=commit_scrollbar.set)
        self.commit_list.pack(side="left", fill="both", expand=True)
        commit_scrollbar.config(command=self.commit_list.yview)

        self.commit_list.bind("<Button-3>", self.commit_list_view.commit_list_context_menu)
        self.commit_list_view.update_commit_list()

    def setup_button_frame(self):
        # Almacenar el frame de botones en self.button_frame para usarlo después
        self.button_frame = Frame(self.terminal_window)
        self.button_frame.pack(fill="both", expand=False)

        common_commands = ["commit", "push", "pull", "fetch"]
        git_icons = {"commit": "💾", "push": "⬆️", "pull": "⬇️", "fetch": "🔄"}

        for command in common_commands:
            button = Button(
                self.button_frame,
                text=f"{git_icons[command]} {command.capitalize()}",
                command=lambda c=command: self.execute_command(c)
            )
            button.pack(side="left")

        self.entry = Entry(self.button_frame, width=80)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.focus()

        # Bind solo el Enter aquí; los binds para las flechas se asignan después de crear command_entry_view
        self.entry.bind("<Return>", lambda event: self.execute_command(self.entry.get()))

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
                    self.ansi_renderer.insert_ansi_text(self.output_text, f"{git_command}\n{output}\n")
            except subprocess.CalledProcessError as e:
                self.ansi_renderer.insert_ansi_text(self.output_text, f"Error: {e.output}\n", "error")
            self.entry.delete(0, END)
            self.output_text.see(END)

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
            self.ansi_renderer.define_ansi_tags(diff_text)
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
        self.ansi_renderer.define_ansi_tags(output_text_widget)
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
                            self.ansi_renderer.apply_ansi_styles(self.output_text, line_clean)
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

