import os
import platform
import re
import subprocess
import sys
from time import sleep
from tkinter import messagebox, Toplevel, Text

from src.controllers.parameters import read_config_parameter
from src.controllers.utility_functions import validate_time
from src.views.tk_utils import (
    script_text,
    generate_stdin,
    generate_stdin_err,
    script_name_label,
    entry_arguments_entry,
    directory_label,
    root, my_font, localization_data
)


def get_execution_command(file_path, entry_arguments, interpreter_path=None):
    """ ""\"
    get_execution_command

    Args:
        file_path (Any): Description of file_path.
        entry_arguments (Any): Description of entry_arguments.

    Returns:
        None: Description of return value.
    ""\" """
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == ".py":
        python_executable = interpreter_path or ("python" if platform.system() == "Windows" else "python3")
        return [python_executable, file_path] + entry_arguments
    elif file_extension == ".sh":
        return ["bash", file_path] + entry_arguments
    elif file_extension == ".ps1":
        if platform.system() == "Windows":
            return [
                "C:\\Windows\\system32\\WindowsPowerShell\\v1.0\\powershell.exe",
                "-File",
                file_path,
            ] + entry_arguments
        else:
            return []
    elif file_extension == ".tex":
        return ["pdflatex", file_path] + entry_arguments
    elif file_extension == ".js":
        return ["node", file_path] + entry_arguments
    elif file_extension == ".html":
        return []
    elif file_extension == ".css":
        return []
    elif file_extension == ".csv":
        return []
    elif file_extension == ".txt":
        return []
    elif file_extension == ".java":
        return ["java", file_path] + entry_arguments
    elif file_extension == ".cpp":
        return [
            "g++",
            file_path,
            "-o",
            "outputfile",
            "&&",
            "./outputfile",
        ] + entry_arguments
    elif file_extension == ".rb":
        return ["ruby", file_path] + entry_arguments
    elif file_extension == ".pl":
        return ["perl", file_path] + entry_arguments
    elif file_extension == ".php":
        return ["php", file_path] + entry_arguments
    elif file_extension == ".ipynb":
        return ["jupyter", "notebook", file_path] + entry_arguments
    elif file_extension == ".swift":
        return ["swift", file_path] + entry_arguments
    elif file_extension == ".go":
        return ["go", "run", file_path] + entry_arguments
    elif file_extension == ".r":
        return ["Rscript", file_path] + entry_arguments
    elif file_extension == ".rs":
        return [
            "rustc",
            file_path,
            "&&",
            "./" + os.path.splitext(file_path)[0],
        ] + entry_arguments
    elif file_extension == ".dart":
        return ["dart", file_path] + entry_arguments
    else:
        return []


def run_script_windows():
    """ ""\"
    run_script_windows

    Args:
        None

    Returns:
        None: Description of return value.
    ""\" """
    script = script_text.get("1.0", "end-1c")
    entry_arguments = entry_arguments_entry.get().split()
    generate_stdout = generate_stdin.get()
    generate_stderr = generate_stdin_err.get()
    file_name_with_prefix = script_name_label.cget("text")
    file_name = file_name_with_prefix.replace(
        localization_data["script_name_label"], ""
    ).strip()
    current_directory = directory_label.cget("text")
    file_path = os.path.join(current_directory, file_name)

    interpreter_path = read_config_parameter("options.project_settings.current_interpreter")
    if not interpreter_path:
        messagebox.showwarning("No Interpreter Selected", "No valid interpreter has been set for the project.")
        return

    command = get_execution_command(file_path, entry_arguments, interpreter_path=interpreter_path)

    if not command:
        print(f"Cannot execute file: {file_name}")
        return
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE if generate_stdout else None,
        stderr=subprocess.PIPE if generate_stderr else None,
        text=True,
    )
    stdout_data, stderr_data = process.communicate()
    if generate_stdout:
        script_out_name = script_name_label.cget("text") + ".out"
        print(script_out_name)
        with open(script_out_name, "w+") as p:
            p.write(stdout_data)
    if generate_stderr:
        script_err_name = script_name_label.cget("text") + ".err"
        with open(script_err_name, "w+") as p:
            p.write(stderr_data)


def find_python_venv(project_dir):
    venv_names = ['.venv', 'venv']
    venv_python_paths = {
        'windows': [
            r'{}/Scripts/python.exe',
            r'{}/Scripts/python3.exe',
            r'{}/.venv/Scripts/python.exe',
            r'{}/.venv/Scripts/python3.exe'
        ],
        'unix': [
            '{}/bin/python3',
            '{}/bin/python',
            '{}/.venv/bin/python3',
            '{}/.venv/bin/python'
        ]
    }

    # Determinar el sistema operativo
    is_windows = os.name == 'nt'
    paths_to_check = venv_python_paths['windows'] if is_windows else venv_python_paths['unix']

    # Verificar rutas directas
    for venv_name in venv_names:
        for path_template in paths_to_check:
            venv_path = path_template.format(os.path.join(project_dir, venv_name))
            if os.path.exists(venv_path):
                return venv_path

    # Búsqueda recursiva más profunda
    for root, dirs, files in os.walk(project_dir):
        for dir_name in dirs:
            if dir_name in venv_names or 'venv' in dir_name.lower():
                for path_template in paths_to_check:
                    venv_path = path_template.format(os.path.join(root, dir_name))
                    if os.path.exists(venv_path):
                        return venv_path

    return None


def run_script_with_venv(script_path, arguments=None, project_dir=None):
    """
    Ejecuta un script de Python utilizando un entorno virtual si está disponible.

    Args:
        script_path (str): Ruta al script a ejecutar
        arguments (list, optional): Argumentos para el script
        project_dir (str, optional): Directorio del proyecto

    Returns:
        subprocess.CompletedProcess: Resultado de la ejecución del script
    """
    if project_dir is None:
        project_dir = os.path.dirname(script_path)

    # Buscar ejecutable de Python del entorno virtual
    venv_python = find_python_venv(project_dir)

    # Preparar comando de ejecución
    if venv_python:
        cmd = [venv_python, script_path]
    else:
        cmd = [sys.executable, script_path]

    # Añadir argumentos si están presentes
    if arguments:
        cmd.extend(arguments)

    try:
        # Ejecutar el script
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar el script: {e}")
        print(f"Salida de error: {e.stderr}")
        raise


def run_script():
    """ ""\"
    Executes the script present in the script_text widget.

    This function runs the script, capturing standard output and error if specified.
    It supports running scripts with additional arguments and reports the execution status.

    Parameters:
    None

    Returns:
    None
    ""\" """
    print("HOLAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
    script = script_text.get("1.0", "end-1c")
    arguments = entry_arguments_entry.get()
    generate_stdout = generate_stdin.get()
    generate_stderr = generate_stdin_err.get()
    try:
        print("WE ARE IN!!")
        print(script_name_label.cget("text"))
        print("YEAH!!")
        process = subprocess.Popen(
            ["bash"]
            + [directory_label.cget("text") + "/" + script_name_label.cget("text")]
            + arguments.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout_data, stderr_data = process.communicate()
        if generate_stdout:
            script_out_name = script_name_label.cget("text") + ".out"
            print(script_out_name)
            p = open(script_out_name, "w+")
            p.write(stdout_data.decode())
        if generate_stderr:
            script_err_name = script_name_label.cget("text") + ".err"
            p = open(script_err_name, "w+")
            p.write(stderr_data.decode())
        messagebox.showinfo("Script Execution", "Script executed successfully.")
    except Exception as e:
        messagebox.showerror("Script Execution", f"Error executing script:\n{str(e)}")


def run_script_with_timeout(timeout_seconds):
    """ ""\"
    Executes the script with a specified timeout.

    Runs the script and automatically stops it after the provided timeout period.
    It captures standard output and error based on the user's selection.

    Parameters:
    timeout_seconds (float): The duration in seconds after which the script is automatically stopped.

    Returns:
    None
    ""\" """
    script = script_text.get("1.0", "end-1c")
    arguments = entry_arguments_entry.get()
    generate_stdout = generate_stdin.get()
    generate_stderr = generate_stdin_err.get()
    try:
        process = subprocess.Popen(
            ["bash"]
            + [directory_label.cget("text") + "/" + script_name_label.cget("text")]
            + arguments.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        sleep(timeout_seconds)
        stdout_data, stderr_data = process.communicate()
        if generate_stdout:
            script_out_name = script_name_label.cget("text") + ".out"
            print(script_out_name)
            p = open(script_out_name, "w+")
            p.write(stdout_data.decode())
        if generate_stderr:
            script_err_name = script_name_label.cget("text") + ".err"
            p = open(script_err_name, "w+")
            p.write(stderr_data.decode())
        messagebox.showinfo("Script Execution", "Script executed successfully.")
    except Exception as e:
        messagebox.showerror("Script Execution", f"Error executing script:\n{str(e)}")


def run_script_once(schedule_time):
    """ ""\"
    Schedules the script for a one-time execution at a specified time.

    The function uses the 'at' command to schedule the script. It validates the provided time format
    and schedules the script accordingly, including redirection of output and error streams.

    Parameters:
    schedule_time (str): The time at which the script is scheduled to run (in HH:MM AM/PM format).

    Returns:
    None
    ""\" """
    script_path = os.path.join(
        directory_label.cget("text"), script_name_label.cget("text")
    )
    arguments = entry_arguments_entry.get()
    generate_stdout = generate_stdin.get()
    generate_stderr = generate_stdin_err.get()
    match = re.match("(\\d{1,2}):(\\d{2})\\s*(AM|PM|am|pm)?", schedule_time)
    if not match:
        messagebox.showerror(
            "Invalid Time", "Please enter a valid time in HH:MM AM/PM format."
        )
        return
    hour = int(match.group(1))
    minute = int(match.group(2))
    am_pm = match.group(3)
    if am_pm and am_pm.lower() == "pm" and hour != 12:
        hour += 12
    if am_pm and am_pm.lower() == "am" and hour == 12:
        hour = 0
    if not validate_time(hour, minute):
        return
    try:
        at_time = f"{hour:02d}:{minute:02d}"
        stdout_redirect = (
            f">{script_name_label.cget('text')}.out" if generate_stdout else "/dev/null"
        )
        stderr_redirect = (
            f"2>{script_name_label.cget('text')}.err"
            if generate_stderr
            else "/dev/null"
        )
        at_command = f"""atq; at {at_time} <<EOF
{script_path} {arguments} {stdout_redirect} {stderr_redirect}
EOF"""
        process = subprocess.Popen(at_command, shell=True)
        process.wait()
        messagebox.showinfo(
            "Script Scheduled", f"Script scheduled to run at {at_time}."
        )
    except Exception as e:
        messagebox.showerror(
            "Error Scheduling Script",
            f"""An error occurred while scheduling the script:
{str(e)}""",
        )


def run_script_crontab(minute, hour, day, month, day_of_week):
    """ ""\"
    Schedules the script using the crontab format.

    Sets up a cron job to execute the script at specified intervals. The function builds the cron schedule
    string based on provided parameters and configures output/error redirection.

    Parameters:
    minute, hour, day, month, day_of_week (str): Time parameters for scheduling the script in crontab format.

    Returns:
    None
    ""\" """
    if not minute or not hour or not day or not month or not day_of_week:
        messagebox.showerror(
            "Error Scheduling Script", "All cron schedule fields must be filled."
        )
        return
    cron_schedule = f"{minute} {hour} {day} {month} {day_of_week}"
    script_path = os.path.join(
        directory_label.cget("text"), script_name_label.cget("text")
    )
    arguments = entry_arguments_entry.get()
    generate_stdout = generate_stdin.get()
    generate_stderr = generate_stdin_err.get()
    out_file = os.path.join(
        directory_label.cget("text"), f"{script_name_label.cget('text')}.out"
    )
    err_file = os.path.join(
        directory_label.cget("text"), f"{script_name_label.cget('text')}.err"
    )
    try:
        stdout_redirect = f">{out_file}" if generate_stdout else "/dev/null"
        stderr_redirect = f"2>{err_file}" if generate_stderr else "/dev/null"
        crontab_command = f"(crontab -l; echo '{cron_schedule} {script_path} {arguments} {stdout_redirect} {stderr_redirect}') | crontab -"
        process = subprocess.Popen(crontab_command, shell=True)
        process.wait()
        messagebox.showinfo(
            "Script Scheduled", f"Script scheduled with cron: {cron_schedule}"
        )
    except Exception as e:
        messagebox.showerror(
            "Error Scheduling Script",
            f"""An error occurred while scheduling the script:
{str(e)}""",
        )


def see_stdout():
    """ ""\"
    Displays the standard output of the last executed script.

    Opens a new window to show the content of the script's stdout captured during the last execution.
    If the stdout file is not found, it indicates no available data.

    Parameters:
    None

    Returns:
    None
    ""\" """
    stdout_window = Toplevel(root)
    stdout_window.title("Standard Output (stdout)")
    stdout_text = Text(stdout_window, font=my_font)
    stdout_text.pack()
    script_out_name = script_name_label.cget("text") + ".out"
    try:
        with open(script_out_name, "r") as f:
            stdout_text.insert("1.0", f.read())
    except FileNotFoundError:
        stdout_text.insert("1.0", "No stdout data available.")


def see_stderr():
    """ ""\"
    Displays the standard error output of the last executed script.

    Opens a new window to show the content of the script's stderr captured during the last execution.
    If the stderr file is not found, it indicates no available data. The stderr text is displayed in red.

    Parameters:
    None

    Returns:
    None
    ""\" """
    stderr_window = Toplevel(root)
    stderr_window.title("Standard Error (stderr)")
    stderr_text = Text(stderr_window, font=my_font)
    stderr_text.pack()
    script_err_name = script_name_label.cget("text") + ".err"
    try:
        with open(script_err_name, "r") as f:
            stderr_text.insert("1.0", f.read())
    except FileNotFoundError:
        stderr_text.insert("1.0", "No stderr data available.")
    stderr_text.tag_configure("red", foreground="red")
    stderr_text.tag_add("red", "1.0", "end")


def get_operative_system():
    """ ""\"
    Populates the 'Jobs' submenu with options based on the operating system.

    For Windows, it adds an option to view scheduled tasks. For other systems, it adds options for 'at' and 'crontab' jobs.

    Parameters:
    submenu (Menu): The submenu to which the job options will be added.

    Returns:
    None
    ""\" """
    if platform.system() == "Windows":
        return "Windows"
    else:
        return platform.system()
