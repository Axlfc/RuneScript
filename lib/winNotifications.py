import subprocess
import argparse


#  USAGE: python .\lib\winNotifications.py --task_name "My Task" --title "Reminder" --duration 20 --custom-icon "C:\Users\user\Desktop\axl.ico" --message "Your custom message here"

def show_balloon_notification(task_name="Default Task", title="Task Notification", message_text="Your custom message here", message_duration=10, custom_icon_path=None):
    # Ensure the PowerShell script correctly handles the icon path.
    icon_path_ps = f"'{custom_icon_path}'" if custom_icon_path and custom_icon_path != 'None' else "$null"

    ps_script = f"""
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing

    $notifyIcon = New-Object System.Windows.Forms.NotifyIcon

    if ({icon_path_ps} -and {icon_path_ps} -ne $null) {{
        $icon = New-Object System.Drawing.Icon({icon_path_ps})
        $notifyIcon.Icon = $icon
    }} else {{
        # Fallback to Application icon if no custom icon is provided
        $notifyIcon.Icon = [System.Drawing.SystemIcons]::Application
    }}

    $notifyIcon.Visible = $True
    $notifyIcon.BalloonTipTitle = '{title}'
    $notifyIcon.BalloonTipText = '{message_text}'
    $notifyIcon.ShowBalloonTip({message_duration * 1000})

    Start-Sleep -Seconds {message_duration}
    $notifyIcon.Dispose()
    """

    subprocess.run(['powershell', '-Command', ps_script], check=True)


def main():
    parser = argparse.ArgumentParser(description="Show balloon notification for tasks.")
    parser.add_argument("--task_name", default="Default Task", help="Name of the task")
    parser.add_argument("--title", default="Task Notification", help="Title of the notification")
    parser.add_argument("--message", default="Your custom message here", help="The custom text to display in the notification")
    parser.add_argument("--duration", type=int, default=10, help="Duration of the notification in seconds")
    parser.add_argument("--custom-icon", default="None", help="Path to a custom icon (.ico file) for the notification")

    args = parser.parse_args()

    show_balloon_notification(args.task_name, args.title, args.message, args.duration, args.custom_icon)


if __name__ == '__main__':
    main()
