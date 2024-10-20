import json
import multiprocessing
import os
import platform
import queue
import re
import subprocess
import threading
import math
import cmath
from tkinter import (
    colorchooser,
    END,
    Toplevel,
    Label,
    Entry,
    Button,
    scrolledtext,
    IntVar,
    Menu,
    StringVar,
    messagebox,
    OptionMenu,
    Checkbutton,
    Scrollbar,
    Canvas,
    Frame,
    font,
    filedialog,
    Listbox,
    simpledialog,
    Text,
    DISABLED,
    NORMAL,
    SUNKEN,
    W,
    BOTH,
    LEFT,
    SINGLE,
    X,
    RAISED,
    WORD,
    RIGHT,
    Y,
    BooleanVar,
    VERTICAL,
    BOTTOM,
    INSERT,
    SEL_FIRST,
    SEL_LAST,
)
import webview
from datetime import datetime
from tkinter.ttk import Separator, Treeview, Notebook, Combobox
import markdown
from PIL import ImageTk
from PIL.Image import Image
from tkhtmlview import HTMLLabel
from src.controllers.parameters import read_config_parameter, write_config_parameter
from src.views.tk_utils import text, script_text, root, style, current_session
from src.controllers.utility_functions import make_tag
from src.views.ui_elements import Tooltip, ScrollableFrame
from src.models.ai_assistant import find_gguf_file
from src.views.edit_operations import cut, copy, paste, duplicate
from lib.git import git_icons

git_console_instance = None


def load_themes_from_json(file_path):
    """
    load_themes_from_json

    Args:
        file_path (Any): Description of file_path.

    Returns:
        None: Description of return value.
    """
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            return data.get("themes", [])
    except FileNotFoundError:
        messagebox.showerror("Error", "Themes file not found.")
        return []
    except json.JSONDecodeError:
        messagebox.showerror("Error", "Error decoding themes file.")
        return []


def change_color():
    """
    Changes the text color in the application's text widget.

    This function opens a color chooser dialog, allowing the user to select a new color for the text.
    It then applies this color to the text within the text widget.

    Parameters:
    None

    Returns:
    None
    """
    color = colorchooser.askcolor(initialcolor="#ff0000")
    color_name = color[1]
    global fontColor
    fontColor = color_name
    current_tags = text.tag_names()
    if "font_color_change" in current_tags:
        text.tag_delete("font_color_change", 1.0, END)
    else:
        text.tag_add("font_color_change", 1.0, END)
    make_tag()


def colorize_text():
    """
    Applies color to the text in the script text widget.

    This function retrieves the current content of the script text widget, deletes it, and reinserts it,
    applying the currently selected color.

    Parameters:
    None

    Returns:
    None
    """
    script_content = script_text.get("1.0", "end")
    script_text.delete("1.0", "end")
    script_text.insert("1.0", script_content)


def check(value):
    """
    Highlights all occurrences of a specified value in the script text widget.

    This function searches for the given value in the script text widget and applies a 'found' tag with a
    yellow background to each occurrence.

    Parameters:
    value (str): The string to be searched for in the text widget.

    Returns:
    None
    """
    script_text.tag_remove("found", "1.0", END)
    if value:
        script_text.tag_config("found", background="yellow")
        idx = "1.0"
        while idx:
            idx = script_text.search(value, idx, nocase=1, stopindex=END)
            if idx:
                lastidx = f"{idx}+{len(value)}c"
                script_text.tag_add("found", idx, lastidx)
                idx = lastidx


def search_and_replace(search_text, replace_text):
    """
    Replaces all occurrences of a specified search text with a replacement text in the script text widget.

    This function finds each occurrence of the search text and replaces it with the provided replacement text.

    Parameters:
    search_text (str): The text to be replaced.
    replace_text (str): The text to replace the search text.

    Returns:
    None
    """
    if search_text:
        start_index = "1.0"
        while True:
            start_index = script_text.search(
                search_text, start_index, nocase=1, stopindex=END
            )
            if not start_index:
                break
            end_index = f"{start_index}+{len(search_text)}c"
            script_text.delete(start_index, end_index)
            script_text.insert(start_index, replace_text)
            start_index = end_index


def find_text(event=None):
    """
    Opens a dialog for finding text within the script text widget.

    This function creates a new window with an entry field where the user can input a text string
    to find in the script text widget.

    Parameters:
    event (Event, optional): The event that triggered this function.

    Returns:
    None
    """
    search_toplevel = Toplevel(root)
    search_toplevel.title("Find Text")
    search_toplevel.transient(root)
    search_toplevel.resizable(False, False)
    Label(search_toplevel, text="Find All:").grid(row=0, column=0, sticky="e")
    search_entry_widget = Entry(search_toplevel, width=25)
    search_entry_widget.grid(row=0, column=1, padx=2, pady=2, sticky="we")
    search_entry_widget.focus_set()
    Button(
        search_toplevel,
        text="Ok",
        underline=0,
        command=lambda: check(search_entry_widget.get()),
    ).grid(row=0, column=2, sticky="e" + "w", padx=2, pady=5)
    Button(
        search_toplevel,
        text="Cancel",
        underline=0,
        command=lambda: find_text_cancel_button(search_toplevel),
    ).grid(row=0, column=4, sticky="e" + "w", padx=2, pady=2)


def find_text_cancel_button(search_toplevel):
    """
    Removes search highlights and closes the search dialog.

    This function is called to close the search dialog and remove any search highlights
    from the text widget.

    Parameters:
    search_toplevel (Toplevel): The top-level widget of the search dialog.

    Returns:
    None
    """
    text.tag_remove("found", "1.0", END)
    search_toplevel.destroy()
    return "break"


def open_search_replace_dialog():
    """
    Opens a dialog for searching and replacing text within the script text widget.

    This function creates a new window with fields for inputting the search and replace texts
    and a button to execute the replacement.

    Parameters:
    None

    Returns:
    None
    """
    search_replace_toplevel = Toplevel(root)
    search_replace_toplevel.title("Search and Replace")
    search_replace_toplevel.transient(root)
    search_replace_toplevel.resizable(False, False)
    Label(search_replace_toplevel, text="Find:").grid(row=0, column=0, sticky="e")
    search_entry_widget = Entry(search_replace_toplevel, width=25)
    search_entry_widget.grid(row=0, column=1, padx=2, pady=2, sticky="we")
    Label(search_replace_toplevel, text="Replace:").grid(row=1, column=0, sticky="e")
    replace_entry_widget = Entry(search_replace_toplevel, width=25)
    replace_entry_widget.grid(row=1, column=1, padx=2, pady=2, sticky="we")
    Button(
        search_replace_toplevel,
        text="Replace All",
        command=lambda: search_and_replace(
            search_entry_widget.get(), replace_entry_widget.get()
        ),
    ).grid(row=2, column=1, sticky="e" + "w", padx=2, pady=5)


def open_ipynb_window():
    """
    open_ipynb_window

    Args:
        None

    Returns:
        None: Description of return value.
    """
    print("OPEN IPYTHON TERMINAL")


def create_settings_window():
    """
    create_settings_window

    Args:
        None

    Returns:
        None: Description of return value.
    """
    settings_window = Toplevel()
    settings_window.title("ScriptsEditor Settings")
    settings_window.geometry("800x600")
    default_config_file = "data/config.json"
    user_config_file = "data/user_config.json"
    if os.path.exists(user_config_file):
        config_file_to_use = user_config_file
    else:
        config_file_to_use = default_config_file
    try:
        with open(config_file_to_use, "r") as config_file:
            config_data = json.load(config_file)
    except FileNotFoundError:
        messagebox.showerror("Error", f"Config file ({config_file_to_use}) not found.")
        return
    except json.JSONDecodeError:
        messagebox.showerror(
            "Error", f"Error decoding config file ({config_file_to_use})."
        )
        return
    main_frame = Frame(settings_window)
    main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
    notebook = Notebook(main_frame)
    notebook.pack(fill=BOTH, expand=True)
    bottom_frame = Frame(settings_window)
    bottom_frame.pack(fill=X, side=BOTTOM, padx=10, pady=10)
    setting_entries = {}
    for section, options in config_data["options"].items():
        section_frame = Frame(notebook)
        notebook.add(section_frame, text=section.capitalize())
        scrollable_frame = ScrollableFrame(section_frame)
        scrollable_frame.pack(fill=BOTH, expand=True)
        for row, (option_name, default_value) in enumerate(options.items()):
            label = Label(
                scrollable_frame.scrollable_frame,
                text=option_name.replace("_", " ").capitalize(),
            )
            label.grid(row=row, column=0, padx=5, pady=5, sticky="w")
            if option_name.lower() == "font_family":
                font_families = font.families()
                default_font = (
                    default_value if default_value in font_families else "Courier New"
                )
                var = StringVar(value=default_font)
                widget = Combobox(
                    scrollable_frame.scrollable_frame,
                    textvariable=var,
                    values=font_families,
                )
            elif option_name.lower() == "theme":
                themes = load_themes_from_json("data/themes.json")
                default_theme = default_value if default_value in themes else themes[0]
                var = StringVar(value=default_theme)
                widget = Combobox(
                    scrollable_frame.scrollable_frame, textvariable=var, values=themes
                )
            elif isinstance(default_value, bool):
                var = BooleanVar(value=default_value)
                widget = Checkbutton(scrollable_frame.scrollable_frame, variable=var)
            elif isinstance(default_value, (str, int)):
                var = StringVar(value=str(default_value))
                widget = Entry(scrollable_frame.scrollable_frame, textvariable=var)
            else:
                continue
            widget.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
            scrollable_frame.scrollable_frame.grid_columnconfigure(1, weight=1)
            setting_entries[section, option_name] = var

    def save_settings():
        """
        save_settings

        Args:
            None

        Returns:
            None: Description of return value.
        """
        print("Save Settings Button Pressed")
        global style
        updated_config_data = {"options": {}}
        for (section, option_name), var in setting_entries.items():
            value = var.get()
            if isinstance(value, str) and value.isdigit():
                value = int(value)
            updated_config_data["options"].setdefault(section, {})[option_name] = value
        with open(user_config_file, "w") as user_config:
            json.dump(updated_config_data, user_config, indent=4)
        theme = (
            updated_config_data["options"]
            .get("theme_appearance", {})
            .get("theme", None)
        )
        if theme:
            try:
                style.theme_use(theme)
            except Exception as e:
                messagebox.showerror(
                    "Theme Error", f"The theme '{theme}' is not available. ({e})"
                )
        messagebox.showinfo("Settings Saved", "Settings saved successfully!")

    def reset_settings():
        """
        reset_settings

        Args:
            None

        Returns:
            None: Description of return value.
        """
        global style
        for (section, option_name), var in setting_entries.items():
            default_value = config_data["options"][section][option_name]
            if isinstance(var, BooleanVar):
                var.set(default_value)
            elif isinstance(var, StringVar):
                var.set(str(default_value))
        if os.path.exists(user_config_file):
            os.remove(user_config_file)
        default_theme = (
            config_data["options"].get("theme_appearance", {}).get("theme", "default")
        )
        print("DEFAULT THEME:\t", default_theme)
        try:
            style.theme_use(default_theme)
        except Exception as e:
            messagebox.showerror(
                "Theme Error",
                f"The default theme '{default_theme}' is not available. ({e}",
            )
        messagebox.showinfo(
            "Reset Settings",
            "Settings reset to defaults. User configuration file deleted.",
        )

    save_button = Button(bottom_frame, text="Save Settings", command=save_settings)
    save_button.pack(side=LEFT, padx=5)
    reset_button = Button(bottom_frame, text="Reset Settings", command=reset_settings)
    reset_button.pack(side=LEFT, padx=5)
    return settings_window


def open_system_info_window():
    """
    open_system_info_window

    Args:
        None

    Returns:
        None: Description of return value.
    """
    system_info_window = Toplevel()
    system_info_window.title("System Information Viewer")
    system_info_window.geometry("800x600")
    notebook = Notebook(system_info_window)
    notebook.pack(expand=True, fill="both", padx=10, pady=10)

    def run_command(command, result_queue, label):
        """
        run_command

        Args:
            command (Any): Description of command.
            result_queue (Any): Description of result_queue.
            label (Any): Description of label.

        Returns:
            None: Description of return value.
        """
        try:
            powershell_path = (
                "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
            )
            full_command = f'"{powershell_path}" -Command "{command}"'
            result = subprocess.run(
                full_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode == 0:
                output = result.stdout.strip()
            else:
                output = f"Error: {result.stderr.strip()}"
        except Exception as e:
            output = f"Error: {str(e)}"
        result_queue.put((label, output))

    def worker(commands, result_queue):
        """
        worker

        Args:
            commands (Any): Description of commands.
            result_queue (Any): Description of result_queue.

        Returns:
            None: Description of return value.
        """
        for label, cmd in commands.items():
            run_command(cmd, result_queue, label)

    def create_info_frame(parent, commands):
        """
        create_info_frame

        Args:
            parent (Any): Description of parent.
            commands (Any): Description of commands.

        Returns:
            None: Description of return value.
        """
        frame = Frame(parent)
        frame.pack(fill="both", expand=True)
        tree = Treeview(frame, columns=("Value",), show="tree")
        tree.heading("#0", text="Property")
        tree.column("#0", width=250)
        tree.heading("Value", text="Value")
        tree.column("Value", width=500)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar = Scrollbar(frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)
        result_queue = queue.Queue()
        thread = threading.Thread(target=worker, args=(commands, result_queue))
        thread.daemon = True
        thread.start()
        tree_items = {}

        def process_queue():
            """
            process_queue

            Args:
                None

            Returns:
                None: Description of return value.
            """
            while not result_queue.empty():
                label, result = result_queue.get()
                if "\n" in result:
                    if label not in tree_items:
                        parent_item = tree.insert("", "end", text=label)
                        tree_items[label] = parent_item
                    else:
                        parent_item = tree_items[label]
                        tree.delete(*tree.get_children(parent_item))
                    for line in result.splitlines():
                        tree.insert(parent_item, "end", text="", values=(line,))
                elif label in tree_items:
                    tree.item(tree_items[label], values=(result,))
                else:
                    item_id = tree.insert("", "end", text=label, values=(result,))
                    tree_items[label] = item_id
            frame.after(100, process_queue)

        process_queue()
        return frame

    system_commands = {
        "Hostname": "$env:COMPUTERNAME",
        "Operating System": "(Get-CimInstance Win32_OperatingSystem).Caption",
        "OS Version": "(Get-CimInstance Win32_OperatingSystem).Version",
        "Build Number": "(Get-CimInstance Win32_OperatingSystem).BuildNumber",
        "System Architecture": "(Get-CimInstance Win32_OperatingSystem).OSArchitecture",
        "Manufacturer": "(Get-CimInstance Win32_ComputerSystem).Manufacturer",
        "Model": "(Get-CimInstance Win32_ComputerSystem).Model",
        "Serial Number": "(Get-CimInstance Win32_BIOS).SerialNumber",
        "BIOS Version": "(Get-CimInstance Win32_BIOS).SMBIOSBIOSVersion",
        "System Uptime": "(New-TimeSpan -Start (Get-CimInstance Win32_OperatingSystem).LastBootUpTime).ToString()",
        "Current System Time": "Get-Date",
        "Timezone": "(Get-TimeZone).DisplayName",
    }
    hardware_commands = {
        "CPU Model": "(Get-CimInstance Win32_Processor).Name",
        "CPU Manufacturer": "(Get-CimInstance Win32_Processor).Manufacturer",
        "CPU Clock Speed (MHz)": "(Get-CimInstance Win32_Processor).MaxClockSpeed",
        "CPU Cores": "(Get-CimInstance Win32_Processor).NumberOfCores",
        "CPU Logical Processors": "(Get-CimInstance Win32_Processor).NumberOfLogicalProcessors",
        "L2 Cache Size (KB)": "(Get-CimInstance Win32_Processor).L2CacheSize",
        "L3 Cache Size (KB)": "(Get-CimInstance Win32_Processor).L3CacheSize",
        "Total Installed Memory (GB)": "('{0:N2}' -f ((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB))",
        "Available Memory (GB)": "('{0:N2}' -f ((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB / 1024))",
        "Memory Type and Speed": "Get-CimInstance Win32_PhysicalMemory | Select-Object MemoryType, Speed | Format-Table -AutoSize",
        "Memory Slots Used": "(Get-CimInstance Win32_PhysicalMemory).Count",
        "Total Memory Slots": "(Get-CimInstance Win32_PhysicalMemoryArray).MemoryDevices",
        "Disk Drives": "Get-CimInstance Win32_DiskDrive | Select-Object Model, MediaType, Size | Format-Table -AutoSize",
        "Logical Drives": "Get-CimInstance Win32_LogicalDisk | Select-Object DeviceID, FileSystem, Size, FreeSpace | Format-Table -AutoSize",
        "GPU Model": "(Get-CimInstance Win32_VideoController).Name",
        "GPU Adapter RAM": "(Get-CimInstance Win32_VideoController).AdapterRAM",
        "GPU Driver Version": "(Get-CimInstance Win32_VideoController).DriverVersion",
        "Motherboard Manufacturer": "(Get-CimInstance Win32_BaseBoard).Manufacturer",
        "Motherboard Model": "(Get-CimInstance Win32_BaseBoard).Product",
        "Network Adapters": "Get-NetAdapter | Select-Object Name, InterfaceDescription, MacAddress, Status | Format-Table -AutoSize",
        "Audio Devices": "Get-CimInstance Win32_SoundDevice | Select-Object Name, Manufacturer | Format-Table -AutoSize",
        "Input Devices": "Get-PnpDevice -Class Keyboard, Mouse | Where-Object { $_.Status -eq 'OK' } | Select-Object FriendlyName | Format-Table -AutoSize",
        '"Connected Monitors": "Get-CimInstance -Namespace root\\wmi -Class WmiMonitorID | "\n                              "ForEach-Object { $name = ($_.UserFriendlyName -notmatch 0 | "\n                              "ForEach-Object { [char]$_ }) -join \'\'; $name }","Display Resolutions": "Add-Type -AssemblyName System.Windows.Forms; "\n                               "[System.Windows.Forms.Screen]::AllScreens | ForEach-Object "\n                               "{ "$($_.DeviceName): $($_.Bounds.Width)x$($_.Bounds.Height)" }",Battery Status': "Get-CimInstance Win32_Battery | Select-Object Name, EstimatedChargeRemaining, BatteryStatus | Format-Table -AutoSize",
    }
    network_commands = {
        "Public IP Address": "(Invoke-WebRequest -Uri 'http://ifconfig.me/ip').Content.Trim()",
        "Private IP Addresses": "Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -ne 'Loopback Pseudo-Interface 1' } | Select-Object IPAddress | Format-Table -AutoSize",
        "Subnet Masks": "Get-NetIPConfiguration | Select-Object InterfaceAlias, IPv4SubnetMask | Format-Table -AutoSize",
        "Default Gateway": "Get-NetIPConfiguration | Select-Object InterfaceAlias, IPv4DefaultGateway | Format-Table -AutoSize",
        "DNS Servers": "Get-DnsClientServerAddress -AddressFamily IPv4 | Select-Object InterfaceAlias, ServerAddresses | Format-Table -AutoSize",
        "DHCP Information": "Get-NetIPConfiguration | Select-Object InterfaceAlias, DhcpServer, DhcpLeaseObtainedTime, DhcpLeaseExpires | Format-Table -AutoSize",
        "Active Network Connections": "Get-NetTCPConnection | Where-Object { $_.State -eq 'Established' } | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort | Format-Table -AutoSize",
        "VPN Connections": "Get-VpnConnection | Select-Object Name, ConnectionStatus | Format-Table -AutoSize",
        "Proxy Settings": "Get-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings' | Select-Object ProxyServer, ProxyEnable | Format-Table -AutoSize",
        "Firewall Status": "Get-NetFirewallProfile | Select-Object Name, Enabled | Format-Table -AutoSize",
    }
    software_commands = {
        "Installed Applications": "Get-ItemProperty @('HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*','HKLM:\\Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*') | Where-Object { $_.DisplayName } | Select-Object DisplayName, DisplayVersion, InstallDate | Sort-Object DisplayName | Format-Table -AutoSize",
        "Running Processes": "Get-Process | Select-Object ProcessName, Id, CPU, WorkingSet | Format-Table -AutoSize",
        "Startup Programs": "Get-CimInstance Win32_StartupCommand | Select-Object Name, Command, Location | Format-Table -AutoSize",
    }
    security_commands = {
        "User Accounts": "Get-LocalUser | Select-Object Name, Enabled | Format-Table -AutoSize",
        '"Group Memberships": "Get-LocalGroupMember -Group \'Administrators\' | Select-Object Name, "\n                             "ObjectClass | Format-Table -AutoSize",Antivirus Software': "Get-CimInstance -Namespace 'root\\SecurityCenter2' -ClassName AntiVirusProduct | Select-Object displayName, productState | Format-Table -AutoSize",
        "Firewall Configuration": "Get-NetFirewallProfile | Select-Object Name, Enabled | Format-Table -AutoSize",
        "Disk Encryption Status": "Get-BitLockerVolume | Select-Object MountPoint, VolumeStatus | Format-Table -AutoSize",
    }
    'performance_commands = {\n        "CPU Usage (%)": "(Get-Counter \'\\Processor(_Total)\\% Processor Time\').CounterSamples."\n                         "CookedValue",\n        "Available Memory (MB)": "(Get-Counter \'\\Memory\\Available MBytes\').CounterSamples."\n                                 "CookedValue",\n        "Disk Read/Write Speeds": "Get-Counter -Counter \'\\PhysicalDisk(_Total)\\Disk Read "\n                                  "Bytes/sec\',\'\\PhysicalDisk(_Total)\\Disk Write Bytes/sec\' | "\n                                  "Format-Table -AutoSize",\n    }'
    development_commands = {
        "Version Control Systems": "Get-Command git, svn -ErrorAction SilentlyContinue | Select-Object Name, Version | Format-Table -AutoSize",
        "Programming Languages": "Get-Command python, java -ErrorAction SilentlyContinue | Select-Object Name, Version | Format-Table -AutoSize",
        "Environment Variables": "[Environment]::GetEnvironmentVariables() | Format-Table -AutoSize",
    }
    miscellaneous_commands = {
        "Locale and Language Settings": "Get-Culture | Select-Object Name, DisplayName",
        "Installed Fonts": "Get-ChildItem -Path $env:windir\\Fonts -Include *.ttf,*.otf -Recurse | Select-Object Name | Format-Table -AutoSize",
        "Recent Application Events": "Get-EventLog -LogName Application -Newest 10 | Format-Table -AutoSize",
    }
    user_commands = {
        "Home Directory Contents": "Get-ChildItem -Path $env:USERPROFILE | Select-Object Name | Format-Table -AutoSize",
        "Installed Browsers": "Get-ItemProperty 'HKLM:\\Software\\Clients\\StartMenuInternet\\*' | Select-Object '(default)' | Format-Table -AutoSize",
    }
    system_tab = create_info_frame(notebook, system_commands)
    hardware_tab = create_info_frame(notebook, hardware_commands)
    network_tab = create_info_frame(notebook, network_commands)
    software_tab = create_info_frame(notebook, software_commands)
    security_tab = create_info_frame(notebook, security_commands)
    development_tab = create_info_frame(notebook, development_commands)
    miscellaneous_tab = create_info_frame(notebook, miscellaneous_commands)
    user_tab = create_info_frame(notebook, user_commands)
    notebook.add(system_tab, text="System")
    notebook.add(hardware_tab, text="Hardware")
    notebook.add(network_tab, text="Network")
    notebook.add(software_tab, text="Software")
    notebook.add(security_tab, text="Security")
    notebook.add(development_tab, text="Development")
    notebook.add(miscellaneous_tab, text="Miscellaneous")
    notebook.add(user_tab, text="User")

    def refresh_all():
        """
        refresh_all

        Args:
            None

        Returns:
            None: Description of return value.
        """
        tabs_and_commands = [
            (system_tab, system_commands),
            (hardware_tab, hardware_commands),
            (network_tab, network_commands),
            (software_tab, software_commands),
            (security_tab, security_commands),
            (development_tab, development_commands),
            (miscellaneous_tab, miscellaneous_commands),
            (user_tab, user_commands),
        ]
        for tab, commands in tabs_and_commands:
            tree = tab.winfo_children()[0]
            tree.delete(*tree.get_children())
            result_queue = queue.Queue()
            thread = threading.Thread(target=worker, args=(commands, result_queue))
            thread.daemon = True
            thread.start()
            tree_items = {}

            def process_queue():
                """
                process_queue

                Args:
                    None

                Returns:
                    None: Description of return value.
                """
                while not result_queue.empty():
                    label, result = result_queue.get()
                    if "\n" in result:
                        if label not in tree_items:
                            parent_item = tree.insert("", "end", text=label)
                            tree_items[label] = parent_item
                        else:
                            parent_item = tree_items[label]
                            tree.delete(*tree.get_children(parent_item))
                        for line in result.splitlines():
                            tree.insert(parent_item, "end", text="", values=(line,))
                    elif label in tree_items:
                        tree.item(tree_items[label], values=(result,))
                    else:
                        item_id = tree.insert("", "end", text=label, values=(result,))
                        tree_items[label] = item_id
                tree.after(100, process_queue)

            process_queue()

    refresh_button = Button(system_info_window, text="Refresh All", command=refresh_all)
    refresh_button.pack(pady=10)


def open_winget_window():
    """
    open_winget_window

    Args:
        None

    Returns:
        None: Description of return value.
    """

    def run_command(command):
        """
        run_command

        Args:
            command (Any): Description of command.

        Returns:
            None: Description of return value.
        """
        try:
            command += " --disable-interactivity"
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                shell=True,
            )
            output = result.stdout
            spinner_chars = {"\\", "-", "|", "/", "█", "▒"}
            filtered_output = "\n".join(
                (
                    line
                    for line in output.splitlines()
                    if not set(line.strip()).issubset(spinner_chars)
                    and line.strip() != ""
                )
            )
            return filtered_output
        except Exception as e:
            return f"Error: {str(e)}"

    def list_programs():
        """
        list_programs

        Args:
            None

        Returns:
            None: Description of return value.
        """
        output = run_command("winget search --exact")
        insert_output(output)

    def list_installed():
        """
        list_installed

        Args:
            None

        Returns:
            None: Description of return value.
        """
        output = run_command('winget list --source "winget"')
        installed_listbox.delete(0, END)
        lines = output.splitlines()
        for line in lines[1:]:
            program_info = " ".join(line.split()).strip()
            if program_info:
                installed_listbox.insert(END, program_info)

    def list_upgradable():
        """
        list_upgradable

        Args:
            None

        Returns:
            None: Description of return value.
        """
        output = run_command("winget upgrade --include-unknown")
        removed_text = "winget"
        for widget in upgrade_checkboxes_frame.winfo_children():
            widget.destroy()
        upgrade_vars.clear()
        version_pattern = re.compile("(\\d+[\\.-]\\d+[\\.-]?\\d*)")
        lines = output.splitlines()[1:]
        for i, line in enumerate(lines):
            from_version = "Unknown"
            to_version = "Unknown"
            if line.strip():
                match = version_pattern.search(line)
                if match:
                    try:
                        program_info = (
                            line[match.start() :].strip().replace(removed_text, "")
                        )
                        to_version = program_info[::-1].split()[0][::-1]
                        from_version = program_info[::-1].split()[1][::-1]
                        new_to_version = "Unknown"
                        new_from_version = "Unknown"
                        if "(" in program_info and ")" in program_info:
                            new_line = line.replace(removed_text, "")
                            new_to_version = new_line[::-1].split()[0]
                            if "(" in new_to_version and ")" in new_to_version:
                                new_new_line = new_line.split()[::-1]
                                new_to_version = new_new_line[1] + " " + new_new_line[0]
                                new_line = new_line.replace(new_to_version, "").strip()
                                to_version = new_to_version
                            if (
                                "(" in new_to_version
                                and ")" in new_to_version
                                and (new_to_version != "Unknown")
                            ):
                                new_new_line = new_line.split()[::-1]
                                new_from_version = (
                                    new_new_line[1] + " " + new_new_line[0]
                                )
                                from_version = new_from_version
                        line = (
                            line.replace(to_version, "")
                            .replace(from_version, "")
                            .replace(removed_text, "")
                        )
                    except Exception as e:
                        pass
                program_id = line[::-1].split()[0][::-1]
                if program_id == "winget":
                    try:
                        removed_text = "winget"
                        new_line = line.replace(removed_text, "")
                        to_version = new_line[::-1].split()[0][::-1]
                        from_version = new_line[::-1].split()[1][::-1]
                        new_line = (
                            line.replace(from_version, "")
                            .replace(to_version, "")
                            .replace(removed_text, "")
                        )
                        program_id = new_line[::-1].split()[0][::-1]
                    except Exception as e:
                        pass
                if (
                    from_version != "Unknown"
                    and to_version != "Unknown"
                    and (program_id != "()")
                ):
                    display_text = (
                        f"{program_id:<40} {from_version:<15} {to_version:<15}"
                    )
                    var = BooleanVar()
                    checkbox = Checkbutton(
                        upgrade_checkboxes_frame,
                        text=display_text,
                        variable=var,
                        anchor="w",
                        justify=LEFT,
                        font=("Courier", 10),
                    )
                    checkbox.grid(row=i, column=0, sticky="w")
                    upgrade_vars.append((var, program_id))
        upgrade_checkboxes_frame.update_idletasks()
        upgrade_checkboxes_canvas.configure(
            scrollregion=upgrade_checkboxes_canvas.bbox("all")
        )

    def update_output(output):
        """
        update_output

        Args:
            output (Any): Description of output.

        Returns:
            None: Description of return value.
        """
        output_text.insert(END, output + "\n")
        output_text.see(END)

    def upgrade_selected():
        """
        upgrade_selected

        Args:
            None

        Returns:
            None: Description of return value.
        """
        disable_upgrade_buttons()

        def upgrade_thread():
            """
            upgrade_thread

            Args:
                None

            Returns:
                None: Description of return value.
            """
            selected_programs = [info for var, info in upgrade_vars if var.get()]
            if not selected_programs:
                messagebox.showinfo(
                    "No Selection", "Please select programs to upgrade."
                )
                enable_upgrade_buttons()
                return
            successfully_upgraded = []
            for program_info in selected_programs:
                program_id = program_info.split()[0]
                update_output(f"\nUpgrading {program_id}...")
                output = run_command(
                    f'winget upgrade --include-unknown --id "{program_id}"'
                )
                update_output(output)
                successfully_upgraded.append(program_id)
            list_upgradable()
            summary = (
                f"Programs {', '.join(successfully_upgraded)} successfully upgraded."
            )
            update_output(summary)
            enable_upgrade_buttons()

        threading.Thread(target=upgrade_thread).start()

    def disable_upgrade_buttons():
        """
        disable_upgrade_buttons

        Args:
            None

        Returns:
            None: Description of return value.
        """
        select_all_button.config(state=DISABLED)
        deselect_all_button.config(state=DISABLED)
        upgrade_selected_button.config(state=DISABLED)
        for widget in upgrade_checkboxes_frame.winfo_children():
            if isinstance(widget, Checkbutton):
                widget.config(state=DISABLED)

    def enable_upgrade_buttons():
        """
        enable_upgrade_buttons

        Args:
            None

        Returns:
            None: Description of return value.
        """
        select_all_button.config(state=NORMAL)
        deselect_all_button.config(state=NORMAL)
        upgrade_selected_button.config(state=NORMAL)
        for widget in upgrade_checkboxes_frame.winfo_children():
            if isinstance(widget, Checkbutton):
                widget.config(state=NORMAL)

    def select_all():
        """
        select_all

        Args:
            None

        Returns:
            None: Description of return value.
        """
        for var, _ in upgrade_vars:
            var.set(True)

    def deselect_all():
        """
        deselect_all

        Args:
            None

        Returns:
            None: Description of return value.
        """
        for var, _ in upgrade_vars:
            var.set(False)

    def search_program():
        """
        search_program

        Args:
            None

        Returns:
            None: Description of return value.
        """
        search_term = simpledialog.askstring("Search", "Enter program name to search:")
        if search_term:
            output = run_command(f'winget search --exact "{search_term}"')
            insert_output(output)

    def install_program():
        """
        install_program

        Args:
            None

        Returns:
            None: Description of return value.
        """
        program_id = simpledialog.askstring("Install", "Enter program ID to install:")
        if program_id:
            output = run_command(f'winget install -s "winget" "{program_id}"')
            insert_output(f"Installing {program_id}...\n{output}")
            list_installed()
            list_upgradable()

    def uninstall_program():
        """
        uninstall_program

        Args:
            None

        Returns:
            None: Description of return value.
        """
        program_id = simpledialog.askstring(
            "Uninstall", "Enter program ID to uninstall:"
        )
        if program_id:
            output = run_command(f'winget uninstall "{program_id}"')
            insert_output(f"Uninstalling {program_id}...\n{output}")
            list_installed()
            list_upgradable()

    def get_program_description(program_id):
        """
        get_program_description

        Args:
            program_id (Any): Description of program_id.

        Returns:
            None: Description of return value.
        """
        return run_command(f'winget show "{program_id}"')

    def program_description():
        """
        program_description

        Args:
            None

        Returns:
            None: Description of return value.
        """
        program_id = simpledialog.askstring(
            "Description of Program", "Enter program ID to get its description:"
        )
        if program_id:
            output = get_program_description(program_id)
            insert_output(output)
            list_installed()

    def insert_output(output):
        """
        insert_output

        Args:
            output (Any): Description of output.

        Returns:
            None: Description of return value.
        """
        output_text.delete(1.0, END)
        output_text.insert(END, output)

    winget_window = Toplevel()
    winget_window.title("WinGet Package Manager")
    winget_window.geometry("1000x700")
    main_frame = Frame(winget_window)
    main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
    left_frame = Frame(main_frame)
    left_frame.pack(side=LEFT, fill=BOTH, expand=True)
    installed_label = Label(left_frame, text="Installed Programs")
    installed_label.pack()
    installed_listbox = Listbox(left_frame, height=20, width=50)
    installed_listbox.pack(side=LEFT, fill=BOTH, expand=True)
    installed_scrollbar = Scrollbar(left_frame)
    installed_scrollbar.pack(side=RIGHT, fill=Y)
    installed_listbox.config(yscrollcommand=installed_scrollbar.set)
    installed_scrollbar.config(command=installed_listbox.yview)
    right_frame = Frame(main_frame)
    right_frame.pack(side=RIGHT, fill=BOTH, expand=True)
    upgradable_label = Label(right_frame, text="Upgradable Programs")
    upgradable_label.pack()
    upgrade_checkboxes_canvas = Canvas(right_frame)
    upgrade_checkboxes_canvas.pack(side=LEFT, fill=BOTH, expand=True)
    upgrade_checkboxes_scrollbar = Scrollbar(
        right_frame, orient=VERTICAL, command=upgrade_checkboxes_canvas.yview
    )
    upgrade_checkboxes_scrollbar.pack(side=RIGHT, fill=Y)
    upgrade_checkboxes_canvas.configure(yscrollcommand=upgrade_checkboxes_scrollbar.set)
    upgrade_checkboxes_frame = Frame(upgrade_checkboxes_canvas)
    upgrade_checkboxes_canvas.create_window(
        (0, 0), window=upgrade_checkboxes_frame, anchor="nw"
    )

    def on_mousewheel(event):
        """
        on_mousewheel

        Args:
            event (Any): Description of event.

        Returns:
            None: Description of return value.
        """
        upgrade_checkboxes_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def bind_mousewheel(event):
        """
        bind_mousewheel

        Args:
            event (Any): Description of event.

        Returns:
            None: Description of return value.
        """
        upgrade_checkboxes_canvas.bind_all("<MouseWheel>", on_mousewheel)

    def unbind_mousewheel(event):
        """
        unbind_mousewheel

        Args:
            event (Any): Description of event.

        Returns:
            None: Description of return value.
        """
        upgrade_checkboxes_canvas.unbind_all("<MouseWheel>")

    upgrade_checkboxes_canvas.bind("<Enter>", bind_mousewheel)
    upgrade_checkboxes_canvas.bind("<Leave>", unbind_mousewheel)
    upgrade_vars = []
    output_text = scrolledtext.ScrolledText(
        winget_window, wrap=WORD, height=10, width=120
    )
    output_text.pack(fill=BOTH, expand=True, padx=10, pady=10)
    button_frame = Frame(winget_window)
    button_frame.pack(fill=X, padx=10, pady=10)
    list_all_programs_button = Button(
        button_frame, text="List All Programs", command=list_programs
    )
    list_all_programs_button.pack(side=LEFT, padx=5)
    search_button = Button(button_frame, text="Search Program", command=search_program)
    search_button.pack(side=LEFT, padx=5)
    program_description_button = Button(
        button_frame, text="Program Description", command=program_description
    )
    program_description_button.pack(side=LEFT, padx=5)
    install_button = Button(
        button_frame, text="Install Program", command=install_program
    )
    install_button.pack(side=LEFT, padx=5)
    uninstall_button = Button(
        button_frame, text="Uninstall Program", command=uninstall_program
    )
    uninstall_button.pack(side=LEFT, padx=5)
    select_all_button = Button(button_frame, text="Select All", command=select_all)
    select_all_button.pack(side=LEFT, padx=5)
    deselect_all_button = Button(
        button_frame, text="Deselect All", command=deselect_all
    )
    deselect_all_button.pack(side=LEFT, padx=5)
    upgrade_selected_button = Button(
        button_frame, text="Upgrade Selected", command=upgrade_selected
    )
    upgrade_selected_button.pack(side=LEFT, padx=5)
    list_installed()
    list_upgradable()
    insert_output(
        "Welcome to WinGet Package Manager.\nUse the buttons to perform WinGet operations."
    )


def open_git_window(repo_dir=None):
    """
    open_git_window

    Args:
        repo_dir (Any): Description of repo_dir.

    Returns:
        None: Description of return value.
    """
    global git_console_instance
    command_history = []

    def execute_command(command):
        """
        execute_command

        Args:
            command (Any): Description of command.

        Returns:
            None: Description of return value.
        """
        if command.strip():
            command_history.append(command)
            history_pointer[0] = len(command_history)
            directory = repo_dir or os.getcwd()
            git_command = f'git -C "{directory}" {command}'
            try:
                if command == "status --porcelain -u":
                    update_output_text(output_text)
                else:
                    output = subprocess.check_output(
                        git_command, stderr=subprocess.STDOUT, shell=True, text=True
                    )
                    insert_ansi_text(output_text, f"{git_command}\n{output}\n")
            except subprocess.CalledProcessError as e:
                insert_ansi_text(output_text, f"Error: {e.output}\n", "error")
            entry.delete(0, END)
            output_text.see(END)

    def populate_branch_menu():
        """
        populate_branch_menu

        Args:
            None

        Returns:
            None: Description of return value.
        """
        branch_menu.delete(0, END)
        try:
            branches_output = subprocess.check_output(
                ["git", "branch", "--all"], text=True
            )
            branches = list(
                filter(None, [branch.strip() for branch in branches_output.split("\n")])
            )
            active_branch = next(
                (branch[2:] for branch in branches if branch.startswith("*")), None
            )
            for branch in branches:
                is_active = branch.startswith("*")
                branch_name = branch[2:] if is_active else branch
                display_name = f"✓ {branch_name}" if is_active else branch_name
                branch_menu.add_command(
                    label=display_name, command=lambda b=branch_name: checkout_branch(b)
                )
        except subprocess.CalledProcessError as e:
            insert_ansi_text(
                output_text, f"Error fetching branches: {e.output}\n", "error"
            )

    def update_commit_list(commit_list):
        """
        update_commit_list

        Args:
            commit_list (Any): Description of commit_list.

        Returns:
            None: Description of return value.
        """
        command = 'git log --no-merges --color --graph --pretty=format:"%h %d %s - <%an (%cr)>" --abbrev-commit --branches'
        output = subprocess.check_output(command, shell=True, text=True)
        commit_list.delete(0, END)
        apply_visual_styles(commit_list)
        current_commit = get_current_checkout_commit()
        short_hash_number_commit = current_commit[:7]
        for line in output.split("\n"):
            line = line[2:]
            if short_hash_number_commit in line:
                commit_list.insert(END, f"* {line}")
            else:
                commit_list.insert(END, line)
        apply_visual_styles(commit_list)

    def apply_visual_styles(commit_list):
        """
        apply_visual_styles

        Args:
            commit_list (Any): Description of commit_list.

        Returns:
            None: Description of return value.
        """
        current_commit = get_current_checkout_commit()
        for i in range(commit_list.size()):
            item = commit_list.get(i)
            if current_commit in item:
                commit_list.itemconfig(i, {"bg": "yellow"})
            elif item.startswith("*"):
                commit_list.itemconfig(i, {"fg": "green"})
            else:
                commit_list.itemconfig(i, {"fg": "gray"})

    def commit_list_context_menu(event):
        """
        commit_list_context_menu

        Args:
            event (Any): Description of event.

        Returns:
            None: Description of return value.
        """
        context_menu = Menu(commit_list, tearoff=0)
        context_menu.add_command(
            label="Checkout",
            command=lambda: checkout_commit(
                commit_list.get(commit_list.curselection())
            ),
        )
        context_menu.add_command(
            label="View Details",
            command=lambda: view_commit_details(
                commit_list.get(commit_list.curselection())
            ),
        )
        context_menu.post(event.x_root, event.y_root)

    def checkout_commit(commit_info):
        """
        checkout_commit

        Args:
            commit_info (Any): Description of commit_info.

        Returns:
            None: Description of return value.
        """
        commit_hash = commit_info.split(" ")[0]
        try:
            execute_command(f"checkout {commit_hash}")
            update_status(commit_hash)
            update_commit_list(commit_list)
        except subprocess.CalledProcessError as e:
            insert_ansi_text(
                output_text, f"Error checking out commit: {e.output}\n", "error"
            )
        apply_visual_styles(commit_list)

    def view_commit_details(commit_hash):
        """
        view_commit_details

        Args:
            commit_hash (Any): Description of commit_hash.

        Returns:
            None: Description of return value.
        """
        try:
            commit_hash_number = commit_hash[:7]
            output = subprocess.check_output(
                ["git", "show", "--color=always", commit_hash_number], text=True
            )
            details_window = Toplevel()
            details_window.title(f"{commit_hash}")
            text_widget = scrolledtext.ScrolledText(details_window)
            define_ansi_tags(text_widget)
            apply_ansi_styles(text_widget, output)
            text_widget.config(state=DISABLED)
            text_widget.pack(fill="both", expand=True)
        except subprocess.CalledProcessError as e:
            error_window = Toplevel()
            error_window.title("Error")
            Label(
                error_window, text=f"Failed to fetch commit details: {e.output}"
            ).pack(pady=20, padx=20)

    def get_current_checkout_commit():
        """
        get_current_checkout_commit

        Args:
            None

        Returns:
            None: Description of return value.
        """
        current_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
        update_status()
        return current_commit

    def checkout_branch(branch):
        """
        checkout_branch

        Args:
            branch (Any): Description of branch.

        Returns:
            None: Description of return value.
        """
        execute_command(f"checkout {branch}")
        populate_branch_menu()
        update_commit_list(commit_list)
        update_status()

    def define_ansi_tags(text_widget):
        """
        define_ansi_tags

        Args:
            text_widget (Any): Description of text_widget.

        Returns:
            None: Description of return value.
        """
        text_widget.tag_configure("added", background="light green", foreground="black")
        text_widget.tag_configure(
            "removed", background="light coral", foreground="black"
        )
        text_widget.tag_configure("changed", foreground="cyan")
        text_widget.tag_configure("commit", foreground="yellow")
        text_widget.tag_configure("author", foreground="green")
        text_widget.tag_configure("date", foreground="magenta")
        text_widget.tag_configure("error", foreground="red")
        text_widget.tag_configure("green", foreground="green")
        text_widget.tag_configure("yellow", foreground="yellow")
        text_widget.tag_configure("blue", foreground="blue")
        text_widget.tag_configure("magenta", foreground="magenta")
        text_widget.tag_configure("cyan", foreground="cyan")
        text_widget.tag_configure("modified", foreground="orange")
        text_widget.tag_configure("modified_multiple", foreground="dark orange")
        text_widget.tag_configure("untracked", foreground="red")
        text_widget.tag_configure("added", foreground="green")
        text_widget.tag_configure("deleted", foreground="red")
        text_widget.tag_configure("renamed", foreground="blue")
        text_widget.tag_configure("copied", foreground="purple")
        text_widget.tag_configure("unmerged", foreground="yellow")
        text_widget.tag_configure("ignored", foreground="gray")
        text_widget.tag_configure("addition", foreground="green")
        text_widget.tag_configure("deletion", foreground="red")
        text_widget.tag_configure("info", foreground="blue")

    def apply_ansi_styles(text_widget, text):
        """
        apply_ansi_styles

        Args:
            text_widget (Any): Description of text_widget.
            text (Any): Description of text.

        Returns:
            None: Description of return value.
        """
        ansi_escape = re.compile("\\x1B\\[([0-9;]*[mK])")
        pos = 0
        lines = text.splitlines()
        for line in lines:
            cleaned_line = ansi_escape.sub("", line)
            if cleaned_line.startswith("commit "):
                text_widget.insert("end", "commit ", "commit")
                text_widget.insert("end", cleaned_line[7:] + "\n")
            elif cleaned_line.startswith("Author: "):
                text_widget.insert("end", "Author: ", "author")
                text_widget.insert("end", cleaned_line[8:] + "\n")
            elif cleaned_line.startswith("Date: "):
                text_widget.insert("end", "Date: ", "date")
                text_widget.insert("end", cleaned_line[6:] + "\n")
            elif cleaned_line.startswith("+ ") or (
                cleaned_line.startswith("+") and (not cleaned_line.startswith("+++"))
            ):
                text_widget.insert("end", cleaned_line + "\n", "added")
            elif cleaned_line.startswith("- ") or (
                cleaned_line.startswith("-") and (not cleaned_line.startswith("---"))
            ):
                text_widget.insert("end", cleaned_line + "\n", "removed")
            elif cleaned_line.startswith("@@ "):
                parts = cleaned_line.split("@@")
                if len(parts) >= 3:
                    text_widget.insert("end", parts[0])
                    text_widget.insert("end", "@@" + parts[1] + "@@", "changed")
                    text_widget.insert("end", "".join(parts[2:]) + "\n")
                else:
                    text_widget.insert("end", cleaned_line + "\n")
            else:
                text_widget.insert("end", cleaned_line + "\n")

    def insert_ansi_text(widget, text, tag=""):
        """
        insert_ansi_text

        Args:
            widget (Any): Description of widget.
            text (Any): Description of text.
            tag (Any): Description of tag.

        Returns:
            None: Description of return value.
        """
        ansi_escape = re.compile("\\x1B\\[(?P<code>\\d+(;\\d+)*)m")
        segments = ansi_escape.split(text)
        tag = None
        for i, segment in enumerate(segments):
            if i % 2 == 0:
                widget.insert(END, segment, tag)
            else:
                codes = list(map(int, segment.split(";")))
                tag = get_ansi_tag(codes)
                if tag:
                    widget.tag_configure(tag, **get_ansi_style(tag))

    def get_ansi_tag(codes):
        """
        get_ansi_tag

        Args:
            codes (Any): Description of codes.

        Returns:
            None: Description of return value.
        """
        fg_map = {
            30: "black",
            31: "red",
            32: "green",
            33: "yellow",
            34: "blue",
            35: "magenta",
            36: "cyan",
            37: "white",
            90: "bright_black",
            91: "bright_red",
            92: "bright_green",
            93: "bright_yellow",
            94: "bright_blue",
            95: "bright_magenta",
            96: "bright_cyan",
            97: "bright_white",
        }
        bg_map = {
            40: "bg_black",
            41: "bg_red",
            42: "bg_green",
            43: "bg_yellow",
            44: "bg_blue",
            45: "bg_magenta",
            46: "bg_cyan",
            47: "bg_white",
            100: "bg_bright_black",
            101: "bg_bright_red",
            102: "bg_bright_green",
            103: "bg_bright_yellow",
            104: "bg_bright_blue",
            105: "bg_bright_magenta",
            106: "bg_bright_cyan",
            107: "bg_bright_white",
        }
        styles = []
        for code in codes:
            if code in fg_map:
                styles.append(fg_map[code])
            elif code in bg_map:
                styles.append(bg_map[code])
            elif code == 1:
                styles.append("bold")
            elif code == 4:
                styles.append("underline")
        return "_".join(styles) if styles else None

    def get_ansi_style(tag):
        """
        get_ansi_style

        Args:
            tag (Any): Description of tag.

        Returns:
            None: Description of return value.
        """
        styles = {
            "black": {"foreground": "black"},
            "red": {"foreground": "red"},
            "green": {"foreground": "green"},
            "yellow": {"foreground": "yellow"},
            "blue": {"foreground": "blue"},
            "magenta": {"foreground": "magenta"},
            "cyan": {"foreground": "cyan"},
            "white": {"foreground": "white"},
            "bright_black": {"foreground": "gray"},
            "bright_red": {"foreground": "lightcoral"},
            "bright_green": {"foreground": "lightgreen"},
            "bright_yellow": {"foreground": "lightyellow"},
            "bright_blue": {"foreground": "lightblue"},
            "bright_magenta": {"foreground": "violet"},
            "bright_cyan": {"foreground": "lightcyan"},
            "bright_white": {"foreground": "white"},
            "bg_black": {"background": "black"},
            "bg_red": {"background": "red"},
            "bg_green": {"background": "green"},
            "bg_yellow": {"background": "yellow"},
            "bg_blue": {"background": "blue"},
            "bg_magenta": {"background": "magenta"},
            "bg_cyan": {"background": "cyan"},
            "bg_white": {"background": "white"},
            "bg_bright_black": {"background": "gray"},
            "bg_bright_red": {"background": "lightcoral"},
            "bg_bright_green": {"background": "lightgreen"},
            "bg_bright_yellow": {"background": "lightyellow"},
            "bg_bright_blue": {"background": "lightblue"},
            "bg_bright_magenta": {"background": "violet"},
            "bg_bright_cyan": {"background": "lightcyan"},
            "bg_bright_white": {"background": "white"},
            "bold": {"font": ("TkDefaultFont", 10, "bold")},
            "underline": {"font": ("TkDefaultFont", 10, "underline")},
        }
        style = {}
        for part in tag.split("_"):
            if part in styles:
                style.update(styles[part])
        return style

    terminal_window = Toplevel()
    terminal_window.title("Git Console")
    terminal_window.geometry("600x512")
    menubar = Menu(terminal_window)
    terminal_window.config(menu=menubar)
    git_menu = Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Git", menu=git_menu)
    for command, icon in git_icons.items():
        git_menu.add_command(
            label=f"{icon} {command.capitalize()}",
            command=lambda c=command: execute_command(c),
        )
    branch_menu = Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Branch", menu=branch_menu)
    populate_branch_menu()
    output_text = scrolledtext.ScrolledText(terminal_window, height=20, width=80)
    output_text.pack(fill="both", expand=True)
    status_bar = Label(
        terminal_window, text="Checking branch...", bd=1, relief=SUNKEN, anchor=W
    )
    status_bar.pack(side="top", fill="x")

    def update_status(commit_hash="HEAD"):
        """
        update_status

        Args:
            commit_hash (Any): Description of commit_hash.

        Returns:
            None: Description of return value.
        """
        try:
            branch_name = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", commit_hash], text=True
            ).strip()
            if branch_name != "HEAD":
                status_bar.config(text=f"Current branch: {branch_name}")
            else:
                commit_short_hash = subprocess.check_output(
                    ["git", "rev-parse", "--short", commit_hash], text=True
                ).strip()
                status_bar.config(text=f"Current commit: {commit_short_hash}")
        except subprocess.CalledProcessError:
            status_bar.config(text="Error: Invalid identifier")

    update_status()
    command_history = []
    history_pointer = [0]

    def navigate_history(event):
        """
        navigate_history

        Args:
            event (Any): Description of event.

        Returns:
            None: Description of return value.
        """
        if command_history:
            if event.keysym == "Up":
                history_pointer[0] = max(0, history_pointer[0] - 1)
            elif event.keysym == "Down":
                history_pointer[0] = min(len(command_history), history_pointer[0] + 1)
            command = (
                command_history[history_pointer[0]]
                if history_pointer[0] < len(command_history)
                else ""
            )
            entry.delete(0, END)
            entry.insert(0, command)

    def add_selected_text_to_git_staging():
        """
        add_selected_text_to_git_staging

        Args:
            None

        Returns:
            None: Description of return value.
        """
        selected_text = output_text.get("sel.first", "sel.last")
        if selected_text:
            execute_command(f"add -f {selected_text}")

    def unstage_selected_text():
        """
        unstage_selected_text

        Args:
            None

        Returns:
            None: Description of return value.
        """
        selected_text = output_text.get("sel.first", "sel.last")
        if selected_text:
            execute_command(f"reset -- {selected_text}")

    def get_git_status():
        """
        get_git_status

        Args:
            None

        Returns:
            None: Description of return value.
        """
        return subprocess.check_output(
            ["git", "status", "--porcelain", "-u"], text=True
        )

    def show_git_diff():
        """
        show_git_diff

        Args:
            None

        Returns:
            None: Description of return value.
        """
        git_diff_command = "git diff --color"
        try:
            output = subprocess.check_output(
                git_diff_command, shell=True, stderr=subprocess.STDOUT
            )
            output = output.decode("utf-8", errors="replace")
            diff_window = Toplevel(terminal_window)
            diff_window.title("Git Diff")
            diff_window.geometry("800x600")
            diff_text = Text(diff_window, height=20, width=80)
            diff_text.pack(fill="both", expand=True)
            define_ansi_tags(diff_text)
            ansi_escape = re.compile("\\x1B\\[[0-?]*[ -/]*[@-~]")
            for line in output.split("\n"):
                line_clean = ansi_escape.sub("", line)
                if line.startswith("+"):
                    diff_text.insert(END, line_clean + "\n", "addition")
                elif line.startswith("-"):
                    diff_text.insert(END, line_clean + "\n", "deletion")
                elif line.startswith("@"):
                    diff_text.insert(END, line_clean + "\n", "info")
                else:
                    diff_text.insert(END, line_clean + "\n")
            diff_text.config(state="disabled")
        except subprocess.CalledProcessError as e:
            output_text.insert(END, f"Error: {e.output}\n", "error")

    def update_output_text(output_text_widget):
        """
        update_output_text

        Args:
            output_text_widget (Any): Description of output_text_widget.

        Returns:
            None: Description of return value.
        """
        git_status = get_git_status()
        define_ansi_tags(output_text_widget)
        if git_status == "":
            output_text_widget.insert("end", "Your branch is up to date.\n\n")
        else:
            for line in git_status.split("\n"):
                status = line[:2]
                filename = line[3:]
                if status in [" M", "M "]:
                    output_text_widget.insert("end", status, "modified")
                    output_text_widget.insert("end", " <" + filename + ">\n")
                elif status == "MM":
                    output_text_widget.insert("end", status, "modified_multiple")
                    output_text_widget.insert("end", " " + filename + "\n")
                elif status == "??":
                    output_text_widget.insert("end", status, "untracked")
                    output_text_widget.insert("end", " " + filename + "\n")
                elif status == "A ":
                    output_text_widget.insert("end", status, "added")
                    output_text_widget.insert("end", " " + filename + "\n")
                elif status in [" D", "D "]:
                    output_text_widget.insert("end", status, "deleted")
                    output_text_widget.insert("end", " " + filename + "\n")
                elif status == "R ":
                    output_text_widget.insert("end", status, "renamed")
                    output_text_widget.insert("end", " " + filename + "\n")
                elif status == "C ":
                    output_text_widget.insert("end", status, "copied")
                    output_text_widget.insert("end", " " + filename + "\n")
                elif status == "U ":
                    output_text_widget.insert("end", status, "unmerged")
                    output_text_widget.insert("end", " " + filename + "\n")
                elif status == "!!":
                    output_text_widget.insert("end", status, "ignored")
                    output_text_widget.insert("end", " " + filename + "\n")
                else:
                    output_text_widget.insert("end", status)
                    output_text_widget.insert("end", " " + filename + "\n")
                try:
                    if status in [" M", "M "]:
                        git_diff_command = f"git diff --color {filename}"
                        diff_output = subprocess.check_output(
                            git_diff_command, shell=True, stderr=subprocess.STDOUT
                        )
                        diff_output = diff_output.decode("utf-8", errors="replace")
                        ansi_escape = re.compile("\\x1B\\[[0-?]*[ -/]*[@-~]")
                        for diff_line in diff_output.split("\n")[1:]:
                            line_clean = ansi_escape.sub("", diff_line)
                            apply_ansi_styles(output_text, line_clean)
                        output_text_widget.insert("end", " </" + filename + ">\n\n")
                except subprocess.CalledProcessError as e:
                    output_text.insert(END, f"Error: {e.output}\n", "error")

    context_menu = Menu(output_text)
    output_text.bind(
        "<Button-3>", lambda event: context_menu.tk_popup(event.x_root, event.y_root)
    )
    context_menu.add_command(label="Git Add", command=add_selected_text_to_git_staging)
    context_menu.add_command(
        label="Git Status", command=lambda: execute_command("status")
    )
    context_menu.add_command(label="Git Unstage", command=unstage_selected_text)
    context_menu.add_command(label="Git Diff", command=show_git_diff)
    top_frame = Frame(terminal_window)
    top_frame.pack(fill="both", expand=True)
    commit_scrollbar = Scrollbar(top_frame)
    commit_scrollbar.pack(side="right", fill="y")
    commit_list = Listbox(top_frame, yscrollcommand=commit_scrollbar.set)
    commit_list.pack(side="left", fill="both", expand=True)
    commit_scrollbar.config(command=commit_list.yview)
    commit_list.bind("<Button-3>", commit_list_context_menu)
    update_commit_list(commit_list)
    button_frame = Frame(terminal_window)
    button_frame.pack(fill="both", expand=False)
    common_commands = ["commit", "push", "pull", "fetch"]
    for command in common_commands:
        button = Button(
            button_frame,
            text=f"{git_icons[command]} {command.capitalize()}",
            command=lambda c=command: execute_command(c),
        )
        button.pack(side="left")
    entry = Entry(button_frame, width=80)
    entry.pack(side="left", fill="x", expand=True)
    entry.focus()
    entry.bind("<Return>", lambda event: execute_command(entry.get()))
    entry.bind("<Up>", navigate_history)
    entry.bind("<Down>", navigate_history)
    execute_command("status --porcelain -u")


def open_kanban_window():
    """
    open_kanban_window

    Args:
        None

    Returns:
        None: Description of return value.
    """
    global kanban_data, columns_frame, drag_label
    kanban_data = {
        "columns": [
            "To Do",
            "In Progress",
            "Testing",
            "Done",
            "Continuous Improvement",
        ],
        "tasks": [
            {
                "title": "Task 1",
                "description": "Description 1",
                "priority": "High",
                "column": "To Do",
            },
            {
                "title": "Task 2",
                "description": "Description 2",
                "priority": "Medium",
                "column": "In Progress",
            },
        ],
        "wip_limits": {
            "To Do": 10,
            "In Progress": 5,
            "Testing": 5,
            "Done": float("inf"),
            "Continuous Improvement": 5,
        },
    }
    drag_label = None

    def load_kanban_data():
        """
        load_kanban_data

        Args:
            None

        Returns:
            None: Description of return value.
        """
        global kanban_data
        try:
            with open("data/kanban_tasks.json", "r") as f:
                kanban_data = json.load(f)
        except FileNotFoundError:
            save_kanban_data()

    def save_kanban_data():
        """
        save_kanban_data

        Args:
            None

        Returns:
            None: Description of return value.
        """
        with open("data/kanban_tasks.json", "w") as f:
            json.dump(kanban_data, f, indent=4)

    def on_drag_start(event):
        """
        on_drag_start

        Args:
            event (Any): Description of event.

        Returns:
            None: Description of return value.
        """
        global drag_label
        widget = event.widget
        index = widget.nearest(event.y)
        _, y, _, height = widget.bbox(index)
        if y <= event.y < y + height:
            widget.drag_data = widget.get(index)
            widget.selection_clear(0, END)
            widget.selection_set(index)
            widget.itemconfig(index, {"bg": "lightblue"})
            drag_label = Label(kanban_window, text=widget.drag_data, relief=RAISED)
            drag_label.place(x=event.x_root, y=event.y_root, anchor="center")

    def on_drag_motion(event):
        """
        on_drag_motion

        Args:
            event (Any): Description of event.

        Returns:
            None: Description of return value.
        """
        global drag_label
        widget = event.widget
        if hasattr(widget, "drag_data") and drag_label:
            x, y = kanban_window.winfo_pointerxy()
            drag_label.place(x=x, y=y, anchor="center")
            target = widget.winfo_containing(x, y)
            if isinstance(target, Listbox):
                for child in columns_frame.winfo_children():
                    if isinstance(child, Frame):
                        child.config(bg="SystemButtonFace")
                target.master.config(bg="lightgreen")

    def on_drop(event):
        """
        on_drop

        Args:
            event (Any): Description of event.

        Returns:
            None: Description of return value.
        """
        global drag_label
        widget = event.widget
        if hasattr(widget, "drag_data"):
            x, y = widget.winfo_pointerxy()
            target = widget.winfo_containing(x, y)
            if isinstance(target, Listbox) and target != widget:
                item = widget.drag_data
                origin_column = widget.column
                target_column = target.column
                for task in kanban_data["tasks"]:
                    if task["title"] == item:
                        task["column"] = target_column
                        break
                save_kanban_data()
                refresh_kanban_board()
            for child in columns_frame.winfo_children():
                if isinstance(child, Frame):
                    child.config(bg="SystemButtonFace")
            if drag_label:
                drag_label.destroy()
                drag_label = None
            delattr(widget, "drag_data")

    def setup_drag_and_drop(listbox, column):
        """
        setup_drag_and_drop

        Args:
            listbox (Any): Description of listbox.
            column (Any): Description of column.

        Returns:
            None: Description of return value.
        """
        listbox.column = column
        listbox.bind("<ButtonPress-1>", on_drag_start)
        listbox.bind("<B1-Motion>", on_drag_motion)
        listbox.bind("<ButtonRelease-1>", on_drop)

    def add_task(event, column):
        """
        add_task

        Args:
            event (Any): Description of event.
            column (Any): Description of column.

        Returns:
            None: Description of return value.
        """
        task_title = event.widget.get()
        if task_title:
            new_task = {
                "title": task_title,
                "description": "",
                "priority": "Medium",
                "column": column,
            }
            kanban_data["tasks"].append(new_task)
            save_kanban_data()
            refresh_kanban_board()

    def create_column(column_name):
        """
        create_column

        Args:
            column_name (Any): Description of column_name.

        Returns:
            None: Description of return value.
        """
        column_frame = Frame(columns_frame, borderwidth=2, relief="raised")
        column_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=5)
        label = Label(
            column_frame,
            text=f"{column_name} (Limit: {kanban_data['wip_limits'][column_name]})",
        )
        label.pack(pady=5)
        task_list = Listbox(column_frame, selectmode=SINGLE)
        task_list.pack(fill=BOTH, expand=True, padx=5, pady=5)
        for task in [t for t in kanban_data["tasks"] if t["column"] == column_name]:
            task_list.insert(END, task["title"])
        setup_drag_and_drop(task_list, column_name)
        entry = Entry(column_frame)
        entry.pack(fill=X, padx=5, pady=5)
        entry.bind("<Return>", lambda event, col=column_name: add_task(event, col))

    def refresh_kanban_board():
        """
        refresh_kanban_board

        Args:
            None

        Returns:
            None: Description of return value.
        """
        for widget in columns_frame.winfo_children():
            widget.destroy()
        for column in kanban_data["columns"]:
            create_column(column)
        for column_frame in columns_frame.winfo_children():
            entry_widget = column_frame.winfo_children()[-1]
            if isinstance(entry_widget, Entry):
                entry_widget.delete(0, END)

    kanban_window = Toplevel()
    kanban_window.title("Kanban Board")
    kanban_window.geometry("1280x720")
    columns_frame = Frame(kanban_window)
    columns_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
    load_kanban_data()
    refresh_kanban_board()
    kanban_window.protocol(
        "WM_DELETE_WINDOW", lambda: (save_kanban_data(), kanban_window.destroy())
    )


def open_calculator_window():
    """
    open_calculator_window

    Args:
        None

    Returns:
        None: Description of return value.
    """
    calculator_window = Toplevel()
    calculator_window.title("Advanced Scientific Calculator")
    calculator_window.geometry("500x600")
    expression_entry = Entry(
        calculator_window,
        width=30,
        font=("Arial", 18),
        borderwidth=2,
        relief="solid",
        justify="right",
    )
    expression_entry.grid(
        row=0, column=0, columnspan=5, padx=10, pady=10, sticky="nsew"
    )
    result_label = Label(
        calculator_window,
        text="",
        font=("Arial", 20, "bold"),
        anchor="e",
        background="white",
        foreground="black",
        borderwidth=2,
        relief="solid",
    )
    result_label.grid(row=1, column=0, columnspan=5, padx=10, pady=5, sticky="nsew")
    original_states = {}

    def update_result_display(message):
        """
        update_result_display

        Args:
            message (Any): Description of message.

        Returns:
            None: Description of return value.
        """
        result_label.config(text=message)

    def copy_result_to_clipboard(event):
        """
        copy_result_to_clipboard

        Args:
            event (Any): Description of event.

        Returns:
            None: Description of return value.
        """
        result = result_label.cget("text")
        calculator_window.clipboard_clear()
        calculator_window.clipboard_append(result)

    result_label.bind("<Button-1>", copy_result_to_clipboard)
    result_label.bind("<Double-Button-1>", copy_result_to_clipboard)

    def button_click(value):
        """
        button_click

        Args:
            value (Any): Description of value.

        Returns:
            None: Description of return value.
        """
        current = expression_entry.get()
        if current in ("Error", "Invalid Input"):
            expression_entry.delete(0, END)
        if expression_entry.selection_present():
            selection_start = expression_entry.index(SEL_FIRST)
            selection_end = expression_entry.index(SEL_LAST)
            expression_entry.delete(selection_start, selection_end)
            expression_entry.insert(selection_start, value)
            expression_entry.icursor(selection_start + len(value))
        else:
            cursor_position = expression_entry.index(INSERT)
            expression_entry.insert(cursor_position, value)
            expression_entry.icursor(cursor_position + len(value))

    def clear_entry():
        """
        clear_entry

        Args:
            None

        Returns:
            None: Description of return value.
        """
        expression_entry.delete(0, END)
        update_result_display("")

    def clear_last_entry():
        """
        clear_last_entry

        Args:
            None

        Returns:
            None: Description of return value.
        """
        current = expression_entry.get()
        cursor_position = expression_entry.index(INSERT)
        if expression_entry.selection_present():
            selection_start = expression_entry.index(SEL_FIRST)
            selection_end = expression_entry.index(SEL_LAST)
            expression_entry.delete(selection_start, selection_end)
            expression_entry.icursor(selection_start)
            return
        if cursor_position == 0:
            return
        pattern = "(\\d+\\.\\d+|\\d+|[a-zA-Z_][a-zA-Z0-9_]*|\\S)"
        tokens = list(re.finditer(pattern, current[:cursor_position]))
        if not tokens:
            return
        last_token = tokens[-1]
        start, end = (last_token.start(), last_token.end())
        expression_entry.delete(start, cursor_position)
        expression_entry.icursor(start)

    def backspace():
        """
        backspace

        Args:
            None

        Returns:
            None: Description of return value.
        """
        if expression_entry.selection_present():
            selection_start = expression_entry.index(SEL_FIRST)
            selection_end = expression_entry.index(SEL_LAST)
            expression_entry.delete(selection_start, selection_end)
            expression_entry.icursor(selection_start)
        else:
            cursor_position = expression_entry.index(INSERT)
            if cursor_position > 0:
                expression_entry.delete(cursor_position - 1, cursor_position)

    def toggle_scientific_calculator_buttons():
        """
        toggle_scientific_calculator_buttons

        Args:
            None

        Returns:
            None: Description of return value.
        """
        toggle_map = {
            "x²": ("x³", lambda value="**3": button_click(value)),
            "xʸ": ("x⁽¹/ʸ⁾", lambda value="**(1/y)": button_click(value)),
            "sin": ("asin", lambda: scientific_function_click("asin")),
            "cos": ("acos", lambda: scientific_function_click("acos")),
            "tan": ("atan", lambda: scientific_function_click("atan")),
            "√": ("¹/ₓ", lambda value="1/": button_click(value)),
            "10ˣ": ("eˣ", lambda value="math.e**": button_click(value)),
            "log": ("ln", lambda: scientific_function_click("ln")),
            "Exp": ("dms", lambda value="dms(": button_click(value)),
            "Mod": ("deg", lambda value="deg(": button_click(value)),
        }
        for btn in calculator_buttons:
            current_text = btn["text"]
            if current_text in toggle_map:
                if btn not in original_states:
                    original_states[btn] = (current_text, btn["command"])
                new_text, new_command = toggle_map[current_text]
                btn.config(text=new_text, command=new_command)
            elif any((current_text == pair[0] for pair in toggle_map.values())):
                reverse_map = {v[0]: (k, v[1]) for k, v in toggle_map.items()}
                original_text, original_command = reverse_map[current_text]
                if btn in original_states:
                    original_text, original_command = original_states[btn]
                    btn.config(text=original_text, command=original_command)

    def balance_parentheses(expr):
        """
        balance_parentheses

        Args:
            expr (Any): Description of expr.

        Returns:
            None: Description of return value.
        """
        open_count = expr.count("(")
        close_count = expr.count(")")
        return expr + ")" * (open_count - close_count)

    def evaluate_expression():
        """
        evaluate_expression

        Args:
            None

        Returns:
            None: Description of return value.
        """
        try:
            expression = expression_entry.get().strip()
            if not expression:
                update_result_display("Error: Empty expression")
                return
            expression = balance_parentheses(expression)
            replacements = {
                "sin": "sin",
                "cos": "cos",
                "tan": "tan",
                "asin": "asin",
                "acos": "acos",
                "atan": "atan",
                "log": "log",
                "ln": "ln",
                "sqrt": "sqrt",
                "abs": "abs",
                "π": "pi",
                "e": "e",
                "**": "**",
                "^": "**",
                "√": "sqrt",
            }
            for old, new in replacements.items():
                expression = expression.replace(old, new)
            expression = re.sub("(\\([^()]*\\)|\\d+)!", "factorial\\1", expression)
            expression = re.sub("(\\d+)([a-zA-Z\\(])", "\\1*\\2", expression)
            expression = re.sub("([a-zA-Z\\)])(\\d+)", "\\1*\\2", expression)
            expression = re.sub("([^\\s\\w\\.\\(\\)])", " \\1 ", expression)
            safe_dict = {
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "asin": math.asin,
                "acos": math.acos,
                "atan": math.atan,
                "sqrt": math.sqrt,
                "abs": abs,
                "log": math.log10,
                "ln": math.log,
                "factorial": math.factorial,
                "pi": math.pi,
                "e": math.e,
            }
            if re.search("[^\\d\\w\\s\\+\\-\\*\\/\\^\\(\\)\\.\\,\\!]", expression):
                update_result_display("Error: Invalid characters in expression")
                return
            result = eval(expression, {"__builtins__": None}, safe_dict)
            if isinstance(result, (int, float)):
                formatted_result = f"{result:.8g}"
            elif isinstance(result, complex):
                formatted_result = (
                    f"{result.real:.8g} + {result.imag:.8g}j"
                    if result.imag != 0
                    else f"{result.real:.8g}"
                )
            else:
                formatted_result = str(result)
            update_result_display(formatted_result)
        except ZeroDivisionError:
            update_result_display("Error: Division by zero")
        except ValueError as ve:
            update_result_display(f"Error: {str(ve)}")
        except SyntaxError:
            update_result_display("Error: Invalid syntax")
        except Exception as e:
            update_result_display(f"Error: {str(e)}")

    def scientific_function_click(func_name):
        """
        scientific_function_click

        Args:
            func_name (Any): Description of func_name.

        Returns:
            None: Description of return value.
        """
        value = f"{func_name}("
        if expression_entry.selection_present():
            selection_start = expression_entry.index(SEL_FIRST)
            selection_end = expression_entry.index(SEL_LAST)
            expression_entry.delete(selection_start, selection_end)
            expression_entry.insert(selection_start, value)
            expression_entry.icursor(selection_start + len(value))
        else:
            cursor_position = expression_entry.index(INSERT)
            expression_entry.insert(cursor_position, value)
            expression_entry.icursor(cursor_position + len(value))

    button_texts = [
        ("x²", 1, 0),
        ("xʸ", 1, 1),
        ("sin", 1, 2),
        ("cos", 1, 3),
        ("tan", 1, 4),
        ("√", 2, 0),
        ("10ˣ", 2, 1),
        ("log", 2, 2),
        ("Exp", 2, 3),
        ("Mod", 2, 4),
        ("↑", 3, 0),
        ("CE", 3, 1),
        ("C", 3, 2),
        ("←", 3, 3),
        ("/", 3, 4),
        ("π", 4, 0),
        ("7", 4, 1),
        ("8", 4, 2),
        ("9", 4, 3),
        ("*", 4, 4),
        ("e", 5, 0),
        ("4", 5, 1),
        ("5", 5, 2),
        ("6", 5, 3),
        ("-", 5, 4),
        ("x!", 6, 0),
        ("1", 6, 1),
        ("2", 6, 2),
        ("3", 6, 3),
        ("+", 6, 4),
        ("(", 7, 0),
        (")", 7, 1),
        ("0", 7, 2),
        (".", 7, 3),
        ("=", 7, 4),
    ]
    calculator_buttons = []
    for text, row, col in button_texts:
        if text == "=":
            btn = Button(
                calculator_window,
                text=text,
                width=8,
                height=2,
                command=evaluate_expression,
            )
        elif text == "C":
            btn = Button(
                calculator_window, text=text, width=8, height=2, command=clear_entry
            )
        elif text == "CE":
            btn = Button(
                calculator_window,
                text=text,
                width=8,
                height=2,
                command=clear_last_entry,
            )
        elif text == "10ˣ":
            btn = Button(
                calculator_window,
                text=text,
                width=8,
                height=2,
                command=lambda: button_click("10**"),
            )
        elif text in (
            "sin",
            "cos",
            "tan",
            "log",
            "ln",
            "abs",
            "asin",
            "acos",
            "atan",
            "√",
        ):
            btn = Button(
                calculator_window,
                text=text,
                width=8,
                height=2,
                command=lambda t=text: scientific_function_click(t),
            )
        elif text in ("π", "e", "j"):
            btn = Button(
                calculator_window,
                text=text,
                width=8,
                height=2,
                command=lambda t=text: button_click(t),
            )
        elif text == "x!":
            btn = Button(
                calculator_window,
                text=text,
                width=8,
                height=2,
                command=lambda: button_click("!"),
            )
        elif text == "←":
            btn = Button(
                calculator_window, text="←", width=8, height=2, command=backspace
            )
        elif text == "↑":
            btn = Button(
                calculator_window,
                text="↑",
                width=8,
                height=2,
                command=toggle_scientific_calculator_buttons,
            )
        else:
            btn = Button(
                calculator_window,
                text=text,
                width=8,
                height=2,
                command=lambda t=text: button_click(t),
            )
        calculator_buttons.append(btn)
        btn.grid(row=row + 1, column=col, padx=2, pady=2)
    for i in range(9):
        calculator_window.grid_rowconfigure(i, weight=1)
    for i in range(5):
        calculator_window.grid_columnconfigure(i, weight=1)
    calculator_window.bind("<Return>", lambda event: evaluate_expression())
    calculator_window.bind("<Escape>", lambda event: clear_entry())
    calculator_window.mainloop()


def open_terminal_window():
    """
    Opens a new window functioning as a terminal within the application.

    This function creates a top-level window that simulates a terminal, allowing users to
    enter and execute commands with output displayed in the window.

    Parameters:
    None

    Returns:
    None
    """
    terminal_window = Toplevel()
    terminal_window.title("Terminal")
    terminal_window.geometry("600x400")
    output_text = scrolledtext.ScrolledText(terminal_window, height=20, width=80)
    output_text.pack(fill="both", expand=True)
    command_history = []
    history_pointer = [0]

    def execute_command(event=None):
        """
        execute_command

        Args:
            event (Any): Description of event.

        Returns:
            None: Description of return value.
        """
        command = entry.get()
        if command.strip():
            command_history.append(command)
            history_pointer[0] = len(command_history)
            try:
                output = subprocess.check_output(
                    command,
                    stderr=subprocess.STDOUT,
                    shell=True,
                    text=True,
                    cwd=os.getcwd(),
                )
                output_text.insert(END, f"{command}\n{output}\n")
            except subprocess.CalledProcessError as e:
                output_text.insert(END, f"Error: {e.output}", "error")
            entry.delete(0, END)
            output_text.see(END)

    def navigate_history(event):
        """
        navigate_history

        Args:
            event (Any): Description of event.

        Returns:
            None: Description of return value.
        """
        if command_history:
            if event.keysym == "Up":
                history_pointer[0] = max(0, history_pointer[0] - 1)
            elif event.keysym == "Down":
                history_pointer[0] = min(len(command_history), history_pointer[0] + 1)
            command = (
                command_history[history_pointer[0]]
                if history_pointer[0] < len(command_history)
                else ""
            )
            entry.delete(0, END)
            entry.insert(0, command)

    entry = Entry(terminal_window, width=80)
    entry.pack(side="bottom", fill="x")
    entry.focus()
    entry.bind("<Return>", execute_command)
    entry.bind("<Up>", navigate_history)
    entry.bind("<Down>", navigate_history)


def open_audio_generation_window():
    """
    open_audio_generation_window

    Args:
        None

    Returns:
        None: Description of return value.
    """

    def generate_audio():
        """
        generate_audio

        Args:
            None

        Returns:
            None: Description of return value.
        """
        model_path = model_path_entry.get()
        prompt = prompt_entry.get()
        start_time = start_time_entry.get()
        duration = duration_entry.get()
        output_path = output_path_entry.get()
        if (
            not model_path
            or not prompt
            or (not start_time)
            or (not duration)
            or (not output_path)
        ):
            messagebox.showwarning("Input Error", "Please fill all fields.")
            return
        status_label.config(text="Starting audio generation...")
        generate_button.config(state=DISABLED)
        output_queue = queue.Queue()
        threading.Thread(
            target=run_audio_generation,
            args=(model_path, prompt, start_time, duration, output_path, output_queue),
        ).start()
        generation_window.after(100, lambda: update_progress(output_queue))

    def run_audio_generation(
        model_path, prompt, start_time, duration, output_path, output_queue
    ):
        """
        run_audio_generation

        Args:
            model_path (Any): Description of model_path.
            prompt (Any): Description of prompt.
            start_time (Any): Description of start_time.
            duration (Any): Description of duration.
            output_path (Any): Description of output_path.
            output_queue (Any): Description of output_queue.

        Returns:
            None: Description of return value.
        """
        try:
            process = subprocess.Popen(
                [
                    ".\\venv\\Scripts\\python.exe",
                    ".\\lib\\stableAudioCpp.py",
                    "--model_path",
                    model_path,
                    "--prompt",
                    prompt,
                    "--start",
                    start_time,
                    "--total",
                    duration,
                    "--out-dir",
                    output_path,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for line in process.stdout:
                output_queue.put(line.strip())
            process.wait()
            if process.returncode == 0:
                output_queue.put("Audio generation completed successfully.")
                output_queue.put(f"LOAD_AUDIO:{output_path}")
                output_queue.put(f"AUDIO GENERATED AT {output_path}")
            else:
                output_queue.put(f"Audio generation failed: {process.stderr.read()}")
        except subprocess.CalledProcessError as e:
            output_queue.put(f"Audio generation failed: {e}")
            return
        output_queue.put("DONE")

    def update_progress(output_queue):
        """
        update_progress

        Args:
            output_queue (Any): Description of output_queue.

        Returns:
            None: Description of return value.
        """
        try:
            while not output_queue.empty():
                line = output_queue.get_nowait()
                if line.startswith("LOAD_AUDIO:"):
                    load_audio(line.split(":", 1)[1])
                elif line.startswith("AUDIO GENERATED AT"):
                    status_label.config(text=line)
                else:
                    status_label.config(text=f"Progress: {line}")
        except queue.Empty:
            pass
        finally:
            if not "AUDIO GENERATED AT" in status_label.cget("text") and (
                not "failed" in status_label.cget("text")
            ):
                generation_window.after(100, lambda: update_progress(output_queue))
            else:
                generate_button.config(state=NORMAL)

    def load_audio(audio_path):
        """
        load_audio

        Args:
            audio_path (Any): Description of audio_path.

        Returns:
            None: Description of return value.
        """
        try:
            status_label.config(text=f"Audio generated at {audio_path}")
        except Exception as e:
            messagebox.showerror("Audio Error", f"Could not load audio: {e}")

    def select_model_path():
        """
        select_model_path

        Args:
            None

        Returns:
            None: Description of return value.
        """
        path = filedialog.askopenfilename(filetypes=[("Checkpoint Files", "*.ckpt")])
        model_path_entry.delete(0, END)
        model_path_entry.insert(0, path)

    def select_output_path():
        """
        select_output_path

        Args:
            None

        Returns:
            None: Description of return value.
        """
        path = filedialog.asksaveasfilename(
            defaultextension=".wav", filetypes=[("WAV Files", "*.wav")]
        )
        output_path_entry.delete(0, END)
        output_path_entry.insert(0, path)

    generation_window = Toplevel()
    generation_window.title("Audio Generation")
    generation_window.geometry("480x580")
    Label(generation_window, text="Model Path:").grid(
        row=0, column=0, padx=10, pady=5, sticky="e"
    )
    model_path_entry = Entry(generation_window, width=30)
    model_path_entry.grid(row=0, column=1, padx=10, pady=5)
    Button(generation_window, text="Browse", command=select_model_path).grid(
        row=0, column=2, padx=10, pady=5
    )
    Label(generation_window, text="Prompt:").grid(
        row=1, column=0, padx=10, pady=5, sticky="e"
    )
    prompt_entry = Entry(generation_window, width=30)
    prompt_entry.grid(row=1, column=1, padx=10, pady=5)
    Label(generation_window, text="Start Time:").grid(
        row=2, column=0, padx=10, pady=5, sticky="e"
    )
    start_time_entry = Entry(generation_window, width=30)
    start_time_entry.grid(row=2, column=1, padx=10, pady=5)
    Label(generation_window, text="Duration:").grid(
        row=3, column=0, padx=10, pady=5, sticky="e"
    )
    duration_entry = Entry(generation_window, width=30)
    duration_entry.grid(row=3, column=1, padx=10, pady=5)
    Label(generation_window, text="Output Path:").grid(
        row=4, column=0, padx=10, pady=5, sticky="e"
    )
    output_path_entry = Entry(generation_window, width=30)
    output_path_entry.grid(row=4, column=1, padx=10, pady=5)
    Button(generation_window, text="Save As", command=select_output_path).grid(
        row=4, column=2, padx=10, pady=5
    )
    generate_button = Button(
        generation_window, text="Generate Audio", command=generate_audio
    )
    generate_button.grid(row=5, column=0, columnspan=3, pady=10)
    status_label = Label(
        generation_window, text="Status: Waiting to start...", width=60, anchor="w"
    )
    status_label.grid(row=6, column=0, columnspan=3, padx=10, pady=10)
    Label(generation_window, text="Audio Preview:").grid(
        row=7, column=0, columnspan=3, pady=10
    )
    audio_label = Label(
        generation_window,
        text="No audio generated yet",
        width=40,
        height=20,
        relief="sunken",
    )
    audio_label.grid(row=8, column=0, columnspan=3, padx=10, pady=10)


def open_music_generation_window():
    """
    open_music_generation_window

    Args:
        None

    Returns:
        None: Description of return value.
    """
    pass


def open_image_generation_window():
    """
    open_image_generation_window

    Args:
        None

    Returns:
        None: Description of return value.
    """

    def generate_image():
        """
        generate_image

        Args:
            None

        Returns:
            None: Description of return value.
        """
        model_path = model_path_entry.get()
        prompt = prompt_entry.get()
        output_path = output_path_entry.get()
        if not model_path or not prompt or (not output_path):
            messagebox.showwarning("Input Error", "Please fill all fields.")
            return
        status_label.config(text="Starting image generation...")
        generate_button.config(state=DISABLED)
        output_queue = queue.Queue()
        threading.Thread(
            target=run_image_generation,
            args=(model_path, prompt, output_path, output_queue),
        ).start()
        generation_window.after(100, lambda: update_progress(output_queue))

    def run_image_generation(model_path, prompt, output_path, output_queue):
        """
        run_image_generation

        Args:
            model_path (Any): Description of model_path.
            prompt (Any): Description of prompt.
            output_path (Any): Description of output_path.
            output_queue (Any): Description of output_queue.

        Returns:
            None: Description of return value.
        """
        try:
            process = subprocess.Popen(
                [
                    ".\\venv\\Scripts\\python.exe",
                    ".\\lib\\stableDiffusionCpp.py",
                    "--model_path",
                    model_path,
                    "--prompt",
                    prompt,
                    "--output_path",
                    output_path,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for line in process.stdout:
                output_queue.put(line.strip())
            process.wait()
            if process.returncode == 0:
                output_queue.put("Image generation completed successfully.")
                output_queue.put(f"LOAD_IMAGE:{output_path}")
                output_queue.put(f"IMAGE GENERATED AT {output_path}")
            else:
                output_queue.put(f"Image generation failed: {process.stderr.read()}")
        except subprocess.CalledProcessError as e:
            output_queue.put(f"Image generation failed: {e}")
        output_queue.put("DONE")

    def update_progress(output_queue):
        """
        update_progress

        Args:
            output_queue (Any): Description of output_queue.

        Returns:
            None: Description of return value.
        """
        try:
            while not output_queue.empty():
                line = output_queue.get_nowait()
                if line.startswith("LOAD_IMAGE:"):
                    load_image(line.split(":", 1)[1])
                elif line.startswith("IMAGE GENERATED AT"):
                    status_label.config(text=line)
                else:
                    status_label.config(text=f"Progress: {line}")
        except queue.Empty:
            pass
        finally:
            if not "IMAGE GENERATED AT" in status_label.cget("text") and (
                not "failed" in status_label.cget("text")
            ):
                generation_window.after(100, lambda: update_progress(output_queue))
            else:
                generate_button.config(state=NORMAL)

    def load_image(image_path):
        """
        load_image

        Args:
            image_path (Any): Description of image_path.

        Returns:
            None: Description of return value.
        """
        try:
            img = Image.open(image_path)
            img = img.resize((250, 250), Image.ANTIALIAS)
            img_tk = ImageTk.PhotoImage(img)
            image_label.config(image=img_tk)
            image_label.image = img_tk
        except Exception as e:
            messagebox.showerror("Image Error", f"Could not load image: {e}")

    def select_model_path():
        """
        select_model_path

        Args:
            None

        Returns:
            None: Description of return value.
        """
        path = filedialog.askopenfilename(filetypes=[("Checkpoint Files", "*.ckpt")])
        model_path_entry.delete(0, END)
        model_path_entry.insert(0, path)

    def select_output_path():
        """
        select_output_path

        Args:
            None

        Returns:
            None: Description of return value.
        """
        path = filedialog.asksaveasfilename(
            defaultextension=".png", filetypes=[("PNG Files", "*.png")]
        )
        output_path_entry.delete(0, END)
        output_path_entry.insert(0, path)

    generation_window = Toplevel()
    generation_window.title("Image Generation")
    generation_window.geometry("480x580")
    Label(generation_window, text="Model Path:").grid(
        row=0, column=0, padx=10, pady=5, sticky="e"
    )
    model_path_entry = Entry(generation_window, width=30)
    model_path_entry.grid(row=0, column=1, padx=10, pady=5)
    Button(generation_window, text="Browse", command=select_model_path).grid(
        row=0, column=2, padx=10, pady=5
    )
    Label(generation_window, text="Prompt:").grid(
        row=1, column=0, padx=10, pady=5, sticky="e"
    )
    prompt_entry = Entry(generation_window, width=30)
    prompt_entry.grid(row=1, column=1, padx=10, pady=5)
    Label(generation_window, text="Output Path:").grid(
        row=2, column=0, padx=10, pady=5, sticky="e"
    )
    output_path_entry = Entry(generation_window, width=30)
    output_path_entry.grid(row=2, column=1, padx=10, pady=5)
    Button(generation_window, text="Save As", command=select_output_path).grid(
        row=2, column=2, padx=10, pady=5
    )
    generate_button = Button(
        generation_window, text="Generate Image", command=generate_image
    )
    generate_button.grid(row=3, column=0, columnspan=3, pady=10)
    status_label = Label(
        generation_window, text="Status: Waiting to start...", width=60, anchor="w"
    )
    status_label.grid(row=4, column=0, columnspan=3, padx=10, pady=10)
    Label(generation_window, text="Image Preview:").grid(
        row=5, column=0, columnspan=3, pady=10
    )
    image_label = Label(
        generation_window,
        text="No image generated yet",
        width=40,
        height=20,
        relief="sunken",
    )
    image_label.grid(row=6, column=0, columnspan=3, padx=10, pady=10)


def add_current_main_opened_script(include_main_script):
    """
    add_current_main_opened_script

    Args:
        include_main_script (Any): Description of include_main_script.

    Returns:
        None: Description of return value.
    """
    global include_main_script_in_command
    include_main_script_in_command = include_main_script


def add_current_selected_text(include_selected_text):
    """
    add_current_selected_text

    Args:
        include_selected_text (Any): Description of include_selected_text.

    Returns:
        None: Description of return value.
    """
    global include_selected_text_in_command
    include_selected_text_in_command = include_selected_text


def open_ai_assistant_window(session_id=None):
    """
    Opens a window for interacting with an AI assistant.

    This function creates a new window where users can input commands or queries, and the AI assistant
    processes and displays the results. It also provides options for rendering Markdown to HTML.

    Parameters:
    None

    Returns:
    None
    """
    global original_md_content, markdown_render_enabled, rendered_html_content, session_data, url_data

    def start_llama_cpp_python_server():
        """
        start_llama_cpp_python_server

        Args:
            None

        Returns:
            None: Description of return value.
        """
        file_path = find_gguf_file()
        print("THE PATH TO THE MODEL IS:\t", file_path)

    def open_ai_server_settings_window():
        """
        open_ai_server_settings_window

        Args:
            None

        Returns:
            None: Description of return value.
        """
        json_path = "data/llm_server_providers.json"

        def toggle_display(selected_server):
            """
            toggle_display

            Args:
                selected_server (Any): Description of selected_server.

            Returns:
                None: Description of return value.
            """
            server_info = server_details.get(selected_server, {})
            server_url = server_info.get("server_url", "")
            api_key = server_info.get("api_key", "")
            server_url_entry.delete(0, END)
            server_url_entry.insert(0, server_url)
            api_key_entry.delete(0, END)
            api_key_entry.insert(0, api_key)
            if selected_server in [
                "lmstudio",
                "ollama",
                "openai",
                "llama-cpp-python",
                "claude",
                "gemini",
            ]:
                server_url_entry.grid()
                server_url_label.grid()
            else:
                server_url_entry.grid_remove()
                server_url_label.grid_remove()
            if selected_server in ["openai", "claude", "gemini"]:
                api_key_entry.grid()
                api_key_label.grid()
            else:
                api_key_entry.grid_remove()
                api_key_label.grid_remove()

        def load_server_details():
            """
            load_server_details

            Args:
                None

            Returns:
                None: Description of return value.
            """
            try:
                with open("data/llm_server_providers.json", "r") as server_file:
                    return json.load(server_file)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                messagebox.showerror(
                    "Error", f"Failed to load server details: {str(e)}"
                )
                return {}

        def load_api_key_names():
            """
            load_api_key_names

            Args:
                None

            Returns:
                None: Description of return value.
            """
            with open(json_path, "r") as file:
                data = json.load(file)
            api_keys = {
                provider: details["api_key"]
                for provider, details in data.items()
                if details["api_key"] != "not-needed"
            }
            return api_keys

        def get_env_variable(variable_name):
            """
            get_env_variable

            Args:
                variable_name (Any): Description of variable_name.

            Returns:
                None: Description of return value.
            """
            env_path = ".env"
            if os.path.exists(env_path):
                with open(env_path, "r") as file:
                    for line in file:
                        if line.startswith(f"{variable_name}="):
                            return line.split("=", 1)[1].strip()

        def update_env_file(api_key_field, new_api_key):
            """
            update_env_file

            Args:
                api_key_field (Any): Description of api_key_field.
                new_api_key (Any): Description of new_api_key.

            Returns:
                None: Description of return value.
            """
            env_path = ".env"
            updated = False
            if os.path.exists(env_path):
                with open(env_path, "r") as file:
                    lines = file.readlines()
                with open(env_path, "w") as file:
                    for line in lines:
                        if line.startswith(api_key_field + "="):
                            file.write(f"{api_key_field}={new_api_key}\n")
                            updated = True
                        else:
                            file.write(line)
                if not updated:
                    with open(env_path, "a") as file:
                        file.write(f"{api_key_field}={new_api_key}\n")
            else:
                with open(env_path, "w") as file:
                    file.write(f"{api_key_field}={new_api_key}\n")

        def save_ai_server_settings():
            """
            save_ai_server_settings

            Args:
                None

            Returns:
                None: Description of return value.
            """
            server_url = server_url_entry.get()
            api_keys = load_api_key_names()
            selected = selected_server.get()
            new_api_key = api_key_entry.get()
            api_key_field = api_keys.get(selected)
            if not new_api_key:
                env_api_key = get_env_variable(api_key_field)
                if env_api_key:
                    new_api_key = env_api_key
                else:
                    messagebox.showerror(
                        "Error",
                        f"No API key found for {selected}. Please enter a valid API key.",
                    )
                    return
            if new_api_key not in api_keys.values():
                if selected in ["openai", "claude", "gemini"]:
                    update_env_file(api_key_field, new_api_key)
                    messagebox.showinfo(
                        "AI Server Settings", "API Key updated successfully!"
                    )
                else:
                    api_key_field = "not-needed"
            else:
                messagebox.showinfo(
                    "AI Server Settings",
                    "No changes made. The API Key entered is a placeholder.",
                )
            write_config_parameter(
                "options.network_settings.last_selected_llm_server_provider", selected
            )
            write_config_parameter("options.network_settings.server_url", server_url)
            write_config_parameter("options.network_settings.api_key", api_key_field)
            settings_window.destroy()

        server_details = load_server_details()
        settings_window = Toplevel()
        settings_window.title("AI Server Settings")
        settings_window.geometry("400x300")
        Label(settings_window, text="Select Server:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        selected_server = StringVar(settings_window)
        last_selected = read_config_parameter(
            "options.network_settings.last_selected_llm_server_provider"
        )
        selected_server.set(
            last_selected
            if last_selected in server_details
            else next(iter(server_details), "")
        )
        server_options = list(server_details.keys())
        server_dropdown = OptionMenu(settings_window, selected_server, *server_options)
        server_dropdown.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        server_url_label = Label(settings_window, text="Server URL:")
        server_url_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        server_url_entry = Entry(settings_window, width=25)
        server_url_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        api_key_label = Label(settings_window, text="API Key:")
        api_key_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)
        api_key_entry = Entry(settings_window, width=25, show="*")
        api_key_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        Button(settings_window, text="Save", command=save_ai_server_settings).grid(
            row=3, column=0, columnspan=2, pady=10
        )
        selected_server.trace("w", lambda *args: toggle_display(selected_server.get()))
        toggle_display(selected_server.get())
        settings_window.columnconfigure(1, weight=1)
        settings_window.mainloop()

    def open_ai_server_agent_settings_window():
        """
        open_ai_server_agent_settings_window

        Args:
            None

        Returns:
            None: Description of return value.
        """

        def load_agents():
            """
            Load agents from the JSON file located at ScriptsEditor/data/agents.json.

            Returns:
            agents (list): A list of agents loaded from the JSON file.
            """
            current_dir = os.path.dirname(os.path.abspath(__file__))
            json_file_path = os.path.join(
                current_dir, "..", "..", "data", "agents.json"
            )
            json_file_path = os.path.normpath(json_file_path)
            print("JSON PATH:", json_file_path)
            try:
                with open(json_file_path, "r") as file:
                    agents = json.load(file)
                return agents
            except FileNotFoundError:
                messagebox.showerror("Error", f"File not found: {json_file_path}")
                return []
            except json.JSONDecodeError:
                messagebox.showerror(
                    "Error", f"Error decoding JSON from file: {json_file_path}"
                )
                return []

        def update_instructions(selected_agent):
            """
            update_instructions

            Args:
                selected_agent (Any): Description of selected_agent.

            Returns:
                None: Description of return value.
            """
            global selected_agent_var
            selected_agent_var = selected_agent
            for agent in agents:
                if agent["name"] == selected_agent:
                    instructions_text.delete("1.0", "end")
                    instructions_text.insert("1.0", agent["instructions"])
                    temperature_entry.delete(0, "end")
                    temperature_entry.insert(0, agent["temperature"])
                    break

        def save_agent_settings():
            """
            save_agent_settings

            Args:
                None

            Returns:
                None: Description of return value.
            """
            global selected_agent_var
            selected_agent = selected_agent_var
            print("SAVE_AGENT_SETTINTS!!!\n", selected_agent, "\n", "* " * 25)
            selected_agent_var = selected_agent
            temperature = temperature_entry.get()
            execute_ai_assistant_command(
                add_current_main_opened_script_var,
                add_current_selected_text_var,
                entry.get(),
            )
            status_label_var.set(selected_agent)
            messagebox.showinfo("Agent Settings", "Settings saved successfully!")
            settings_window.destroy()

        agents = load_agents()
        if not agents:
            return
        settings_window = Toplevel()
        settings_window.title("AI Server Agent Settings")
        Label(settings_window, text="Select Agent:").grid(row=0, column=0)
        selected_agent_var = StringVar(settings_window)
        selected_agent_var.set(agents[0]["name"])
        agent_options = [agent["name"] for agent in agents]
        agent_dropdown = OptionMenu(
            settings_window,
            selected_agent_var,
            *agent_options,
            command=update_instructions,
        )
        agent_dropdown.grid(row=0, column=1)
        Label(settings_window, text="Instructions:").grid(row=1, column=0)
        instructions_text = scrolledtext.ScrolledText(
            settings_window, height=7, width=50
        )
        instructions_text.grid(row=1, column=1, columnspan=2)
        agent_temperature = [agent["temperature"] for agent in agents]
        Label(settings_window, text="Temperature:").grid(row=2, column=0)
        temperature_entry = Entry(settings_window)
        temperature_entry.grid(row=2, column=1)
        persistent_agent_selection_checkbox = Checkbutton(
            settings_window,
            text="Persistent Agent Selection",
            variable=persistent_agent_selection_var,
        )
        persistent_agent_selection_checkbox.grid(row=3, columnspan=2)
        Button(
            settings_window, text="Save", command=lambda: save_agent_settings()
        ).grid(row=4, column=0)
        Button(settings_window, text="Cancel", command=settings_window.destroy).grid(
            row=4, column=1
        )
        update_instructions(selected_agent_var.get())

    original_md_content = ""
    rendered_html_content = ""
    markdown_render_enabled = False
    session_data = []
    url_data = []
    ai_assistant_window = Toplevel()
    ai_assistant_window.title("AI Assistant")
    ai_assistant_window.geometry("800x600")
    menu_bar = Menu(ai_assistant_window)
    ai_assistant_window.config(menu=menu_bar)
    settings_menu = Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Settings", menu=settings_menu)
    menu_bar.add_command(
        label="AI Server Settings", command=open_ai_server_settings_window
    )
    menu_bar.add_command(
        label="Agent Options", command=open_ai_server_agent_settings_window
    )
    render_markdown_var = IntVar()
    settings_menu.add_checkbutton(
        label="Toggle Markdown-to-HTML Rendering",
        onvalue=1,
        offvalue=0,
        variable=render_markdown_var,
        command=lambda: toggle_render_markdown(render_markdown_var.get()),
    )
    add_current_main_opened_script_var = IntVar()
    settings_menu.add_checkbutton(
        label="Include Main Script in AI Context",
        onvalue=1,
        offvalue=0,
        variable=add_current_main_opened_script_var,
        command=lambda: add_current_main_opened_script(
            add_current_main_opened_script_var.get()
        ),
    )
    add_current_selected_text_var = IntVar()
    settings_menu.add_checkbutton(
        label="Include Selected Text from Script",
        onvalue=1,
        offvalue=0,
        variable=add_current_selected_text_var,
        command=lambda: add_current_selected_text(add_current_selected_text_var.get()),
    )
    persistent_agent_selection_var = IntVar()
    'settings_menu.add_checkbutton(\n        label="Persistent Agent Selection",\n        onvalue=1,\n        offvalue=0,\n        variable=persistent_agent_selection_var,\n        #command=lambda: add_current_selected_text(add_current_selected_text_var.get())\n    )'
    session_list_frame = Frame(ai_assistant_window)
    session_list_frame.pack(side="left", fill="y")
    Label(session_list_frame, text="SESSIONS", font=("Helvetica", 10, "bold")).pack(
        fill="x"
    )
    sessions_list = Listbox(session_list_frame)
    sessions_list.pack(fill="both", expand=True)
    Separator(session_list_frame, orient="horizontal").pack(fill="x", pady=5)
    Label(session_list_frame, text="LINKS", font=("Helvetica", 10, "bold")).pack(
        fill="x"
    )
    links_frame = Frame(session_list_frame)
    links_frame.pack(fill="both", expand=True)
    links_list = Listbox(links_frame)
    links_list.pack(fill="both", expand=True)

    def refresh_links_list():
        """
        refresh_links_list

        Args:
            None

        Returns:
            None: Description of return value.
        """
        print("Refreshing links list...")
        links_list.delete(0, END)
        for idx, url in enumerate(url_data):
            links_list.insert(END, url)

    def add_new_link():
        """
        add_new_link

        Args:
            None

        Returns:
            None: Description of return value.
        """
        print("Adding new link...")
        new_url = simpledialog.askstring("Add New Link", "Enter URL:")
        if new_url:
            url_data.append(new_url)
            refresh_links_list()

    def delete_selected_link():
        """
        delete_selected_link

        Args:
            None

        Returns:
            None: Description of return value.
        """
        print("Deleting selected link...")
        selected_link_index = links_list.curselection()
        if selected_link_index:
            url_data.pop(selected_link_index[0])
            refresh_links_list()

    def edit_selected_link():
        """
        edit_selected_link

        Args:
            None

        Returns:
            None: Description of return value.
        """
        selected_link_index = links_list.curselection()
        if selected_link_index:
            selected_link = links_list.get(selected_link_index)
            new_url = simpledialog.askstring(
                "Edit Link", "Enter new URL:", initialvalue=selected_link
            )
            if new_url:
                url_data[selected_link_index[0]] = new_url
                refresh_links_list()

    links_context_menu = Menu(ai_assistant_window, tearoff=0)

    def show_links_context_menu(event):
        """
        show_links_context_menu

        Args:
            event (Any): Description of event.

        Returns:
            None: Description of return value.
        """
        if links_list.size() == 0:
            links_context_menu.delete(0, END)
            links_context_menu.add_command(label="Add New Link", command=add_new_link)
        else:
            links_context_menu.delete(0, END)
            selected_link_index = links_list.curselection()
            if selected_link_index:
                links_context_menu.add_command(
                    label="Edit Link", command=edit_selected_link
                )
                links_context_menu.add_command(
                    label="Delete Selected Link", command=delete_selected_link
                )
            else:
                links_context_menu.add_command(
                    label="Add New Link", command=add_new_link
                )
        links_context_menu.post(event.x_root, event.y_root)

    links_list.bind("<Button-3>", show_links_context_menu)
    refresh_links_list()
    Separator(session_list_frame, orient="horizontal").pack(fill="x", pady=5)
    Label(session_list_frame, text="DOCUMENTS", font=("Helvetica", 10, "bold")).pack(
        fill="x"
    )
    documents_frame = Frame(session_list_frame)
    documents_frame.pack(fill="both", expand=True)
    document_paths = []
    document_checkbuttons = []

    def refresh_documents_list():
        """
        refresh_documents_list

        Args:
            None

        Returns:
            None: Description of return value.
        """
        print("Refreshing documents list...")
        for widget in documents_frame.winfo_children():
            widget.destroy()
        for idx, doc_path in enumerate(document_paths):
            doc_name = os.path.basename(doc_path)
            var = IntVar()
            checkbutton = Checkbutton(documents_frame, text=doc_name, variable=var)
            checkbutton.pack(anchor="w")
            document_checkbuttons.append((doc_path, var))

    def add_new_document():
        """
        add_new_document

        Args:
            None

        Returns:
            None: Description of return value.
        """
        print("Adding new document...")
        file_path = filedialog.askopenfilename(
            initialdir=".",
            title="Select a PDF document",
            filetypes=(("PDF files", "*.pdf"), ("all files", "*.*")),
        )
        if file_path:
            document_paths.append(file_path)
            refresh_documents_list()

    refresh_documents_list()
    documents_context_menu = Menu(ai_assistant_window, tearoff=0)
    documents_context_menu.add_command(
        label="Add New Document", command=add_new_document
    )

    def show_documents_context_menu(event):
        """
        show_documents_context_menu

        Args:
            event (Any): Description of event.

        Returns:
            None: Description of return value.
        """
        documents_context_menu.post(event.x_root, event.y_root)

    documents_frame.bind("<Button-3>", show_documents_context_menu)
    output_text = scrolledtext.ScrolledText(ai_assistant_window, height=20, width=80)
    output_text.pack(fill="both", expand=True)
    html_display = HTMLLabel(ai_assistant_window, html="")
    html_display.pack(side="left", fill="both", expand=False)
    html_display.pack_forget()
    entry = Entry(ai_assistant_window, width=30)
    entry.pack(side="bottom", fill="x")
    Tooltip(entry, "Input text prompt")
    status_label_var = StringVar()
    status_label = Label(ai_assistant_window, textvariable=status_label_var)
    status_label.pack(side="bottom")
    status_label_var.set("READY")
    output_text.tag_configure("user", foreground="#a84699")
    output_text.tag_configure("ai", foreground="#6a7fd2")
    output_text.tag_configure("error", foreground="red")
    output_text.insert(END, "> ", "ai")
    entry.focus()

    def on_md_content_change(event=None):
        """
        on_md_content_change

        Args:
            event (Any): Description of event.

        Returns:
            None: Description of return value.
        """
        global original_md_content
        original_md_content = script_text.get("1.0", END)
        if markdown_render_enabled:
            update_html_content()

    def update_html_content():
        """
        update_html_content

        Args:
            None

        Returns:
            None: Description of return value.
        """
        global rendered_html_content
        rendered_html_content = markdown.markdown(original_md_content)
        html_display.set_html(rendered_html_content)

    def update_html_content_thread():
        """
        update_html_content_thread

        Args:
            None

        Returns:
            None: Description of return value.
        """
        global rendered_html_content
        rendered_html_content = markdown.markdown(original_md_content)
        html_display.set_html(rendered_html_content)

    def toggle_render_markdown(is_checked):
        """
        toggle_render_markdown

        Args:
            is_checked (Any): Description of is_checked.

        Returns:
            None: Description of return value.
        """
        global markdown_render_enabled
        markdown_render_enabled = bool(is_checked)
        if markdown_render_enabled:
            threading.Thread(target=update_html_content_thread).start()
            output_text.pack_forget()
            html_display.pack(fill="both", expand=True)
        else:
            output_text.delete("1.0", "end")
            output_text.insert("1.0", original_md_content)
            html_display.pack_forget()
            output_text.pack(fill="both", expand=True)

    def navigate_history(event):
        """
        navigate_history

        Args:
            event (Any): Description of event.

        Returns:
            None: Description of return value.
        """
        if command_history:
            if event.keysym == "Up":
                history_pointer[0] = max(0, history_pointer[0] - 1)
            elif event.keysym == "Down":
                history_pointer[0] = min(len(command_history), history_pointer[0] + 1)
            command = (
                command_history[history_pointer[0]]
                if history_pointer[0] < len(command_history)
                else ""
            )
            entry.delete(0, END)
            entry.insert(0, command)

    def stream_output(process):
        """
        stream_output

        Args:
            process (Any): Description of process.

        Returns:
            None: Description of return value.
        """
        global current_session
        ai_response_buffer = ""
        try:
            while True:
                char = process.stdout.read(1)
                if char:
                    ai_response_buffer += char
                    if markdown_render_enabled:
                        update_html_content()
                    else:
                        output_text.insert(END, char, "ai")
                        output_text.see(END)
                elif process.poll() is not None:
                    break
            if ai_response_buffer:
                current_session.add_message("ai", ai_response_buffer)
        except Exception as e:
            output_text.insert(END, f"Error: {e}\n", "error")
        finally:
            on_processing_complete()

    def on_processing_complete():
        """
        on_processing_complete

        Args:
            None

        Returns:
            None: Description of return value.
        """
        load_selected_agent()
        entry.config(state="normal")
        status_label_var.set("READY")

    def store_selected_agent(selected_agent):
        """
        store_selected_agent

        Args:
            selected_agent (Any): Description of selected_agent.

        Returns:
            None: Description of return value.
        """
        with open("data/agent_config.json", "w") as config_file:
            json.dump({"selected_agent": selected_agent}, config_file)

    def load_selected_agent():
        """
        load_selected_agent

        Args:
            None

        Returns:
            None: Description of return value.
        """
        try:
            with open("data/config.json", "r") as config_file:
                config_data = json.load(config_file)
                return config_data.get("selected_agent", selected_agent_var)
        except FileNotFoundError:
            pass

    def execute_ai_assistant_command(opened_script_var, selected_text_var, ai_command):
        """
        execute_ai_assistant_command

        Args:
            opened_script_var (Any): Description of opened_script_var.
            selected_text_var (Any): Description of selected_text_var.
            ai_command (Any): Description of ai_command.

        Returns:
            None: Description of return value.
        """
        global original_md_content, selected_agent_var, current_session
        if not current_session:
            create_session()
        if ai_command.strip():
            script_content = ""
            if selected_text_var.get():
                try:
                    script_content = (
                        "```\n"
                        + script_text.get(
                            script_text.tag_ranges("sel")[0],
                            script_text.tag_ranges("sel")[1],
                        )
                        + "```\n\n"
                    )
                except:
                    messagebox.showerror(
                        "Error", "No text selected in main script window."
                    )
                    return
            elif opened_script_var.get():
                script_content = "```\n" + script_text.get("1.0", END) + "```\n\n"
            combined_command = f"{script_content}{ai_command}"
            current_session.add_message("user", combined_command)
            original_md_content += f"\n{combined_command}\n"
            original_md_content += "-" * 80 + "\n"
            output_text.insert("end", f"You: {combined_command}\n", "user")
            output_text.insert("end", "-" * 80 + "\n")
            entry.delete(0, END)
            entry.config(state="disabled")
            status_label_var.set("AI is thinking...")
            ai_script_path = "src/models/ai_assistant.py"
            if persistent_agent_selection_var.get():
                try:
                    selected_agent = selected_agent_var
                except Exception as e:
                    selected_agent_var = "Assistant"
                    selected_agent = selected_agent_var
                store_selected_agent(selected_agent)
            else:
                print("Non persistant agent")
                selected_agent_var = "Assistant"
                selected_agent = selected_agent_var
            command = create_ai_command(
                ai_script_path, combined_command, selected_agent
            )
            print("SAVE AI MESSAGE BEFORE")
            process_ai_command(command)
            print("SAVE AI MESSAGE END")
        else:
            entry.config(state="normal")

    def create_ai_command(ai_script_path, user_prompt, agent_name=None):
        """
        create_ai_command

        Args:
            ai_script_path (Any): Description of ai_script_path.
            user_prompt (Any): Description of user_prompt.
            agent_name (Any): Description of agent_name.

        Returns:
            None: Description of return value.
        """
        if platform.system() == "Windows":
            python_executable = os.path.join("venv", "Scripts", "python")
        else:
            python_executable = os.path.join("venv", "bin", "python3")
        if agent_name:
            return [python_executable, ai_script_path, user_prompt, agent_name]
        else:
            return [python_executable, ai_script_path, user_prompt]

    def process_ai_command(command):
        """
        process_ai_command

        Args:
            command (Any): Description of command.

        Returns:
            None: Description of return value.
        """
        global process, selected_agent_var
        try:
            if "process" in globals() and process.poll() is None:
                process.terminate()
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                bufsize=1,
            )
            threading.Thread(target=stream_output, args=(process,)).start()
        except Exception as e:
            output_text.insert(END, f"Error: {e}\n")
            on_processing_complete()
        finally:
            update_html_content()
            status_label_var.set(f"{selected_agent_var} is thinking")

    def read_ai_command(command_name, user_prompt):
        """
        read_ai_command

        Args:
            command_name (Any): Description of command_name.
            user_prompt (Any): Description of user_prompt.

        Returns:
            None: Description of return value.
        """
        commands_file = "data/commands.json"
        try:
            with open(commands_file, "r") as f:
                commands_data = json.load(f)

            def find_command(commands, command_name):
                """
                find_command

                Args:
                    commands (Any): Description of commands.
                    command_name (Any): Description of command_name.

                Returns:
                    None: Description of return value.
                """
                for command in commands:
                    if command["name"] == command_name:
                        return command
                    if "submenu" in command:
                        result = find_command(command["submenu"], command_name)
                        if result:
                            return result
                return None

            matching_command = find_command(
                commands_data["customCommands"], command_name
            )
            if matching_command:
                original_prompt = matching_command.get("prompt", "")
                formatted_prompt = original_prompt.replace("{{{ input }}}", user_prompt)
                return formatted_prompt
            else:
                return f"Command '{command_name}' not found."
        except FileNotFoundError:
            return f"Error: File '{commands_file}' not found."
        except json.JSONDecodeError:
            return f"Error: Failed to decode JSON from '{commands_file}'."

    def ai_assistant_rightclick_menu(command):
        """
        ai_assistant_rightclick_menu

        Args:
            command (Any): Description of command.

        Returns:
            None: Description of return value.
        """
        selected_text = output_text.get("sel.first", "sel.last")
        if selected_text.strip():
            fix_user_prompt = read_ai_command(command, selected_text)
            execute_ai_assistant_command(
                add_current_main_opened_script_var,
                add_current_selected_text_var,
                fix_user_prompt,
            )

    def nlp_custom():
        """
        nlp_custom

        Args:
            None

        Returns:
            None: Description of return value.
        """
        selected_text = output_text.get("sel.first", "sel.last")
        if selected_text.strip():
            print(read_ai_command("code-optimize", selected_text))

    def show_context_menu(event):
        """
        show_context_menu

        Args:
            event (Any): Description of event.

        Returns:
            None: Description of return value.
        """
        commands_file = "data/commands.json"

        def load_commands():
            """
            load_commands

            Args:
                None

            Returns:
                None: Description of return value.
            """
            try:
                with open(commands_file, "r") as f:
                    commands_data = json.load(f)
                return commands_data["customCommands"]
            except (FileNotFoundError, json.JSONDecodeError) as e:
                messagebox.showerror("Error", f"Failed to load commands: {e}")
                return []

        def add_commands_to_menu(menu, commands):
            """
            add_commands_to_menu

            Args:
                menu (Any): Description of menu.
                commands (Any): Description of commands.

            Returns:
                None: Description of return value.
            """
            for command in commands:
                if "submenu" in command:
                    submenu = Menu(menu, tearoff=0)
                    menu.add_cascade(label=command["name"], menu=submenu)
                    add_commands_to_menu(submenu, command["submenu"])
                elif command["name"] == "---":
                    menu.add_separator()
                else:
                    menu.add_command(
                        label=command["description"],
                        command=lambda cmd=command: ai_assistant_rightclick_menu(
                            cmd["name"]
                        ),
                    )
                    if "description" in command:
                        Tooltip(menu, command["description"])

        context_menu = Menu(root, tearoff=0)
        context_menu.add_command(label="Cut", command=cut)
        context_menu.add_command(label="Copy", command=copy)
        context_menu.add_command(label="Paste", command=paste)
        context_menu.add_command(label="Duplicate", command=duplicate)
        context_menu.add_command(label="Select All", command=duplicate)
        context_menu.add_separator()
        custom_commands = load_commands()
        add_commands_to_menu(context_menu, custom_commands)
        context_menu.add_separator()
        context_menu.add_command(label="Custom AI request", command=nlp_custom)
        context_menu.post(event.x_root, event.y_root)
        context_menu.focus_set()

        def destroy_menu():
            """
            destroy_menu

            Args:
                None

            Returns:
                None: Description of return value.
            """
            context_menu.unpost()

        context_menu.bind("<Leave>", lambda e: destroy_menu())
        context_menu.bind("<FocusOut>", lambda e: destroy_menu())

    output_text.bind("<Button-3>", show_context_menu)
    output_text.bind("<<TextModified>>", on_md_content_change)
    output_text.see(END)
    entry.bind(
        "<Return>",
        lambda event: execute_ai_assistant_command(
            add_current_main_opened_script_var,
            add_current_selected_text_var,
            entry.get(),
        ),
    )
    entry.bind("<Up>", navigate_history)
    entry.bind("<Down>", navigate_history)
    command_history = []
    history_pointer = [0]

    class Session:
        """
        Session

        Description of the class.
        """

        def __init__(self, session_id, load_existing=True):
            """
            __init__

            Args:
                self (Any): Description of self.
                session_id (Any): Description of session_id.
                load_existing (Any): Description of load_existing.

            Returns:
                None: Description of return value.
            """
            self.id = session_id
            self.name = ""
            self.file_path = os.path.join(
                "data", "conversations", self.id, f"session_{self.id}.json"
            )
            self.messages = []
            if load_existing and os.path.exists(self.file_path):
                self.load()
            else:
                self.name = f"Session {self.id}"
                self.save()

        def add_message(self, role, content):
            """
            add_message

            Args:
                self (Any): Description of self.
                role (Any): Description of role.
                content (Any): Description of content.

            Returns:
                None: Description of return value.
            """
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
            }
            self.messages.append(message)
            self.save()

        def save(self):
            """
            save

            Args:
                self (Any): Description of self.

            Returns:
                None: Description of return value.
            """
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            data = {
                "session_id": self.id,
                "session_name": self.name,
                "messages": self.messages,
            }
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        def load(self):
            """
            load

            Args:
                self (Any): Description of self.

            Returns:
                None: Description of return value.
            """
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.name = data.get("session_name", f"Session {self.id}")
                self.messages = data.get("messages", [])

    def create_session():
        """
        create_session

        Args:
            None

        Returns:
            None: Description of return value.
        """
        global current_session, session_data
        new_session_id = datetime.now().strftime("%Y%m%d%H%M%S")
        current_session = Session(new_session_id, load_existing=False)
        session_data.append(current_session)
        update_sessions_list()
        select_session(len(session_data) - 1)

    def update_chat_display():
        """
        update_chat_display

        Args:
            None

        Returns:
            None: Description of return value.
        """
        output_text.delete("1.0", END)
        if current_session:
            for message in current_session.messages:
                role_tag = "user" if message["role"] == "user" else "ai"
                output_text.insert(
                    END, f"{message['role']}: {message['content']}\n", role_tag
                )
        output_text.see(END)

    def load_session(session_id):
        """
        load_session

        Args:
            session_id (Any): Description of session_id.

        Returns:
            None: Description of return value.
        """
        global current_session
        for session in session_data:
            if session.id == session_id:
                current_session = session
                current_session.load()
                break
        update_chat_display()

    def select_session(index):
        """
        select_session

        Args:
            index (Any): Description of index.

        Returns:
            None: Description of return value.
        """
        global current_session
        sessions_list.selection_clear(0, END)
        sessions_list.selection_set(index)
        sessions_list.activate(index)
        sessions_list.see(index)
        current_session = session_data[index]
        current_session.load()
        update_chat_display()
        write_config_parameter(
            "options.network_settings.last_selected_session_id", index + 1
        )

    def update_sessions_list():
        """
        update_sessions_list

        Args:
            None

        Returns:
            None: Description of return value.
        """
        sessions_list.delete(0, END)
        for session in session_data:
            sessions_list.insert(END, session.name)

    def load_sessions(session_listbox):
        """
        load_sessions

        Args:
            session_listbox (Any): Description of session_listbox.

        Returns:
            None: Description of return value.
        """
        sessions_path = "data/conversations"
        session_folders = [
            f
            for f in os.listdir(sessions_path)
            if os.path.isdir(os.path.join(sessions_path, f))
        ]
        session_listbox.delete(0, "end")
        for session_folder in session_folders:
            session = Session(session_folder, load_existing=True)
            session_listbox.insert("end", session.name)

    def initialize_ai_assistant_window():
        """
        initialize_ai_assistant_window

        Args:
            None

        Returns:
            None: Description of return value.
        """
        global session_data, current_session
        sessions_path = "data/conversations"
        session_data = []
        if os.path.exists(sessions_path):
            for session_folder in os.listdir(sessions_path):
                session = Session(session_folder, load_existing=True)
                session_data.append(session)
        update_sessions_list()
        if session_data:
            select_session(len(session_data) - 1)
        else:
            create_session()

    def on_session_select(event):
        """
        on_session_select

        Args:
            event (Any): Description of event.

        Returns:
            None: Description of return value.
        """
        selected_indices = sessions_list.curselection()
        if selected_indices:
            index = selected_indices[0]
            load_session(session_data[index].id)

    def show_session_context_menu(event, session_index):
        """
        show_session_context_menu

        Args:
            event (Any): Description of event.
            session_index (Any): Description of session_index.

        Returns:
            None: Description of return value.
        """
        session_context_menu = Menu(ai_assistant_window, tearoff=0)
        session_context_menu.add_command(
            label="Share Chat", command=lambda: save_session(session_index)
        )
        session_context_menu.add_command(
            label="Change Name", command=lambda: rename_session(session_index)
        )
        session_context_menu.add_command(
            label="Archive", command=lambda: archive_session(session_index)
        )
        session_context_menu.add_command(
            label="Delete", command=lambda: delete_session(session_index)
        )
        session_context_menu.post(event.x_root, event.y_root)

    def save_session(session_index):
        """
        save_session

        Args:
            session_index (Any): Description of session_index.

        Returns:
            None: Description of return value.
        """
        print(f"Saving session {session_index}...")
        session = session_data[session_index]
        with open(f"session_{session['id']}.txt", "w") as f:
            f.write(session["content"])
            messagebox.showinfo(
                "Delete Session", f"Session {session['id']} deleted successfully."
            )

    def rename_session(session_index):
        """
        rename_session

        Args:
            session_index (Any): Description of session_index.

        Returns:
            None: Description of return value.
        """
        session = session_data[session_index]
        new_name = simpledialog.askstring(
            "Rename Session", "Enter new session name:", initialvalue=session.name
        )
        if new_name:
            session.name = new_name
            session.save()
            update_sessions_list()

    def archive_session(session_index):
        """
        archive_session

        Args:
            session_index (Any): Description of session_index.

        Returns:
            None: Description of return value.
        """
        print(f"Archiving session {session_index}...")
        messagebox.showinfo(
            "Archive Session",
            f"Session {session_data[session_index]['id']} archived successfully.",
        )

    def delete_session(session_index):
        """
        delete_session

        Args:
            session_index (Any): Description of session_index.

        Returns:
            None: Description of return value.
        """
        print(f"Deleting session {session_index}...")
        session = session_data.pop(session_index)
        update_sessions_list()
        messagebox.showinfo(
            "Delete Session", f"Session {session['id']} deleted successfully."
        )

    def handle_session_click(event):
        """
        handle_session_click

        Args:
            event (Any): Description of event.

        Returns:
            None: Description of return value.
        """
        session_context_menu = Menu(ai_assistant_window, tearoff=0)
        try:
            session_index = sessions_list.curselection()[0]
            session = session_data[session_index]
            session_context_menu.add_command(
                label="Share Chat", command=lambda: save_session(session_index)
            )
            session_context_menu.add_command(
                label="Change Name", command=lambda: rename_session(session_index)
            )
            session_context_menu.add_command(
                label="Archive", command=lambda: archive_session(session_index)
            )
            session_context_menu.add_command(
                label="Delete", command=lambda: delete_session(session_index)
            )
            session_context_menu.add_separator()
            session_context_menu.add_command(
                label="Create New Session", command=create_session
            )
        except IndexError:
            session_index = 0
        session_context_menu.add_command(
            label="Create New Session", command=create_session
        )
        session_context_menu.post(event.x_root, event.y_root)

    sessions_list.bind("<Button-3>", handle_session_click)
    sessions_list.bind("<<ListboxSelect>>", on_session_select)
    initialize_ai_assistant_window()
    ai_assistant_window.mainloop()


def _create_webview_process(title, url):
    """
    _create_webview_process

    Args:
        title (Any): Description of title.
        url (Any): Description of url.

    Returns:
        None: Description of return value.
    """
    webview.create_window(
        title, url, width=800, height=600, text_select=True, zoomable=True
    )
    webview.start(private_mode=True)


def open_webview(title, url):
    """
    open_webview

    Args:
        title (Any): Description of title.
        url (Any): Description of url.

    Returns:
        None: Description of return value.
    """
    webview_process = multiprocessing.Process(
        target=_create_webview_process, args=(title, url)
    )
    webview_process.start()


def open_url_in_webview(url):
    """
    open_url_in_webview

    Args:
        url (Any): Description of url.

    Returns:
        None: Description of return value.
    """
    webview.create_window(
        "My Web Browser",
        url,
        width=800,
        height=600,
        text_select=True,
        zoomable=True,
        easy_drag=True,
        confirm_close=True,
        background_color="#1f1f1f",
    )
    webview.start(private_mode=True)


def on_go_button_clicked(entry, window):
    """
    on_go_button_clicked

    Args:
        entry (Any): Description of entry.
        window (Any): Description of window.

    Returns:
        None: Description of return value.
    """
    url = entry.get()
    if not url.startswith("http://") and (not url.startswith("https://")):
        url = "https://" + url
    on_close(window)
    webview_process = multiprocessing.Process(target=open_url_in_webview, args=(url,))
    webview_process.start()


def create_url_input_window():
    """
    create_url_input_window

    Args:
        None

    Returns:
        None: Description of return value.
    """
    window = Toplevel(root)
    window.title("Enter URL")
    entry = Entry(window, width=50)
    entry.insert(0, "https://duckduckgo.com")
    entry.pack(padx=10, pady=10)
    entry.focus()
    go_button = Button(
        window, text="Go", command=lambda: on_go_button_clicked(entry, window)
    )
    go_button.pack(pady=5)
    window.bind("<Return>", lambda event: on_go_button_clicked(entry, window))


def on_enter(event, entry, window):
    """Event handler to trigger navigation when Enter key is pressed."""
    on_go_button_clicked(entry, window)


def on_close(window):
    """
    on_close

    Args:
        window (Any): Description of window.

    Returns:
        None: Description of return value.
    """
    window.destroy()
