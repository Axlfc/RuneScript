import subprocess
import argparse


def show_balloon_notification(
    task_name="Default Task",
    title="Task Notification",
    message_text="Your custom message here",
    message_duration=10,
    custom_icon_path=None,
):
    """
    show_balloon_notification

    Args:
        task_name (Any): Description of task_name.
        title (Any): Description of title.
        message_text (Any): Description of message_text.
        message_duration (Any): Description of message_duration.
        custom_icon_path (Any): Description of custom_icon_path.

    Returns:
        None: Description of return value.
    """
    icon_path_ps = (
        f"'{custom_icon_path}'"
        if custom_icon_path and custom_icon_path != "None"
        else "$null"
    )
    ps_script = f"\n    Add-Type -AssemblyName System.Windows.Forms\n    Add-Type -AssemblyName System.Drawing\n\n    $notifyIcon = New-Object System.Windows.Forms.NotifyIcon\n\n    if ({icon_path_ps} -and {icon_path_ps} -ne $null) {{\n        $icon = New-Object System.Drawing.Icon({icon_path_ps})\n        $notifyIcon.Icon = $icon\n    }} else {{\n        # Fallback to Application icon if no custom icon is provided\n        $notifyIcon.Icon = [System.Drawing.SystemIcons]::Application\n    }}\n\n    $notifyIcon.Visible = $True\n    $notifyIcon.BalloonTipTitle = '{title}'\n    $notifyIcon.BalloonTipText = '{message_text}'\n    $notifyIcon.ShowBalloonTip({message_duration * 1000})\n\n    Start-Sleep -Seconds {message_duration}\n    $notifyIcon.Dispose()\n    "
    subprocess.run(["powershell", "-Command", ps_script], check=True)


def main():
    """
    main

    Args:
        None

    Returns:
        None: Description of return value.
    """
    parser = argparse.ArgumentParser(description="Show balloon notification for tasks.")
    parser.add_argument("--task_name", default="Default Task", help="Name of the task")
    parser.add_argument(
        "--title", default="Task Notification", help="Title of the notification"
    )
    parser.add_argument(
        "--message",
        default="Your custom message here",
        help="The custom text to display in the notification",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=10,
        help="Duration of the notification in seconds",
    )
    parser.add_argument(
        "--custom-icon",
        default="None",
        help="Path to a custom icon (.ico file) for the notification",
    )
    args = parser.parse_args()
    show_balloon_notification(
        args.task_name, args.title, args.message, args.duration, args.custom_icon
    )


if __name__ == "__main__":
    main()
