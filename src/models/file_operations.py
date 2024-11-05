from tkinter import messagebox, simpledialog
import os
from src.views.tk_utils import root, script_name_label


def validate_time(hour, minute):
    try:
        hour = int(hour)
        minute = int(minute)
        if not 0 <= hour < 24 or not 0 <= minute < 60:
            raise ValueError
        return True
    except ValueError:
        messagebox.showerror(
            "Invalid Time", "Please enter a valid time in HH:MM format."
        )
        return False


def rename(event=None):
    global file_name
    if file_name == "":
        file_path = simpledialog.askstring("Rename", "Enter file path or select a file")
        if not file_path:
            return
        print("File path:", file_path)
        if not os.path.exists(file_path):
            messagebox.showerror("Error", "File does not exist")
            return
        file_name = file_path
    dir_path, old_name = os.path.split(file_name)
    new_name = simpledialog.askstring("Rename", "Enter new name")
    try:
        new_path = os.path.join(dir_path, new_name)
        os.rename(file_name, new_path)
        file_name = new_path
        root.title(file_name + " - Script Editor")
    except OSError as e:
        messagebox.showerror("Error", f"Failed to rename file: {e}")


def prompt_rename_file():
    new_name = simpledialog.askstring("Rename or Create File", "Enter new file name:")
    if new_name:
        clean_name = new_name.replace(" ", "_")
        rename_or_create_file(clean_name)


def rename_or_create_file(new_name):
    global file_name
    dir_path = os.path.dirname(file_name) if file_name else os.getcwd()
    new_path = os.path.join(dir_path, new_name)
    if file_name and os.path.exists(file_name):
        try:
            os.rename(file_name, new_path)
            file_name = new_path
            script_name_label.config(text=f"File Name: {new_name}")
            messagebox.showinfo(
                "Rename Successful", f"File has been renamed to {new_name}"
            )
        except OSError as e:
            messagebox.showerror("Error", f"Failed to rename file: {e}")
    else:
        try:
            with open(new_path, "w") as new_file:
                new_file.write("")
            file_name = new_path
            script_name_label.config(text=f"File Name: {new_name}")
            messagebox.showinfo(
                "File Created", f"New file has been created: {new_name}"
            )
        except OSError as e:
            messagebox.showerror("Error", f"Failed to create file: {e}")


def remove_asterisk_from_title():
    title = root.title()
    if title.startswith("*"):
        root.title(title[1:])
