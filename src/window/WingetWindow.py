import re
import subprocess
import threading
from tkinter import Button, LEFT, X, Frame, BOTH, WORD, scrolledtext, RIGHT, VERTICAL, Scrollbar, Canvas, Label, \
    Listbox, Y, END, simpledialog, NORMAL, DISABLED, messagebox, BooleanVar, Toplevel, Checkbutton


class WingetWindow:
    def __init__(self):
        self.winget_window = Toplevel()
        self.winget_window.title("WinGet Package Manager")
        self.winget_window.geometry("1000x700")
        self.upgrade_vars = []
        self.setup_ui()
        self.list_installed()
        self.list_upgradable()
        self.insert_output(
            """Welcome to WinGet Package Manager.
Use the buttons to perform WinGet operations."""
        )

    def run_command(self, command):
        try:
            command += " --disable-interactivity"
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                shell=True,
            )
            output = result.stdout
            spinner_chars = {"\\", "-", "|", "/", "█", "▒"}
            filtered_output = "\n".join(
                line
                for line in output.splitlines()
                if not set(line.strip()).issubset(spinner_chars) and line.strip() != ""
            )
            return filtered_output
        except Exception as e:
            return f"Error: {str(e)}"

    def list_programs(self):
        output = self.run_command("winget search --exact")
        self.insert_output(output)

    def list_installed(self):
        output = self.run_command('winget list --source "winget"')
        self.installed_listbox.delete(0, END)
        lines = output.splitlines()
        for line in lines[1:]:
            program_info = " ".join(line.split()).strip()
            if program_info:
                self.installed_listbox.insert(END, program_info)

    def list_upgradable(self):
        output = self.run_command("winget upgrade --include-unknown")
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
                    var = BooleanVar()
                    checkbox = Checkbutton(
                        self.upgrade_checkboxes_frame,
                        text=display_text,
                        variable=var,
                        anchor="w",
                        justify=LEFT,
                        font=("Courier", 10),
                    )
                    checkbox.grid(row=i, column=0, sticky="w")
                    self.upgrade_vars.append((var, program_id))
        self.upgrade_checkboxes_frame.update_idletasks()
        self.upgrade_checkboxes_canvas.configure(
            scrollregion=self.upgrade_checkboxes_canvas.bbox("all")
        )

    def update_output(self, output):
        self.output_text.insert(END, output + "\n")
        self.output_text.see(END)

    def upgrade_selected(self):
        self.disable_upgrade_buttons()

        def upgrade_thread():
            selected_programs = [info for var, info in self.upgrade_vars if var.get()]
            if not selected_programs:
                messagebox.showinfo(
                    "No Selection", "Please select programs to upgrade."
                )
                self.enable_upgrade_buttons()
                return
            successfully_upgraded = []
            for program_info in selected_programs:
                program_id = program_info.split()[0]
                self.update_output(f"\nUpgrading {program_id}...")
                output = self.run_command(f'winget upgrade --include-unknown --id "{program_id}"')
                self.update_output(output)
                successfully_upgraded.append(program_id)
            self.list_upgradable()
            summary = (
                f"Programs {', '.join(successfully_upgraded)} successfully upgraded."
            )
            self.update_output(summary)
            self.enable_upgrade_buttons()

        threading.Thread(target=upgrade_thread).start()

    def disable_upgrade_buttons(self):
        self.select_all_button.config(state=DISABLED)
        self.deselect_all_button.config(state=DISABLED)
        self.upgrade_selected_button.config(state=DISABLED)
        for widget in self.upgrade_checkboxes_frame.winfo_children():
            if isinstance(widget, Checkbutton):
                widget.config(state=DISABLED)

    def enable_upgrade_buttons(self):
        self.select_all_button.config(state=NORMAL)
        self.deselect_all_button.config(state=NORMAL)
        self.upgrade_selected_button.config(state=NORMAL)
        for widget in self.upgrade_checkboxes_frame.winfo_children():
            if isinstance(widget, Checkbutton):
                widget.config(state=NORMAL)

    def select_all(self):
        for var, _ in self.upgrade_vars:
            var.set(True)

    def deselect_all(self):
        for var, _ in self.upgrade_vars:
            var.set(False)

    def search_program(self):
        search_term = simpledialog.askstring("Search", "Enter program name to search:")
        if search_term:
            output = self.run_command(f'winget search --exact "{search_term}"')
            self.insert_output(output)

    def install_program(self):
        program_id = simpledialog.askstring("Install", "Enter program ID to install:")
        if program_id:
            output = self.run_command(f'winget install -s "winget" "{program_id}"')
            self.insert_output(f"Installing {program_id}...\n{output}")
            self.list_installed()
            self.list_upgradable()

    def uninstall_program(self):
        program_id = simpledialog.askstring(
            "Uninstall", "Enter program ID to uninstall:"
        )
        if program_id:
            output = self.run_command(f'winget uninstall "{program_id}"')
            self.insert_output(f"Uninstalling {program_id}...\n{output}")
            self.list_installed()
            self.list_upgradable()

    def get_program_description(self, program_id):
        return self.run_command(f'winget show "{program_id}"')

    def program_description(self):
        program_id = simpledialog.askstring(
            "Description of Program", "Enter program ID to get its description:"
        )
        if program_id:
            output = self.get_program_description(program_id)
            self.insert_output(output)
            self.list_installed()

    def insert_output(self, output):
        self.output_text.delete(1.0, END)
        self.output_text.insert(END, output)

    def on_mousewheel(self, event):
        self.upgrade_checkboxes_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def bind_mousewheel(self, event):
        self.upgrade_checkboxes_canvas.bind_all("<MouseWheel>", self.on_mousewheel)

    def unbind_mousewheel(self, event):
        self.upgrade_checkboxes_canvas.unbind_all("<MouseWheel>")

    def setup_ui(self):
        main_frame = Frame(self.winget_window)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Left frame setup
        left_frame = Frame(main_frame)
        left_frame.pack(side=LEFT, fill=BOTH, expand=True)
        installed_label = Label(left_frame, text="Installed Programs")
        installed_label.pack()
        self.installed_listbox = Listbox(left_frame, height=20, width=50)
        self.installed_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        installed_scrollbar = Scrollbar(left_frame)
        installed_scrollbar.pack(side=RIGHT, fill=Y)
        self.installed_listbox.config(yscrollcommand=installed_scrollbar.set)
        installed_scrollbar.config(command=self.installed_listbox.yview)

        # Right frame setup
        right_frame = Frame(main_frame)
        right_frame.pack(side=RIGHT, fill=BOTH, expand=True)
        upgradable_label = Label(right_frame, text="Upgradable Programs")
        upgradable_label.pack()

        self.upgrade_checkboxes_canvas = Canvas(right_frame)
        self.upgrade_checkboxes_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        upgrade_checkboxes_scrollbar = Scrollbar(
            right_frame, orient=VERTICAL, command=self.upgrade_checkboxes_canvas.yview
        )
        upgrade_checkboxes_scrollbar.pack(side=RIGHT, fill=Y)
        self.upgrade_checkboxes_canvas.configure(yscrollcommand=upgrade_checkboxes_scrollbar.set)
        self.upgrade_checkboxes_frame = Frame(self.upgrade_checkboxes_canvas)
        self.upgrade_checkboxes_canvas.create_window(
            (0, 0), window=self.upgrade_checkboxes_frame, anchor="nw"
        )

        # Bind mouse wheel events
        self.upgrade_checkboxes_canvas.bind("<Enter>", self.bind_mousewheel)
        self.upgrade_checkboxes_canvas.bind("<Leave>", self.unbind_mousewheel)

        # Output text setup
        self.output_text = scrolledtext.ScrolledText(
            self.winget_window, wrap=WORD, height=10, width=120
        )
        self.output_text.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Button frame setup
        button_frame = Frame(self.winget_window)
        button_frame.pack(fill=X, padx=10, pady=10)

        # Create buttons
        Button(
            button_frame, text="List All Programs", command=self.list_programs
        ).pack(side=LEFT, padx=5)

        Button(
            button_frame, text="Search Program", command=self.search_program
        ).pack(side=LEFT, padx=5)

        Button(
            button_frame, text="Program Description", command=self.program_description
        ).pack(side=LEFT, padx=5)

        Button(
            button_frame, text="Install Program", command=self.install_program
        ).pack(side=LEFT, padx=5)

        Button(
            button_frame, text="Uninstall Program", command=self.uninstall_program
        ).pack(side=LEFT, padx=5)

        self.select_all_button = Button(
            button_frame, text="Select All", command=self.select_all
        )
        self.select_all_button.pack(side=LEFT, padx=5)

        self.deselect_all_button = Button(
            button_frame, text="Deselect All", command=self.deselect_all
        )
        self.deselect_all_button.pack(side=LEFT, padx=5)

        self.upgrade_selected_button = Button(
            button_frame, text="Upgrade Selected", command=self.upgrade_selected
        )
        self.upgrade_selected_button.pack(side=LEFT, padx=5)