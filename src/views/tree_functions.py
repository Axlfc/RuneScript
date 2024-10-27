import os
import shutil
import subprocess
import tkinter as tk
import webbrowser
from tkinter import messagebox, simpledialog
from datetime import datetime
from src.controllers.file_operations import open_file
from src.controllers.parameters import write_config_parameter, read_config_parameter
from src.views.tk_utils import tree, menu


def get_project_root():
    """Get the project root path from the first item in tree"""
    root_items = tree.get_children('')
    if root_items:
        return tree.item(root_items[0])['values'][0]
    return None


def get_relative_path(path):
    """
    Get path relative to current working directory from config

    Args:
        path (str): Absolute path to file or directory

    Returns:
        str: Path relative to current working directory
    """
    project_root = read_config_parameter("options.file_management.current_working_directory")
    if project_root and os.path.exists(project_root):
        return os.path.relpath(path, project_root)
    return path


def _copy_relative_path(path):
    """Copy relative path to clipboard"""
    relative_path = get_relative_path(path)
    tree.clipboard_clear()
    tree.clipboard_append(relative_path)


def update_tree(path):
    """
    update_tree

    Args:
        path (Any): Description of path.

    Returns:
        None: Description of return value.
    """
    for item in tree.get_children():
        tree.delete(item)
    abspath = os.path.abspath(path)
    root_node = tree.insert("", "end", text=abspath, values=(abspath,), open=True)
    populate_tree(root_node, abspath)


def populate_tree(parent, path):
    """
    populate_tree

    Args:
        parent (Any): Description of parent.
        path (Any): Description of path.

    Returns:
        None: Description of return value.
    """
    for item in os.listdir(path):
        if item != ".git" and item != ".idea":
            abspath = os.path.join(path, item)
            node = tree.insert(parent, "end", text=item, values=(abspath,), open=False)
            if os.path.isdir(abspath):
                tree.insert(node, "end")


def item_opened(event):
    """
    item_opened

    Args:
        event (Any): Description of event.

    Returns:
        None: Description of return value.
    """
    item = tree.focus()
    abspath = tree.item(item, "values")[0]
    if os.path.isdir(abspath):
        tree.delete(*tree.get_children(item))
        populate_tree(item, abspath)


def on_item_select(event):
    """
    Handle item selection in the tree view.

    Args:
        event (Any): The event triggering the selection.

    Returns:
        None: Prints item information or error message.
    """
    item = tree.focus()
    item_text = tree.item(item, 'text')
    item_values = tree.item(item, 'values')

    if item_values:  # Check if values are present to avoid IndexError
        print(f"Selected: {item_text}")
        print(f"Full path: {item_values[0]}")
    else:
        print(f"Selected: {item_text} (No path available)")


def on_double_click(event):
    """
    Handle double click on tree item
    """
    item = tree.identify("item", event.x, event.y)
    filepath = tree.item(item, "values")[0]
    if os.path.isfile(filepath):
        open_file(filepath)
        write_config_parameter("options.file_management.current_file_path", filepath)


def show_context_menu(event):
    """
    Show context menu for file system items.

    Args:
        event: Right-click event
    """
    # Identify clicked item
    item = tree.identify("item", event.x, event.y)
    if not item:
        return

    # Clear previous selection and select the clicked item
    tree.selection_set(item)
    tree.focus(item)  # Set the focused item to the clicked item

    # Trigger the on_item_select event handler manually to update the selected item display
    on_item_select(event)

    # Get item path
    item_path = tree.item(item, "values")[0]

    # Create context menu
    context_menu = tk.Menu(tree, tearoff=0)

    # Build the appropriate menu based on whether the item is a file or directory
    if os.path.isfile(item_path):
        _build_file_menu(context_menu, item_path)
    elif os.path.isdir(item_path):
        _build_directory_menu(context_menu, item_path)

    # Display menu at mouse position
    context_menu.post(event.x_root, event.y_root)


def _count_file_lines(file_path):
    """Count number of lines in a text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)
        messagebox.showinfo("Line Count", f"Total lines: {line_count}")
    except Exception as e:
        messagebox.showerror("Error", f"Could not count lines: {str(e)}")


def _run_python_script(file_path):
    """Run a Python script"""
    try:
        import subprocess
        result = subprocess.run(['python', file_path], capture_output=True, text=True)
        if result.returncode == 0:
            messagebox.showinfo("Success", f"Output:\n{result.stdout}")
        else:
            messagebox.showerror("Error", f"Error running script:\n{result.stderr}")
    except Exception as e:
        messagebox.showerror("Error", f"Could not run script: {str(e)}")


def _view_image(file_path):
    """Open image in default viewer"""
    try:
        if os.name == 'nt':
            os.startfile(file_path)
        else:
            os.system(f'xdg-open "{file_path}"')
    except Exception as e:
        messagebox.showerror("Error", f"Could not open image: {str(e)}")


def _check_pep8(file_path):
    """Check Python file for PEP8 compliance"""
    try:
        import pycodestyle
        style_guide = pycodestyle.StyleGuide()
        result = style_guide.check_files([file_path])
        messagebox.showinfo("PEP8 Check", f"Found {result.total_errors} style errors.")
    except ImportError:
        messagebox.showwarning("Warning", "pycodestyle not installed. Install with: pip install pycodestyle")
    except Exception as e:
        messagebox.showerror("Error", f"Could not check PEP8: {str(e)}")



def _show_image_info(file_path):
    """Show image information"""
    try:
        from PIL import Image
        with Image.open(file_path) as img:
            info = f"Image Information:\n\n"
            info += f"Format: {img.format}\n"
            info += f"Mode: {img.mode}\n"
            info += f"Size: {img.size}\n"
            info += f"Resolution: {img.info.get('dpi', 'N/A')}"
            messagebox.showinfo("Image Info", info)
    except ImportError:
        messagebox.showwarning("Warning", "Pillow not installed. Install with: pip install Pillow")
    except Exception as e:
        messagebox.showerror("Error", f"Could not get image info: {str(e)}")


def _extract_archive(file_path):
    """Extract archive in the same directory"""
    try:
        import zipfile
        extract_dir = os.path.dirname(file_path)
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        messagebox.showinfo("Success", "Archive extracted successfully")
        _refresh_tree()
    except Exception as e:
        messagebox.showerror("Error", f"Could not extract archive: {str(e)}")


def _extract_archive_to_folder(file_path):
    """Extract archive to a new folder"""
    try:
        import zipfile
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        extract_dir = os.path.join(os.path.dirname(file_path), base_name)
        os.makedirs(extract_dir, exist_ok=True)

        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        messagebox.showinfo("Success", f"Archive extracted to: {extract_dir}")
        _refresh_tree()
    except Exception as e:
        messagebox.showerror("Error", f"Could not extract archive: {str(e)}")


def _show_document_info(file_path):
    """
    Display information about an office document.
    """
    try:
        import olefile
        ole = olefile.OleFileIO(file_path)
        metadata = ole.get_metadata()
        info = f"Title: {metadata.title}\nAuthor: {metadata.author}\nComments: {metadata.comments}"
        messagebox.showinfo("Document Info", info)
    except ImportError:
        messagebox.showerror("Error", "olefile library is not installed.")
    except Exception as e:
        messagebox.showerror("Error", f"Unable to get document info: {e}")


def _convert_to_pdf(file_path):
    """
    Convert an office document to PDF.
    """
    try:
        import comtypes.client
        wdFormatPDF = 17
        word = comtypes.client.CreateObject('Word.Application')
        doc = word.Documents.Open(file_path)
        output_path = os.path.splitext(file_path)[0] + '.pdf'
        doc.SaveAs(output_path, FileFormat=wdFormatPDF)
        doc.Close()
        word.Quit()
        messagebox.showinfo("Success", f"Converted to PDF: {output_path}")
    except ImportError:
        messagebox.showerror("Error", "comtypes library is not installed.")
    except Exception as e:
        messagebox.showerror("Error", f"Unable to convert to PDF: {e}")


def _view_pdf(file_path):
    """
    Open the PDF file using the default PDF viewer.
    """
    try:
        if os.name == 'nt':  # For Windows
            os.startfile(file_path)
        elif os.name == 'posix':  # For macOS and Linux
            subprocess.call(('xdg-open', file_path))
        else:
            webbrowser.open_new(file_path)
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open PDF: {e}")


def _display_text_in_window(text, title="Text Viewer"):
    """
    Display text in a new Tkinter window.
    """
    import tkinter as tk
    window = tk.Toplevel()
    window.title(title)
    text_widget = tk.Text(window, wrap='word')
    text_widget.insert('1.0', text)
    text_widget.pack(expand=1, fill='both')


def _extract_pdf_text(file_path):
    """
    Extract text from the PDF file and display it.
    """
    try:
        import PyPDF2
        with open(file_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            text = ''
            for page in reader.pages:
                text += page.extract_text()
        # Display the extracted text in a new window or message box
        _display_text_in_window(text, title="Extracted Text")
    except ImportError:
        messagebox.showerror("Error", "PyPDF2 library is not installed.")
    except Exception as e:
        messagebox.showerror("Error", f"Unable to extract text: {e}")


def _run_script(file_path):
    """
    Run a script file (.bat, .sh, .ps1).
    """
    try:
        # Windows Batch Script
        if file_path.endswith('.bat') and os.name == 'nt':
            subprocess.call([file_path], shell=True)

        # Shell Script
        elif file_path.endswith('.sh'):
            if os.name == 'posix':
                subprocess.call(['bash', file_path])
            else:
                messagebox.showerror("Error", "Shell scripts are not supported on this OS.")

        # PowerShell Script
        elif file_path.endswith('.ps1') and os.name == 'nt':
            subprocess.call(['powershell', '-ExecutionPolicy', 'Bypass', '-File', file_path])

        else:
            messagebox.showerror("Error", "Unsupported script type or operating system.")
    except Exception as e:
        messagebox.showerror("Error", f"Unable to run script: {e}")


def get_file_extension_operations(file_path):
    """
    Get context menu operations based on file extension

    Args:
        file_path (str): Path to the file

    Returns:
        list: List of tuples containing (label, command) for menu items
    """
    ext = os.path.splitext(file_path)[1].lower()
    operations = []

    # Text files
    text_file_formats = [
        ".txt", ".csv", ".md", ".tex", ".latex", ".ltx", ".sty", ".cls", ".bib",
        ".rtf", ".html", ".xml", ".json", ".yaml", ".log", ".ini",
        ".rst", ".toml", ".xhtml", ".conf", ".properties", ".plist", ".srt",
        ".vtt", ".man", ".info", ".asc", ".tsv", ".env",
        ".cfg", ".xsl", ".mdx", ".sql", ".dot", ".nfo", ".rdf",
        ".tcl", ".awk", ".patch", ".diff", ".org", ".adoc", ".haml", ".scss",
        ".sass", ".less", ".yml", ".gpx", ".lisp"
    ]

    if ext in text_file_formats:
        operations.extend([
            ("Open in Text Editor", lambda: open_file(file_path)),
            ("Count Lines", lambda: _count_file_lines(file_path)),
        ])

    # Script files
    script_file_formats = ['.bat', '.sh', '.ps1']

    if ext in script_file_formats:
        operations.extend([
            ("Open in Text Editor", lambda: open_file(file_path)),
            ("Run Script", lambda: _run_script(file_path)),
        ])

    # Python files
    if ext == '.py':
        operations.extend([
            ("Open in Text Editor", lambda: open_file(file_path)),
            ("Run Python Script", lambda: _run_python_script(file_path)),
            ("Check PEP8", lambda: _check_pep8(file_path)),
        ])

    # Image files
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
        operations.extend([
            ("View Image", lambda: _view_image(file_path)),
            ("Get Image Info", lambda: _show_image_info(file_path)),
        ])

    # Archive files
    if ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
        operations.extend([
            ("Extract Here", lambda: _extract_archive(file_path)),
            ("Extract to Folder", lambda: _extract_archive_to_folder(file_path)),
        ])

    # PDF files
    if ext == '.pdf':
        operations.extend([
            ("View PDF", lambda: _view_pdf(file_path)),
            ("Extract Text", lambda: _extract_pdf_text(file_path)),
        ])

    # Office documents
    if ext in ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']:
        operations.extend([
            ("Convert to PDF", lambda: _convert_to_pdf(file_path)),
            ("Get Document Info", lambda: _show_document_info(file_path)),
        ])

    return operations


def _build_file_menu(menu, file_path):
    """Build context menu for files with extension-specific operations"""
    # Standard operations
    menu.add_command(label="Open", command=lambda: open_file(file_path))
    menu.add_command(label="Open in Default App",
                     command=lambda: os.startfile(file_path) if os.name == 'nt'
                     else os.system(f'xdg-open "{file_path}"'))

    # Add extension-specific operations
    extension_operations = get_file_extension_operations(file_path)
    if extension_operations:
        menu.add_separator()
        for label, command in extension_operations:
            menu.add_command(label=label, command=command)

    # Standard operations continued
    menu.add_separator()
    menu.add_command(label="Copy Path", command=lambda: _copy_to_clipboard(file_path))
    menu.add_command(label="Copy Relative Path", command=lambda: _copy_relative_path(file_path))
    menu.add_separator()
    menu.add_command(label="Rename", command=lambda: _rename_item(file_path))
    menu.add_command(label="Delete", command=lambda: _delete_item(file_path))
    menu.add_separator()
    menu.add_command(label="Properties", command=lambda: _show_properties(file_path))


def _build_directory_menu(menu, dir_path):
    """Build context menu for directories"""
    menu.add_command(label="Open in File Explorer",
                     command=lambda: os.startfile(dir_path) if os.name == 'nt'
                     else os.system(f'xdg-open "{dir_path}"'))
    menu.add_separator()
    menu.add_command(label="New File", command=lambda: _create_new_file(dir_path))
    menu.add_command(label="New Folder", command=lambda: _create_new_folder(dir_path))
    menu.add_separator()
    menu.add_command(label="Copy Path", command=lambda: _copy_to_clipboard(dir_path))
    menu.add_command(label="Copy Relative Path", command=lambda: _copy_relative_path(dir_path))
    menu.add_separator()
    menu.add_command(label="Rename", command=lambda: _rename_item(dir_path))
    menu.add_command(label="Delete", command=lambda: _delete_item(dir_path))
    menu.add_separator()
    menu.add_command(label="Properties", command=lambda: _show_properties(dir_path))


def _copy_to_clipboard(path):
    """Copy path to clipboard"""
    tree.clipboard_clear()
    tree.clipboard_append(path)


def _create_new_file(dir_path):
    """Create new file in directory"""
    name = simpledialog.askstring("New File", "Enter file name:")
    if name:
        file_path = os.path.join(dir_path, name)
        try:
            with open(file_path, 'w') as f:
                f.write('')
            _refresh_tree()
        except Exception as e:
            messagebox.showerror("Error", f"Could not create file: {str(e)}")


def _create_new_folder(dir_path):
    """Create new folder in directory"""
    name = simpledialog.askstring("New Folder", "Enter folder name:")
    if name:
        folder_path = os.path.join(dir_path, name)
        try:
            os.makedirs(folder_path)
            _refresh_tree()
        except Exception as e:
            messagebox.showerror("Error", f"Could not create folder: {str(e)}")


def _rename_item(path):
    """Rename file or folder"""
    old_name = os.path.basename(path)
    new_name = simpledialog.askstring("Rename", "Enter new name:", initialvalue=old_name)
    if new_name and new_name != old_name:
        new_path = os.path.join(os.path.dirname(path), new_name)
        try:
            os.rename(path, new_path)
            _refresh_tree()
        except Exception as e:
            messagebox.showerror("Error", f"Could not rename: {str(e)}")


def _delete_item(path):
    """Delete file or folder"""
    item_type = "folder" if os.path.isdir(path) else "file"
    if messagebox.askyesno("Confirm Delete",
                           f"Are you sure you want to delete this {item_type}?\n{path}"):
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            _refresh_tree()
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete: {str(e)}")


def _show_properties(path):
    """Show properties of file or folder"""
    stats = os.stat(path)
    is_dir = os.path.isdir(path)

    info = f"{'Folder' if is_dir else 'File'} Properties\n\n"
    info += f"Name: {os.path.basename(path)}\n"
    info += f"Path: {path}\n"
    info += f"Size: {_format_size(stats.st_size)}\n"
    info += f"Created: {datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}\n"
    info += f"Modified: {datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}\n"
    info += f"Accessed: {datetime.fromtimestamp(stats.st_atime).strftime('%Y-%m-%d %H:%M:%S')}"

    messagebox.showinfo("Properties", info)


def _format_size(size):
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _refresh_tree():
    """Refresh the tree view"""
    root_items = tree.get_children('')
    if root_items:
        root_path = tree.item(root_items[0])['values'][0]
        update_tree(root_path)


# Bind right-click event
tree.bind("<Button-3>", show_context_menu)