import subprocess
import sys
from tkinter import filedialog, messagebox, simpledialog
import os
import json

from src.controllers.menu_functions import open_file
from src.localization import localization_data

from src.views.tk_utils import root, directory_label, script_name_label, file_name


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


def rename(event=None):
    """
        Renames an existing file after prompting the user for the new file name.

        This function allows the user to specify a new name for an existing file. If the file path is not already
        set, it prompts the user to either enter a file path or select a file using a file dialog. The function then
        carries out the renaming operation and updates the application title.

        Parameters:
        event (optional): An event object representing the event that triggered this function.

        Returns:
        None
    """
    global file_name
    if file_name == "":
        # Prompt the user to enter the file path or select a file using a file dialog
        file_path = simpledialog.askstring("Rename", "Enter file path or select a file")
        if not file_path:
            # User cancelled the operation
            return

        print("File path:", file_path)
        if not os.path.exists(file_path):
            messagebox.showerror("Error", "File does not exist")
            return

        file_name = file_path

    # Extract the directory path and file name
    dir_path, old_name = os.path.split(file_name)
    new_name = simpledialog.askstring("Rename", "Enter new name")

    try:
        # Rename the file
        new_path = os.path.join(dir_path, new_name)
        os.rename(file_name, new_path)
        file_name = new_path
        root.title(file_name + " - Script Editor")
    except OSError as e:
        messagebox.showerror("Error", f"Failed to rename file: {e}")


def select_directory():
    """
        Opens a dialog for the user to select a directory, and changes the current working directory to the selected one.

        After the directory is selected, the function updates the directory label in the UI and opens the first text file
        (if any) in the selected directory.

        Parameters:
        None

        Returns:
        None
    """
    directory = filedialog.askdirectory()
    if directory:
        os.chdir(directory)
        global current_directory  # Declare current_directory as global if it's not in the same file
        current_directory = directory  # Update the current_directory variable
        directory_label.config(text=f"{directory}")
        # Ask user if they want to open the first text file
        if messagebox.askyesno(localization_data['open_script'], localization_data['open_first_file_from_directory']):
            open_first_text_file(directory)


def open_current_directory():
    directory = directory_label.cget("text")
    if sys.platform == "win32":
        os.startfile(directory)
    elif sys.platform == "darwin":
        subprocess.run(["open", directory])
    else:  # Assuming Linux or similar
        subprocess.run(["xdg-open", directory])


def open_first_text_file(directory):
    """
        Opens the first text file in the given directory.

        This function scans the specified directory for text files and, if found, opens the first one. It is typically
        used after changing the working directory to automatically open a text file from that directory.

        Parameters:
        directory (str): The directory path in which to search for text files.

        Returns:
        None
    """
    text_files = get_text_files(directory)
    if text_files:
        file_path = os.path.join(directory, text_files[0])
        open_file(file_path)


def get_text_files(directory):
    """
        Retrieves a list of text files in the specified directory.

        This function scans the provided directory and creates a list of all files ending with a '.txt' extension.

        Parameters:
        directory (str): The directory path in which to search for text files.

        Returns:
        list: A list of text file names found in the directory.
    """
    text_files = []
    for file in os.listdir(directory):
        if file.endswith(".txt"):
            text_files.append(file)
    return text_files


def prompt_rename_file():
    """
    Prompts the user for a new file name and renames or creates the file.
    """
    new_name = simpledialog.askstring("Rename or Create File", "Enter new file name:")
    if new_name:  # Proceed only if the user entered a name
        clean_name = new_name.replace(" ", "_")
        rename_or_create_file(clean_name)


def rename_or_create_file(new_name):
    """
    Renames the current file to the new name provided by the user, or creates a new file if none exists.

    Parameters:
    new_name (str): The new name for the file.
    """
    global file_name
    dir_path = os.path.dirname(file_name) if file_name else os.getcwd()  # Use current directory if file_name is not set
    new_path = os.path.join(dir_path, new_name)

    if file_name and os.path.exists(file_name):
        # If there's a current file, rename it
        try:
            os.rename(file_name, new_path)
            file_name = new_path  # Update the global file_name variable
            script_name_label.config(text=f"File Name: {new_name}")
            messagebox.showinfo("Rename Successful", f"File has been renamed to {new_name}")
        except OSError as e:
            messagebox.showerror("Error", f"Failed to rename file: {e}")
    else:
        # If no current file, try to create a new one
        try:
            with open(new_path, 'w') as new_file:
                new_file.write("")  # Create an empty file
            file_name = new_path  # Update the global file_name variable
            script_name_label.config(text=f"File Name: {new_name}")
            messagebox.showinfo("File Created", f"New file has been created: {new_name}")
        except OSError as e:
            messagebox.showerror("Error", f"Failed to create file: {e}")


def remove_asterisk_from_title():
    """
        Removes an asterisk from the beginning of the application's title if present.

        This function is typically used to update the application's title to indicate that the current file has been saved
        or no longer contains unsaved changes.

        Parameters:
        None

        Returns:
        None
    """
    title = root.title()
    if title.startswith("*"):
        root.title(title[1:])
