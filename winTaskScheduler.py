import subprocess
import argparse
import datetime
import re

'''
Lista de parámetros: 
x /Create         Crea una nueva tarea programada.
x /Delete         Elimina las tareas programadas.
x /Query          Muestra todas las tareas programadas.
/Change         Cambia las propiedades de la tarea programada.
/Run            Ejecuta la tarea programada a petición.
/End            Detiene la tarea programada que se está ejecutando actualmente.
/ShowSid        Muestra el identificador de seguridad correspondiente al nombre de una tarea programada.

'''

windows_tasks_file_path = 'C:\\Windows\\System32\\schtasks.exe'
windows_cmd_file_path = 'C:\\Windows\\System32\\cmd.exe'


def format_time_input(time_str):
    """
    Formats the time input to HH:MM:SS format and returns a datetime.time object.
    If hours, minutes, or seconds are missing, defaults them to '00'.
    Examples:
        '8' -> '08:00:00'
        '8:30' -> '08:30:00'
        '8:8:8' -> '08:08:08'
    """
    # Split the input string by ':' and extend it to 3 elements if necessary
    parts = time_str.split(':')
    while len(parts) < 3:
        parts.append('00')

    # Convert each part to integer and format with leading zeros
    formatted_parts = [str(int(part)).zfill(2) for part in parts]

    # Join the parts and convert to a datetime.time object
    formatted_time_str = ':'.join(formatted_parts)
    return datetime.datetime.strptime(formatted_time_str, '%H:%M:%S').time()


def parse_create_args(subparsers):
    parser_create = subparsers.add_parser('create')
    parser_create.add_argument('name')
    parser_create.add_argument('start_time')
    parser_create.add_argument('schedule_type')
    parser_create.add_argument('--interval', default=None)
    parser_create.add_argument('--program', default=None)


def parse_delete_args(subparsers):
    parser_delete = subparsers.add_parser('delete')
    parser_delete.add_argument('name')


def parse_list_args(subparsers):
    subparsers.add_parser('list')


def parse_change_args(subparsers):
    parser_change = subparsers.add_parser('change')
    parser_change.add_argument('name')
    parser_change.add_argument('--program', default=None)
    parser_change.add_argument('--start_time', default=None)


def parse_run_args(subparsers):
    parser_run = subparsers.add_parser('run')
    parser_run.add_argument('name')


def parse_end_args(subparsers):
    parser_end = subparsers.add_parser('end')
    parser_end.add_argument('name')


def parse_showsid_args(subparsers):
    parser_showsid = subparsers.add_parser('showsid')
    parser_showsid.add_argument('name')


def parse_at_args(subparsers):
    parser_at = subparsers.add_parser('at')
    parser_at.add_argument('start_time')
    parser_at.add_argument('program')


def parse_crontab_args(subparsers):
    parser_crontab = subparsers.add_parser('crontab')
    parser_crontab.add_argument('minute')
    parser_crontab.add_argument('hour')
    parser_crontab.add_argument('day')
    parser_crontab.add_argument('month')
    parser_crontab.add_argument('day_of_week')
    parser_crontab.add_argument('script_path')


def process_parse_args():
    parser = argparse.ArgumentParser(description="Task Scheduler Wrapper")
    subparsers = parser.add_subparsers(dest='command')

    # Parsing argument for each sub-command
    parse_create_args(subparsers)
    parse_delete_args(subparsers)
    parse_list_args(subparsers)
    parse_change_args(subparsers)
    parse_run_args(subparsers)
    parse_end_args(subparsers)
    parse_showsid_args(subparsers)
    parse_at_args(subparsers)
    parse_crontab_args(subparsers)

    return parser.parse_args()


def delete_task(name):
    command = [windows_tasks_file_path, '/Delete', '/TN', name, '/F']
    try:
        subprocess.run(command, check=True)
        print(f'Successfully deleted task: {name}')
    except subprocess.CalledProcessError as e:
        print(f'Error deleting task: {e}')


def list_tasks():
    excluded_folders = [
        '\\Microsoft',
        '\\Adobe',
        '\\PowerToys',
        '\\Mozilla',
        '\\MEGA',
        '\\Opera',
        '\\NVIDIA',
        '\\NvTmRep',
        '\\NvProfileUpdaterOnLogon_',
        '\\NvProfileUpdaterDaily_',
        '\\NvNodeLauncher_',
        '\\NvDriverUpdateCheckDaily_',
        '\\NahimicTask',
        '\\NahimicSvc',
        '\\Dragon_Center',
        '\\MSI_Dragon',
        '\\MSISCMTsk',
        '\\MSIAfterburner',
        '\\CreateExplorerShellUnelevatedTask',
        '\\ViGEmBus',
        '\\GoogleSystem',

    ]

    # Initial command to get the list of tasks
    list_command = [windows_tasks_file_path, '/Query', '/FO', 'LIST']
    process = subprocess.Popen(list_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Read the output and error streams
    output, error = process.communicate()

    # Check for errors and print them
    if error:
        print("Error:", error)
        return []  # Return an empty list in case of error

    # Split the output by empty lines (each task is separated by an empty line)
    tasks = output.strip().split('\n\n')

    # Filter tasks not in the excluded folders
    filtered_tasks = [task for task in tasks if not any(folder in task for folder in excluded_folders)]

    detailed_task_info = []

    # Iterate over each task and get detailed information including the command
    for task in filtered_tasks:
        task_name_match = re.search(r"Nombre de tarea:(\s*\\[^\\]+\\)?\s*([^\r\n]+)", task)
        if task_name_match:
            task_name = task_name_match.group(2).strip()
            # Fetch detailed info for each task
            detail_command = [windows_tasks_file_path, '/Query', '/TN', task_name, '/V', '/FO', 'LIST']
            detail_process = subprocess.Popen(detail_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            detail_output, detail_error = detail_process.communicate()

            if detail_error:
                print(f"Error getting details for task {task_name}: {detail_error}")
            else:
                # Extract the command or script path
                command_match = re.search(r"Acción:\s*([^\r\n]+)", detail_output)
                command = command_match.group(1).strip() if command_match else "Unknown Command"
                # Extract the next run time
                next_run_time_match = re.search(r"Hora pr¢xima ejecuci¢n:\s*([^\r\n]+)", detail_output)
                next_run_time = next_run_time_match.group(1).strip() if next_run_time_match else "Unknown Next Run Time"
                detailed_task_info.append(f"Task Name: {task_name}, Command: {command}, Next Run Time: {next_run_time}")
    # return detailed_task_info

    # Print the filtered_tasks
    for task in filtered_tasks:
        print(task)
        print('-' * 80)  # Separator for readability

    return detailed_task_info
    #  return filtered_tasks  # Return the filtered list of tasks


def change_task(name, program=None, start_time=None):
    command = [windows_tasks_file_path, '/Change', '/TN', name]
    if program:
        command.extend(['/TR', program])
    if start_time:
        command.extend(['/ST', start_time])
    subprocess.run(command, check=True)


def run_task(name):
    command = [windows_tasks_file_path, '/Run', '/TN', name]
    subprocess.run(command, check=True)


def end_task(name):
    command = [windows_tasks_file_path, '/End', '/TN', name]
    subprocess.run(command, check=True)


def showsid_task(name):
    command = [windows_tasks_file_path, '/ShowSid', '/TN', name]
    subprocess.run(command, check=True)


def create_task(name, start_time, schedule_type=None, interval=None, program=None):
    command = [windows_tasks_file_path, '/Create', '/TN', name, '/ST', start_time]
    if interval:
        command.extend(['/MO', interval])
    if program:
        command.extend(['/TR', program])
    if schedule_type:
        command.extend(['/SC', schedule_type])

    subprocess.run(command, check=True)


def create_self_deleting_task(name, start_time, program):
    # Ensure the program path is correctly quoted
    program_path = f'"{program}"' if ' ' in program else program

    # Command to delete the task after execution
    delete_command = f' && {windows_tasks_file_path} /Delete /TN "{name}" /f'

    # Full command combining program execution and task deletion, running silently
    full_command = f'{windows_cmd_file_path} /c start /b {program_path}{delete_command}'

    # Task creation command
    command = [windows_tasks_file_path, '/Create', '/TN', name, '/ST', start_time, '/TR', full_command, '/SC', 'ONCE']

    # Execute the command
    try:
        subprocess.run(command, check=True)
        print(f"Self-deleting task '{name}' created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error creating self-deleting task: {e}")


def at_function(start_time, program):
    formatted_start_time = format_time_input(start_time)
    current_time = datetime.datetime.now().time()

    if formatted_start_time < current_time:
        print("Error: The specified time is earlier than the current time.")
        return

    formatted_start_time_str = formatted_start_time.strftime('%H:%M:%S')
    task_name = f"{formatted_start_time.strftime('%H%M')}"

    create_self_deleting_task(task_name, formatted_start_time_str, program)


def crontab_function(minute, hour, day, month, day_of_week, script_path):
    # Task name
    task_name = "ScheduledScript"

    # Ensure the script path is correctly quoted
    script_path = f'"{script_path}"' if ' ' in script_path else script_path

    # Determine the schedule type and additional arguments
    if day_of_week != "*":
        schedule_type = "/SC WEEKLY"
        day_argument = f"/D {day_of_week.upper()}"
    elif day != "*":
        schedule_type = "/SC MONTHLY"
        day_argument = f"/D {day}"
    elif month != "*":
        schedule_type = "/SC MONTHLY"
        day_argument = ""  # no specific day, runs on the first day of the month
    else:
        # If no specific day, week, or month, defaults to daily
        schedule_type = "/SC DAILY"
        day_argument = ""

    # Add month argument if specific months are defined
    month_argument = f"/M {month.upper()}" if month != "*" else ""

    # Format start time
    start_time = f"{hour}:{minute}" if hour != "*" and minute != "*" else "00:00"

    # Full command for creating the task
    full_command = f'schtasks /Create /TN "{task_name}" /TR {script_path} {schedule_type} {day_argument} {month_argument} /ST {start_time} /F'

    # Execute the command
    try:
        subprocess.run(full_command, check=True, shell=True)
        print("Scheduled task created successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating scheduled task: {e}")
        return False


def main():
    args = process_parse_args()

    if args.command == 'create':
        create_task(args.name, args.start_time, args.schedule_type, args.interval, args.program)
    elif args.command == 'delete':
        delete_task(args.name)
    elif args.command == 'list':
        list_tasks()
    elif args.command == 'change':
        change_task(args.name, args.program, args.start_time)
    elif args.command == 'run':
        run_task(args.name)
    elif args.command == 'end':
        end_task(args.name)
    elif args.command == 'showsid':
        showsid_task(args.name)
    elif args.command == 'at':
        at_function(args.start_time, args.program)
    elif args.command == 'crontab':
        crontab_function(args.minute, args.hour, args.day, args.month, args.day_of_week, args.script_path)


if __name__ == '__main__':
    main()
