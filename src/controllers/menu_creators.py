import os
from tkinter import Menu, messagebox

from src.controllers.parameters import read_config_parameter, write_config_parameter
from src.controllers.script_tasks import (
    render_markdown_to_html,
    generate_html_from_markdown,
    render_markdown_to_latex,
    run_javascript_analysis,
    analyze_generic_text_data,
    render_latex_to_pdf,
    generate_latex_pdf,
    change_interpreter,
    run_python_script,
    analyze_csv_data)
from src.views.tk_utils import local_python_var
#from src.controllers.menu_functions import open_create_venv_window



def create_submenu(parent_menu, title, entries):
    """ ""\"
    ""\"
    Creates a submenu with specified entries under the given parent menu.

    Parameters:
    parent_menu (Menu): The parent menu to which the submenu will be added.
    title (str): The title of the submenu.
    entries (dict): A dictionary of menu item labels and their corresponding command functions.

    Returns:
    None
    ""\"
    ""\" """
    submenu = Menu(parent_menu, tearoff=0)
    parent_menu.add_cascade(label=title, menu=submenu)
    for label, command in entries.items():
        submenu.add_command(label=label, command=command)


def create_csv_menu(parent_menu):
    """ ""\"
    ""\"
    Creates a submenu for CSV-related operations.

    This function adds specific options related to CSV files, such as data analysis, to the given parent menu.

    Parameters:
    parent_menu (Menu): The parent menu to which the CSV submenu will be added.

    Returns:
    None
    ""\"
    ""\" """
    entries = {"Analyze Data": analyze_csv_data}
    create_submenu(parent_menu, "CSV", entries)


def create_bash_menu(parent_menu):
    """ ""\"
    ""\"
    create_bash_menu

    Args:
        parent_menu (Any): Description of parent_menu.

    Returns:
        None: Description of return value.
    ""\"
    ""\" """
    parent_menu.add_command(label="Analyze Data")


def create_powershell_menu(parent_menu):
    """ ""\"
    ""\"
    create_powershell_menu

    Args:
        parent_menu (Any): Description of parent_menu.

    Returns:
        None: Description of return value.
    ""\"
    ""\" """
    parent_menu.add_command(label="Analyze Data")


def create_markdown_menu(parent_menu):
    """ ""\"
    ""\"
    create_markdown_menu

    Args:
        parent_menu (Any): Description of parent_menu.

    Returns:
        None: Description of return value.
    ""\"
    ""\" """
    entries = {
        "Render HTML": render_markdown_to_html,
        "Generate HTML": generate_html_from_markdown,
        "Render LaTeX PDF": render_markdown_to_latex,
    }
    create_submenu(parent_menu, "Markdown", entries)


def create_javascript_menu(parent_menu):
    """ ""\"
    ""\"
    create_javascript_menu

    Args:
        parent_menu (Any): Description of parent_menu.

    Returns:
        None: Description of return value.
    ""\"
    ""\" """
    entries = {"Analyze Data": run_javascript_analysis}
    create_submenu(parent_menu, "JavaScript", entries)


def create_html_menu(parent_menu):
    """ ""\"
    ""\"
    create_html_menu

    Args:
        parent_menu (Any): Description of parent_menu.

    Returns:
        None: Description of return value.
    ""\"
    ""\" """
    parent_menu.add_command(label="Analyze Data")


def create_css_menu(parent_menu):
    """ ""\"
    ""\"
    create_css_menu

    Args:
        parent_menu (Any): Description of parent_menu.

    Returns:
        None: Description of return value.
    ""\"
    ""\" """
    parent_menu.add_command(label="Analyze Data")


def create_java_menu(parent_menu):
    """ ""\"
    ""\"
    create_java_menu

    Args:
        parent_menu (Any): Description of parent_menu.

    Returns:
        None: Description of return value.
    ""\"
    ""\" """
    parent_menu.add_command(label="Analyze Data")


def create_cpp_menu(parent_menu):
    """ ""\"
    ""\"
    create_cpp_menu

    Args:
        parent_menu (Any): Description of parent_menu.

    Returns:
        None: Description of return value.
    ""\"
    ""\" """
    parent_menu.add_command(label="Analyze Data")


def create_generic_text_menu(parent_menu):
    """ ""\"
    ""\"
    create_generic_text_menu

    Args:
        parent_menu (Any): Description of parent_menu.

    Returns:
        None: Description of return value.
    ""\"
    ""\" """
    entries = {"Analyze Data": analyze_generic_text_data}
    create_submenu(parent_menu, "Text", entries)


def create_latex_menu(parent_menu):
    """ ""\"
    ""\"
    create_latex_menu

    Args:
        parent_menu (Any): Description of parent_menu.

    Returns:
        None: Description of return value.
    ""\"
    ""\" """
    entries = {"Render PDF": render_latex_to_pdf, "Generate PDF": generate_latex_pdf}
    create_submenu(parent_menu, "LaTeX", entries)


def create_python_menu(parent_menu):
    missing = read_config_parameter("options.project_settings.missing_dot_venv")

    python_menu = Menu(parent_menu, tearoff=0)
    parent_menu.add_cascade(label="Python", menu=python_menu)

    # Si NO hay .venv, solo mostramos "Create New Virtual Environmentâ€¦"
    if missing:
        from src.controllers.menu_functions import open_create_venv_window
        python_menu.add_command(
            label="Create New Virtual Environmentâ€¦",
            command=open_create_venv_window
        )
        return

    # â€”â€”â€”â€”â€”â€”â€”â€”â€” Si HAY venv, pintamos todo el menÃº completo â€”â€”â€”â€”â€”â€”â€”â€”â€”

    interpreters = read_config_parameter("options.project_settings.interpreters") or []
    current      = read_config_parameter("options.project_settings.current_interpreter") or ""

    # SubmenÃº de selecciÃ³n de intÃ©rprete
    interp_menu = Menu(python_menu, tearoff=0)
    python_menu.add_cascade(label="Select Interpreterâ€¦", menu=interp_menu)

    for interp in interpreters:
        path = interp["path"]
        name = interp["name"]
        interp_menu.add_radiobutton(
            label=name,
            value=path,
            variable=local_python_var,
            command=lambda p=path: _on_switch_interpreter(p))

    local_python_var.set(current)

    python_menu.add_separator()
    python_menu.add_command(
        label="Manage pip packagesâ€¦",
        command=lambda: change_interpreter(current)
    )
    python_menu.add_command(
        label="Install requirements.txtâ€¦",
        command=lambda: install_reqs(current)
    )
    python_menu.add_separator()
    from src.controllers.menu_functions import open_create_venv_window
    python_menu.add_command(
        label="Create New Virtual Environmentâ€¦",
        command=open_create_venv_window
    )

def _on_switch_interpreter(path):
    """
    Callback al seleccionar un nuevo intÃ©rprete.
    Actualiza la config y notifica al usuario.
    """
    write_config_parameter("options.project_settings.current_interpreter", path)
    messagebox.showinfo(
        "Interpreter switched",
        f"Active Python interpreter:\n{path}"
    )
