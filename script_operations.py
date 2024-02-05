import os
import re
import subprocess
from time import sleep
from tkinter import messagebox, Toplevel, Text

from tk_utils import script_text, generate_stdin, generate_stdin_err, script_name_label, entry_arguments_entry, \
    directory_label, root
from utility_functions import validate_time


def run_script():
    script = script_text.get("1.0", "end-1c")
    arguments = entry_arguments_entry.get()
    generate_stdout = generate_stdin.get()
    generate_stderr = generate_stdin_err.get()

    try:
        # Execute the script with provided arguments
        # Use the subprocess module to run the script as a separate process
        # result = subprocess.run([script] + arguments.split(), capture_output=True, shell=True)
        # TODO "/"
        process = subprocess.Popen(["bash"] + [directory_label.cget('text') + "/" + script_name_label.cget('text')] + arguments.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout_data, stderr_data = process.communicate()

        # Print the stdout and stderr
        if generate_stdout:
            script_out_name = script_name_label.cget('text') + ".out"
            print(script_out_name)
            p = open(script_out_name, "w+")
            p.write(stdout_data.decode())

        if generate_stderr:
            script_err_name = script_name_label.cget('text') + ".err"
            p = open(script_err_name, "w+")
            p.write(stderr_data.decode())

        messagebox.showinfo("Script Execution", "Script executed successfully.")
    except Exception as e:
        messagebox.showerror("Script Execution", f"Error executing script:\n{str(e)}")


def run_script_with_timeout(timeout_seconds):
    script = script_text.get("1.0", "end-1c")
    arguments = entry_arguments_entry.get()
    generate_stdout = generate_stdin.get()
    generate_stderr = generate_stdin_err.get()

    try:
        # Execute the script with provided arguments
        # Use the subprocess module to run the script as a separate process
        # result = subprocess.run([script] + arguments.split(), capture_output=True, shell=True)
        # TODO "/"
        process = subprocess.Popen(
            ["bash"] + [directory_label.cget('text') + "/" + script_name_label.cget('text')] + arguments.split(),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        sleep(timeout_seconds)
        stdout_data, stderr_data = process.communicate()

        # Print the stdout and stderr
        if generate_stdout:
            script_out_name = script_name_label.cget('text') + ".out"
            print(script_out_name)
            p = open(script_out_name, "w+")
            p.write(stdout_data.decode())

        if generate_stderr:
            script_err_name = script_name_label.cget('text') + ".err"
            p = open(script_err_name, "w+")
            p.write(stderr_data.decode())

        messagebox.showinfo("Script Execution", "Script executed successfully.")
    except Exception as e:
        messagebox.showerror("Script Execution", f"Error executing script:\n{str(e)}")


def run_script_once(schedule_time):
    script_path = os.path.join(directory_label.cget('text'), script_name_label.cget('text'))
    arguments = entry_arguments_entry.get()
    generate_stdout = generate_stdin.get()
    generate_stderr = generate_stdin_err.get()

    # Extract hour, minute, and AM/PM from the input time string
    match = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?', schedule_time)
    if not match:
        messagebox.showerror("Invalid Time", "Please enter a valid time in HH:MM AM/PM format.")
        return

    hour = int(match.group(1))
    minute = int(match.group(2))
    am_pm = match.group(3)

    # Adjust hour for 12-hour clock format
    if am_pm and am_pm.lower() == 'pm' and hour != 12:
        hour += 12

    if am_pm and am_pm.lower() == 'am' and hour == 12:
        hour = 0

    if not validate_time(hour, minute):
        return

    try:
        # Use the 'at' command to schedule the script execution and redirection
        at_time = f"{hour:02d}:{minute:02d}"

        stdout_redirect = f">{script_name_label.cget('text')}.out" if generate_stdout else "/dev/null"
        stderr_redirect = f"2>{script_name_label.cget('text')}.err" if generate_stderr else "/dev/null"

        at_command = f"atq; at {at_time} <<EOF\n{script_path} {arguments} {stdout_redirect} {stderr_redirect}\nEOF"

        process = subprocess.Popen(at_command, shell=True)
        process.wait()

        messagebox.showinfo("Script Scheduled", f"Script scheduled to run at {at_time}.")
    except Exception as e:
        messagebox.showerror("Error Scheduling Script", f"An error occurred while scheduling the script:\n{str(e)}")


def run_script_crontab(minute, hour, day, month, day_of_week):
    if not minute or not hour or not day or not month or not day_of_week:
        messagebox.showerror("Error Scheduling Script", "All cron schedule fields must be filled.")
        return

    # Build the cron schedule string
    cron_schedule = f"{minute} {hour} {day} {month} {day_of_week}"

    script_path = os.path.join(directory_label.cget('text'), script_name_label.cget('text'))
    arguments = entry_arguments_entry.get()

    generate_stdout = generate_stdin.get()
    generate_stderr = generate_stdin_err.get()

    # Determine the full path for .out and .err files based on the selected directory
    out_file = os.path.join(directory_label.cget('text'), f"{script_name_label.cget('text')}.out")
    err_file = os.path.join(directory_label.cget('text'), f"{script_name_label.cget('text')}.err")

    try:
        stdout_redirect = f">{out_file}" if generate_stdout else "/dev/null"
        stderr_redirect = f"2>{err_file}" if generate_stderr else "/dev/null"

        # Use the 'crontab' command to set up the script execution schedule
        crontab_command = f"(crontab -l; echo '{cron_schedule} {script_path} {arguments} {stdout_redirect} {stderr_redirect}') | crontab -"
        process = subprocess.Popen(crontab_command, shell=True)
        process.wait()

        messagebox.showinfo("Script Scheduled", f"Script scheduled with cron: {cron_schedule}")
    except Exception as e:
        messagebox.showerror("Error Scheduling Script", f"An error occurred while scheduling the script:\n{str(e)}")


def see_stdout():
    stdout_window = Toplevel(root)
    stdout_window.title("Standard Output (stdout)")
    stdout_text = Text(stdout_window)
    stdout_text.pack()

    script_out_name = script_name_label.cget('text') + ".out"
    try:
        with open(script_out_name, "r") as f:
            stdout_text.insert("1.0", f.read())
    except FileNotFoundError:
        stdout_text.insert("1.0", "No stdout data available.")


def see_stderr():
    stderr_window = Toplevel(root)
    stderr_window.title("Standard Error (stderr)")
    stderr_text = Text(stderr_window)
    stderr_text.pack()

    script_err_name = script_name_label.cget('text') + ".err"
    try:
        with open(script_err_name, "r") as f:
            stderr_text.insert("1.0", f.read())
    except FileNotFoundError:
        stderr_text.insert("1.0", "No stderr data available.")

    # Configure the text widget to use red font color
    stderr_text.tag_configure("red", foreground="red")
    stderr_text.tag_add("red", "1.0", "end")

