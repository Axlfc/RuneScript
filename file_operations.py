from tkinter import filedialog, messagebox, simpledialog
import os

from menu_functions import open_file

from tk_utils import root, directory_label


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
        directory_label.config(text=f"{directory}")
        open_first_text_file(directory)


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
