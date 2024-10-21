import subprocess
import argparse
import datetime
import re


windows_tasks_file_path = "C:\\Windows\\System32\\schtasks.exe"
windows_cmd_file_path = "C:\\Windows\\System32\\cmd.exe"


def format_time_input(time_str):
    
    parts = time_str.split(":")
    while len(parts) < 3:
        parts.append("00")
    formatted_parts = [str(int(part)).zfill(2) for part in parts]
    formatted_time_str = ":".join(formatted_parts)
    return datetime.datetime.strptime(formatted_time_str, "%H:%M:%S").time()


def parse_create_args(subparsers):
    
    parser_create = subparsers.add_parser("create")
    parser_create.add_argument("name")
    parser_create.add_argument("start_time")
    parser_create.add_argument("schedule_type")
    parser_create.add_argument("--interval", default=None)
    parser_create.add_argument("--program", default=None)


def parse_delete_args(subparsers):
    
    parser_delete = subparsers.add_parser("delete")
    parser_delete.add_argument("name")


def parse_list_args(subparsers):
    
    subparsers.add_parser("list")


def parse_change_args(subparsers):
    
    parser_change = subparsers.add_parser("change")
    parser_change.add_argument("name")
    parser_change.add_argument("--program", default=None)
    parser_change.add_argument("--start_time", default=None)


def parse_run_args(subparsers):
    
    parser_run = subparsers.add_parser("run")
    parser_run.add_argument("name")


def parse_end_args(subparsers):
    
    parser_end = subparsers.add_parser("end")
    parser_end.add_argument("name")


def parse_showsid_args(subparsers):
    
    parser_showsid = subparsers.add_parser("showsid")
    parser_showsid.add_argument("name")


def parse_at_args(subparsers):
    
    parser_at = subparsers.add_parser("at")
    parser_at.add_argument("name")
    parser_at.add_argument("start_time")
    parser_at.add_argument("program")


def parse_crontab_args(subparsers):
    
    parser_crontab = subparsers.add_parser("crontab")
    parser_crontab.add_argument("name")
    parser_crontab.add_argument("minute")
    parser_crontab.add_argument("hour")
    parser_crontab.add_argument("day")
    parser_crontab.add_argument("month")
    parser_crontab.add_argument("day_of_week")
    parser_crontab.add_argument("script_path")


def process_parse_args():
    
    parser = argparse.ArgumentParser(description="Task Scheduler Wrapper")
    subparsers = parser.add_subparsers(dest="command")
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
    
    command = [windows_tasks_file_path, "/Delete", "/TN", name, "/F"]
    try:
        subprocess.run(command, check=True)
        print(f"Successfully deleted task: {name}")
    except subprocess.CalledProcessError as e:
        print(f"Error deleting task: {e}")


def list_tasks():
    
    excluded_folders = [
        "\\Microsoft",
        "\\Adobe",
        "\\PowerToys",
        "\\Mozilla",
        "\\MEGA",
        "\\Opera",
        "\\NVIDIA",
        "\\NvTmRep",
        "\\NvProfileUpdaterOnLogon_",
        "\\NvProfileUpdaterDaily_",
        "\\NvNodeLauncher_",
        "\\NvDriverUpdateCheckDaily_",
        "\\NahimicTask",
        "\\NahimicSvc",
        "\\Dragon_Center",
        "\\MSI_Dragon",
        "\\MSISCMTsk",
        "\\MSIAfterburner",
        "\\CreateExplorerShellUnelevatedTask",
        "\\ViGEmBus",
        "\\GoogleSystem",
    ]
    list_command = [windows_tasks_file_path, "/Query", "/FO", "LIST"]
    process = subprocess.Popen(
        list_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    output, error = process.communicate()
    if error:
        print("Error:", error)
        return []
    tasks = output.strip().split("\n\n")
    filtered_tasks = [
        task for task in tasks if not any(folder in task for folder in excluded_folders)
    ]
    detailed_task_info = []
    for task in filtered_tasks:
        task_name_match = re.search(
            "Nombre de tarea:(\\s*\\\\[^\\\\]+\\\\)?\\s*([^\\r\\n]+)", task
        )
        if task_name_match:
            task_name = task_name_match.group(2).strip()
            detail_command = [
                windows_tasks_file_path,
                "/Query",
                "/TN",
                task_name,
                "/V",
                "/FO",
                "LIST",
            ]
            detail_process = subprocess.Popen(
                detail_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            detail_output, detail_error = detail_process.communicate()
            if detail_error:
                print(f"Error getting details for task {task_name}: {detail_error}")
            else:
                command_match = re.search(
                    "Tarea que se ejecutar\xa0:\\s*([^\\r\\n]+)", detail_output
                )
                command = (
                    command_match.group(1).strip()
                    if command_match
                    else "Unknown Command"
                )
                next_run_time_match = re.search(
                    "Hora pr¢xima ejecuci¢n:\\s*([^\\r\\n]+)", detail_output
                )
                next_run_time = (
                    next_run_time_match.group(1).strip()
                    if next_run_time_match
                    else "Unknown Next Run Time"
                )
                task_name = task_name.split("\\")[1]
                detailed_task_info.append(
                    f'"{task_name}": ({command}) - {next_run_time}'
                )
     ""\"
    ""\"
    ""\"
    ""\"
    Changes properties of an existing scheduled task.

        Parameters:
        name (str): The name of the task to change.
        program (str, optional): The new program path for the task.
        start_time (str, optional): The new start time for the task.

        Returns:
        None
    ""\"
    ""\"
    ""\"
    ""\"  ""\"
    ""\"
    ""\"
    ""\"
    Runs a scheduled task on demand.

        Parameters:
        name (str): The name of the task to run.

        Returns:
        None
    ""\"
    ""\"
    ""\"
    ""\"  ""\"
    ""\"
    ""\"
    ""\"
    Ends a currently running scheduled task.

        Parameters:
        name (str): The name of the task to end.

        Returns:
        None
    ""\"
    ""\"
    ""\"
    ""\"  ""\"
    ""\"
    ""\"
    ""\"
    Displays the security identifier (SID) for a scheduled task.

        Parameters:
        name (str): The name of the task.

        Returns:
        None
    ""\"
    ""\"
    ""\"
    ""\"  ""\"
    ""\"
    ""\"
    ""\"
    Creates a new scheduled task.

        Parameters:
        name (str): The name of the new task.
        start_time (str): The start time for the task.
        schedule_type (str, optional): The type of schedule (e.g., daily, weekly).
        interval (str, optional): The interval for the task repetition.
        program (str, optional): The program path to execute.

        Returns:
        None
    ""\"
    ""\"
    ""\"
    ""\"  ""\"
    ""\"
    ""\"
    ""\"
    Creates a task that deletes itself after execution.

        Parameters:
        name (str): The name of the task.
        start_time (str): The start time for the task.
        program (str): The program path to execute.

        Returns:
        None
    ""\"
    ""\"
    ""\"
    ""\"  ""\"
    ""\"
    ""\"
    ""\"
    Creates a task using 'at' command with a self-deleting feature.

        Parameters:
        name (str): The name of the task.
        start_time (str): The start time for the task in HH:MM format.
        program (str): The program path to execute.

        Returns:
        None
    ""\"
    ""\"
    ""\"
    ""\"  ""\"
    ""\"
    ""\"
    ""\"
    Creates a scheduled task using crontab-like syntax.

        Parameters:
        task_name (str): The name of the task.
        minute (str): Minute part of the schedule.
        hour (str): Hour part of the schedule.
        day (str): Day part of the schedule.
        month (str): Month part of the schedule.
        day_of_week (str): Day of the week part of the schedule.
        script_path (str): The script path to execute.

        Returns:
        bool: True if the task was created successfully, False otherwise.
    ""\"
    ""\"
    ""\"
    ""\"  ""\"
    ""\"
    ""\"
    ""\"
    Main function to process command line arguments and execute corresponding task scheduler functions.

        Returns:
        None
    ""\"
    ""\"
    ""\"
    ""\" """
    args = process_parse_args()
    if args.command == "create":
        create_task(
            args.name, args.start_time, args.schedule_type, args.interval, args.program
        )
    elif args.command == "delete":
        delete_task(args.name)
    elif args.command == "list":
        list_tasks()
    elif args.command == "change":
        change_task(args.name, args.program, args.start_time)
    elif args.command == "run":
        run_task(args.name)
    elif args.command == "end":
        end_task(args.name)
    elif args.command == "showsid":
        showsid_task(args.name)
    elif args.command == "at":
        at_function(args.name, args.start_time, args.program)
    elif args.command == "crontab":
        crontab_function(
            args.name,
            args.minute,
            args.hour,
            args.day,
            args.month,
            args.day_of_week,
            args.script_path,
        )


if __name__ == "__main__":
    main()
