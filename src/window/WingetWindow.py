import re
import subprocess
import threading
import tkinter as tk
import customtkinter as ctk
from src.utils.thread_manager import thread_manager
from tkinter import (
    BooleanVar, END, simpledialog, messagebox
)
from src.ui.themed_window import ThemedWindow


class WingetWindow(ThemedWindow):
    def __init__(self, parent=None):
        if parent is None:
            try:
                from src.views.tk_utils import root
                parent = root
            except ImportError:
                pass
        super().__init__(parent)
        self.winget_window = self # self is the window
        self.title("WinGet Package Manager")
        self.geometry("1000x800")
        self.upgrade_vars = []
        self.setup_ui()
        self.list_installed()
        self.list_upgradable()
        self.insert_output(
            """Welcome to WinGet Package Manager.
Use the buttons to perform WinGet operations."""
        )

    def run_command_async(self, command, task_id, on_complete):
        thread_manager.update_status_bar(f"Running winget command...", show_progress=True)

        def worker(stop_event):
            try:
                full_command = command + " --disable-interactivity"
                result = subprocess.run(
                    full_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    shell=True)
                output = result.stdout
                spinner_chars = {"\\", "-", "|", "/", "█", "▒"}
                filtered_output = "\n".join(
                    line
                    for line in output.splitlines()
                    if not set(line.strip()).issubset(spinner_chars) and line.strip() != ""
                )
                self.winget_window.after(0, lambda: [
                    thread_manager.update_status_bar("Ready"),
                    on_complete(filtered_output)
                ])
            except Exception as e:
                self.winget_window.after(0, lambda: messagebox.showerror("Error", str(e)))

        thread_manager.run_in_thread(worker, task_id)

    def list_programs(self):
        self.run_command_async("winget search --exact", "winget_list_all", self.insert_output)

    def list_installed(self):
        def update_installed(output):
            if not self.winget_window.winfo_exists(): return
            self.installed_listbox.delete(0, tk.END)
            lines = output.splitlines()
            for line in lines[1:]:
                program_info = " ".join(line.split()).strip()
                if program_info:
                    self.installed_listbox.insert(tk.END, program_info)

        self.run_command_async('winget list --source "winget"', "winget_list_installed", update_installed)

    def list_upgradable(self):
        self.run_command_async("winget upgrade --include-unknown", "winget_list_upgradable", self._process_upgradable)

    def _process_upgradable(self, output):
        if not self.winget_window.winfo_exists(): return
        removed_text = "winget"
        for widget in self.upgrade_checkboxes_frame.winfo_children():
            widget.destroy()
        self.upgrade_vars.clear()
        version_pattern = re.compile("(\\d+[\\.-]\\d+[\\.-]?\\d*)")
        lines = output.splitlines()[1:]
        for i, line in enumerate(lines):
            from_version = "Unknown"
            to_version = "Unknown"
            if line.strip():
                match = version_pattern.search(line)
                if match:
                    try:
                        program_info = (
                            line[match.start():].strip().replace(removed_text, "")
                        )
                        to_version = program_info[::-1].split()[0][::-1]
                        from_version = program_info[::-1].split()[1][::-1]
                        new_to_version = "Unknown"
                        new_from_version = "Unknown"
                        if "(" in program_info and ")" in program_info:
                            new_line = line.replace(removed_text, "")
                            new_to_version = new_line[::-1].split()[0]
                            if "(" in new_to_version and ")" in new_to_version:
                                new_new_line = new_line.split()[::-1]
                                new_to_version = new_new_line[1] + " " + new_new_line[0]
                                new_line = new_line.replace(new_to_version, "").strip()
                                to_version = new_to_version
                            if (
                                    "(" in new_to_version
                                    and ")" in new_to_version
                                    and new_to_version != "Unknown"
                            ):
                                new_new_line = new_line.split()[::-1]
                                new_from_version = (
                                        new_new_line[1] + " " + new_new_line[0]
                                )
                                from_version = new_from_version
                        line = (
                            line.replace(to_version, "")
                            .replace(from_version, "")
                            .replace(removed_text, "")
                        )
                    except Exception as e:
                        pass
                program_id = line[::-1].split()[0][::-1]
                if program_id == "winget":
                    try:
                        removed_text = "winget"
                        new_line = line.replace(removed_text, "")
                        to_version = new_line[::-1].split()[0][::-1]
                        from_version = new_line[::-1].split()[1][::-1]
                        new_line = (
                            line.replace(from_version, "")
                            .replace(to_version, "")
                            .replace(removed_text, "")
                        )
                        program_id = new_line[::-1].split()[0][::-1]
                    except Exception as e:
                        pass
                if (
                        from_version != "Unknown"
                        and to_version != "Unknown"
                        and program_id != "()"
                ):
                    display_text = (
                        f"{program_id:<40} {from_version:<15} {to_version:<15}"
                    )
                    var = tk.BooleanVar()
                    checkbox = ctk.CTkCheckBox(
                        self.upgrade_checkboxes_frame,
                        text=display_text,
                        variable=var,
                        font=("Courier", 12))
                    checkbox.pack(anchor="w", pady=2)
                    self.upgrade_vars.append((var, program_id))

    def update_output(self, output):
        self.output_text.insert(tk.END, output + "\n")
        self.output_text.see(tk.END)

    def upgrade_selected(self):
        selected_programs = [info for var, info in self.upgrade_vars if var.get()]
        if not selected_programs:
            messagebox.showinfo("No Selection", "Please select programs to upgrade.")
            return

        self.disable_upgrade_buttons()
        task_id = "winget_upgrade"

        def worker(stop_event):
            successfully_upgraded = []
            for program_info in selected_programs:
                if stop_event.is_set(): break
                program_id = program_info.split()[0]
                self.winget_window.after(0, lambda p=program_id: self.update_output(f"\nUpgrading {p}..."))

                # We use blocking run here because it's already in a worker thread
                try:
                    res = subprocess.run(f'winget upgrade --include-unknown --id "{program_id}" --disable-interactivity',
                                       stdout=subprocess.PIPE, text=True, shell=True)
                    self.winget_window.after(0, lambda o=res.stdout: self.update_output(o))
                    successfully_upgraded.append(program_id)
                except Exception as e:
                    self.winget_window.after(0, lambda err=str(e): self.update_output(f"Error: {err}"))

            self.winget_window.after(0, lambda: [
                self.list_upgradable(),
                self.update_output(f"Programs {', '.join(successfully_upgraded)} successfully upgraded."),
                self.enable_upgrade_buttons()
            ])

        thread_manager.run_in_thread(worker, task_id)

    def disable_upgrade_buttons(self):
        self.select_all_button.configure(state=tk.DISABLED)
        self.deselect_all_button.configure(state=tk.DISABLED)
        self.upgrade_selected_button.configure(state=tk.DISABLED)
        for widget in self.upgrade_checkboxes_frame.winfo_children():
            if isinstance(widget, ctk.CTkCheckBox):
                widget.configure(state=tk.DISABLED)

    def enable_upgrade_buttons(self):
        self.select_all_button.configure(state=tk.NORMAL)
        self.deselect_all_button.configure(state=tk.NORMAL)
        self.upgrade_selected_button.configure(state=tk.NORMAL)
        for widget in self.upgrade_checkboxes_frame.winfo_children():
            if isinstance(widget, ctk.CTkCheckBox):
                widget.configure(state=tk.NORMAL)

    def select_all(self):
        for var, _ in self.upgrade_vars:
            var.set(True)

    def deselect_all(self):
        for var, _ in self.upgrade_vars:
            var.set(False)

    def search_program(self):
        search_term = simpledialog.askstring("Search", "Enter program name to search:")
        if search_term:
            self.run_command_async(f'winget search --exact "{search_term}"', "winget_search", self.insert_output)

    def install_program(self):
        program_id = simpledialog.askstring("Install", "Enter program ID to install:")
        if program_id:
            def on_complete(output):
                self.insert_output(f"Installing {program_id}...\n{output}")
                self.list_installed()
                self.list_upgradable()
            self.run_command_async(f'winget install -s "winget" "{program_id}"', "winget_install", on_complete)

    def uninstall_program(self):
        program_id = simpledialog.askstring(
            "Uninstall", "Enter program ID to uninstall:"
        )
        if program_id:
            def on_complete(output):
                self.insert_output(f"Uninstalling {program_id}...\n{output}")
                self.list_installed()
                self.list_upgradable()
            self.run_command_async(f'winget uninstall "{program_id}"', "winget_uninstall", on_complete)

    def get_program_description(self, program_id):
        return self.run_command(f'winget show "{program_id}"')

    def program_description(self):
        program_id = simpledialog.askstring(
            "Description of Program", "Enter program ID to get its description:"
        )
        if program_id:
            def on_complete(output):
                self.insert_output(output)
                self.list_installed()
            self.run_command_async(f'winget show "{program_id}"', "winget_show", on_complete)

    def insert_output(self, output):
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, output)

    def on_mousewheel(self, event):
        self.upgrade_checkboxes_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def bind_mousewheel(self, event):
        self.upgrade_checkboxes_canvas.bind_all("<MouseWheel>", self.on_mousewheel)

    def unbind_mousewheel(self, event):
        self.upgrade_checkboxes_canvas.unbind_all("<MouseWheel>")

    def setup_ui(self):
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top frame setup
        top_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        top_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left frame setup
        left_frame = ctk.CTkFrame(top_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        ctk.CTkLabel(left_frame, text="Installed Programs", font=("Segoe UI", 12, "bold")).pack(pady=5)

        # Listbox still needed, wrap it
        self.installed_listbox = tk.Listbox(left_frame, borderwidth=0, highlightthickness=0)
        self.installed_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        installed_scrollbar = ctk.CTkScrollbar(left_frame, orientation="vertical", command=self.installed_listbox.yview)
        installed_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.installed_listbox.configure(yscrollcommand=installed_scrollbar.set)

        # Right frame setup
        right_frame = ctk.CTkFrame(top_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        ctk.CTkLabel(right_frame, text="Upgradable Programs", font=("Segoe UI", 12, "bold")).pack(pady=5)

        # Use CTkScrollableFrame for upgradable list
        self.upgrade_checkboxes_frame = ctk.CTkScrollableFrame(right_frame)
        self.upgrade_checkboxes_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Output text setup
        self.output_text = ctk.CTkTextbox(
            self.main_container, height=200
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Button frame setup
        button_frame = ctk.CTkFrame(self.main_container)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        # Create buttons
        ctk.CTkButton(
            button_frame, text="List All", width=100, command=self.list_programs
        ).pack(side=tk.LEFT, padx=2)

        ctk.CTkButton(
            button_frame, text="Search", width=100, command=self.search_program
        ).pack(side=tk.LEFT, padx=2)

        ctk.CTkButton(
            button_frame, text="Description", width=100, command=self.program_description
        ).pack(side=tk.LEFT, padx=2)

        ctk.CTkButton(
            button_frame, text="Install", width=100, command=self.install_program
        ).pack(side=tk.LEFT, padx=2)

        ctk.CTkButton(
            button_frame, text="Uninstall", width=100, command=self.uninstall_program
        ).pack(side=tk.LEFT, padx=2)

        self.select_all_button = ctk.CTkButton(
            button_frame, text="Select All", width=100, command=self.select_all
        )
        self.select_all_button.pack(side=tk.LEFT, padx=2)

        self.deselect_all_button = ctk.CTkButton(
            button_frame, text="Deselect All", width=100, command=self.deselect_all
        )
        self.deselect_all_button.pack(side=tk.LEFT, padx=2)

        self.upgrade_selected_button = ctk.CTkButton(
            button_frame, text="Upgrade", width=100, command=self.upgrade_selected
        )
        self.upgrade_selected_button.pack(side=tk.LEFT, padx=2)

        # Apply simple theme to Listbox
        is_dark = ctk.get_appearance_mode().lower() == "dark"
        self.installed_listbox.configure(bg="#2b2b2b" if is_dark else "#f0f0f0",
                                         fg="white" if is_dark else "black")
