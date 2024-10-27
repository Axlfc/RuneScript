import json
import os
import platform
import queue
import re
import shutil
import subprocess
import threading
import webbrowser

import requests
import hashlib
import markdown

from tkinter import (
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
    BOTH,
    LEFT,
    X,
    RAISED,
    BooleanVar,
    BOTTOM,
    FLAT
)
from tkinter.ttk import (
    Separator,
    Treeview,
    Notebook,
    Combobox
)
from tkhtmlview import HTMLLabel
from src.controllers.parameters import read_config_parameter, write_config_parameter
from src.models.AudioGenerationWindow import AudioGenerationWindow
from src.models.FindInFilesWindow import FindInFilesWindow
from src.models.GitWindow import GitWindow
from src.models.HelpWindow import HelpWindow
from src.models.IPythonNotebookTerminal import IPythonNotebookTerminal
from src.models.ImageGenerationWindow import ImageGenerationWindow
from src.models.KanbanWindow import KanbanWindow
from src.models.LaTeXMarkdownEditor import LaTeXMarkdownEditor
from src.models.MnemonicsWindow import MnemonicsWindow
from src.models.PromptEnhancementWindow import PromptEnhancementWindow
from src.models.PythonTerminalWindow import PythonTerminalWindow
from src.models.CalculatorWindow import CalculatorWindow
from src.models.SearchAndReplaceWindow import SearchAndReplaceWindow
from src.models.SearchWindow import SearchWindow
from src.models.ShortcutsWindow import ShortcutsWindow
from src.models.SettingsWindow import SettingsWindow
from src.models.TTSManager import TTSManager
from src.models.TerminalWindow import TerminalWindow
from src.models.TranslatorWindow import TranslatorWindow
from src.models.VaultRAG import VaultRAG
from src.models.WingetWindow import WingetWindow
from src.models.convert_pdf_to_text import process_pdf_to_text
from src.models.embeddings import generate_embedding
from src.views.tk_utils import text, script_text, root, current_session, menu
from src.views.ui_elements import Tooltip, ScrollableFrame
from src.models.ai_assistant import find_gguf_file
from difflib import SequenceMatcher
from datetime import datetime
from typing import List, Dict, Optional

git_console_instance = None


def open_find_in_files_window(event=None):
    return FindInFilesWindow()


def open_search_replace_window(event=None):
    return SearchAndReplaceWindow()


def open_search_window(event=None):
    return SearchWindow()


def open_help_window(event=None):
    return HelpWindow()


def open_shortcuts_window(event=None):
    return ShortcutsWindow()


def open_mnemonics_window(event=None):
    return MnemonicsWindow()


def report_problems(event=None):
    url = "https://github.com/Axlfc/ScriptsEditor/issues/new"
    try:
        webbrowser.open(url)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open web browser: {e}")


def create_settings_window(event=None):
    def load_themes_from_json(file_path):
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
        """ ""\"
        ""\"
            save_settings

                Args:
                    None

                Returns:
                    None: Description of return value.
            ""\"
        ""\" """
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
        """ ""\"
        ""\"
            reset_settings

                Args:
                    None

                Returns:
                    None: Description of return value.
            ""\"
        ""\" """
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


'''def create_settings_window(event=None):
    return SettingsWindow()'''


def open_system_info_window(event=None):
    system_info_window = Toplevel()
    system_info_window.title("System Information Viewer")
    system_info_window.geometry("800x600")
    notebook = Notebook(system_info_window)
    notebook.pack(expand=True, fill="both", padx=10, pady=10)

    def run_command(command, result_queue, label):
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
        for label, cmd in commands.items():
            run_command(cmd, result_queue, label)

    def create_info_frame(parent, commands):
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
        """"Connected Monitors": "Get-CimInstance -Namespace root\\wmi -Class WmiMonitorID | "
                              "ForEach-Object { $name = ($_.UserFriendlyName -notmatch 0 | "
                              "ForEach-Object { [char]$_ }) -join ''; $name }","Display Resolutions": "Add-Type -AssemblyName System.Windows.Forms; "
                               "[System.Windows.Forms.Screen]::AllScreens | ForEach-Object "
                               "{ "$($_.DeviceName): $($_.Bounds.Width)x$($_.Bounds.Height)" }",Battery Status""": "Get-CimInstance Win32_Battery | Select-Object Name, EstimatedChargeRemaining, BatteryStatus | Format-Table -AutoSize",
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
        """"Group Memberships": "Get-LocalGroupMember -Group 'Administrators' | Select-Object Name, "
                             "ObjectClass | Format-Table -AutoSize",Antivirus Software""": "Get-CimInstance -Namespace 'root\\SecurityCenter2' -ClassName AntiVirusProduct | Select-Object displayName, productState | Format-Table -AutoSize",
        "Firewall Configuration": "Get-NetFirewallProfile | Select-Object Name, Enabled | Format-Table -AutoSize",
        "Disk Encryption Status": "Get-BitLockerVolume | Select-Object MountPoint, VolumeStatus | Format-Table -AutoSize",
    }
    """performance_commands = {
        "CPU Usage (%)": "(Get-Counter '\\Processor(_Total)\\% Processor Time').CounterSamples."
                         "CookedValue",
        "Available Memory (MB)": "(Get-Counter '\\Memory\\Available MBytes').CounterSamples."
                                 "CookedValue",
        "Disk Read/Write Speeds": "Get-Counter -Counter '\\PhysicalDisk(_Total)\\Disk Read "
                                  "Bytes/sec','\\PhysicalDisk(_Total)\\Disk Write Bytes/sec' | "
                                  "Format-Table -AutoSize",
    }"""
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


def open_winget_window(event=None):
    return WingetWindow()


def open_git_window(repo_dir=None):
    return GitWindow(repo_dir)


def open_calculator_window(event=None):
    return CalculatorWindow()


def open_kanban_window(event=None):
    return KanbanWindow()


def open_latex_markdown_editor(event=None):
    return LaTeXMarkdownEditor()


def open_ipython_notebook_window(event=None):
    return IPythonNotebookTerminal()


def open_python_terminal_window(event=None):
    return PythonTerminalWindow()


def open_terminal_window(event=None):
    return TerminalWindow()


def open_prompt_enhancement_window(event=None):
    return PromptEnhancementWindow()


def open_translator_window(event=None):
    return TranslatorWindow()


def open_audio_generation_window():
    return AudioGenerationWindow()


def open_music_generation_window():
    pass


def open_image_generation_window():
    return ImageGenerationWindow()


def open_ai_assistant_window(session_id=None):
    global original_md_content, markdown_render_enabled, rendered_html_content, session_data, url_data

    tts_manager = TTSManager()

    def start_llama_cpp_python_server():
        file_path = find_gguf_file()
        print("THE PATH TO THE MODEL IS:\t", file_path)

    def open_ai_server_settings_window():
        json_path = "data/llm_server_providers.json"

        def toggle_display(selected_server):
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
            try:
                with open("data/llm_server_providers.json", "r") as server_file:
                    return json.load(server_file)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                messagebox.showerror(
                    "Error", f"Failed to load server details: {str(e)}"
                )
                return {}

        def load_api_key_names():
            with open(json_path, "r") as file:
                data = json.load(file)
            api_keys = {
                provider: details["api_key"]
                for provider, details in data.items()
                if details["api_key"] != "not-needed"
            }
            return api_keys

        def get_env_variable(variable_name):
            env_path = ".env"
            if os.path.exists(env_path):
                with open(env_path, "r") as file:
                    for line in file:
                        if line.startswith(f"{variable_name}="):
                            return line.split("=", 1)[1].strip()

        def update_env_file(api_key_field, new_api_key):
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
        def load_agents():
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

    def add_current_main_opened_script(include_main_script):
        global include_main_script_in_command
        include_main_script_in_command = include_main_script

    def add_current_selected_text(include_selected_text):
        global include_selected_text_in_command
        include_selected_text_in_command = include_selected_text

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
    tts_enabled_var = IntVar()
    settings_menu.add_checkbutton(
        label="Enable Text-to-Speech",
        onvalue=1,
        offvalue=0,
        variable=tts_enabled_var,
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
    """settings_menu.add_checkbutton(
        label="Persistent Agent Selection",
        onvalue=1,
        offvalue=0,
        variable=persistent_agent_selection_var,
        #command=lambda: add_current_selected_text(add_current_selected_text_var.get())
    )"""

    # Left side frame for sessions, links, and documents
    session_list_frame = Frame(ai_assistant_window)
    session_list_frame.pack(side="left", fill="y")

    # Sessions List
    Label(session_list_frame, text="SESSIONS", font=("Helvetica", 10, "bold")).pack(fill="x")
    sessions_list = Listbox(session_list_frame)
    sessions_list.pack(fill="both", expand=True)

    Separator(session_list_frame, orient="horizontal").pack(fill="x", pady=5)

    # Links List
    Label(session_list_frame, text="LINKS", font=("Helvetica", 10, "bold")).pack(fill="x")
    links_frame = Frame(session_list_frame)
    links_frame.pack(fill="both", expand=True)
    links_list = Listbox(links_frame)
    links_list.pack(fill="both", expand=True)

    def refresh_links_list():
        links_list.delete(0, END)
        if current_session:
            for url in current_session.links:
                links_list.insert(END, url)

    def find_content_boundaries(content, marker, marker_type=None):
        # Find the start of our marker
        marker_start = content.find(f"\n\n{marker}\n")
        if marker_start == -1:
            return None, None

        # Find the separator line that follows the marker
        separator_start = content.find("\n", marker_start + len(marker) + 3)
        if separator_start == -1:
            return None, None

        # Find the content start after the separator
        content_start = content.find("\n", separator_start + 1)
        if content_start == -1:
            return None, None

        # Initialize the end position
        end_index = len(content)

        # Get the current block's type (Document or Link)
        current_block_type = marker.split(":")[0] if ":" in marker else None

        # Find the next content block or chat message
        pos = content_start
        while pos < len(content):
            next_line_start = content.find("\n", pos + 1)
            if next_line_start == -1:
                break

            next_line = content[next_line_start:next_line_start + 100].strip()  # Look at start of next line

            # Check for next content block markers
            if (next_line.startswith("Document:") or
                    next_line.startswith("Link:") or
                    next_line.startswith("===== New Document")):
                # Found next content block
                end_index = next_line_start
                break

            # Check for chat messages
            elif next_line.startswith("USER:") or next_line.startswith("AI:"):
                # Found chat message
                end_index = next_line_start
                break

            pos = next_line_start

        # Trim any trailing whitespace from our content block
        while end_index > content_start and content[end_index - 1].isspace():
            end_index -= 1

        return marker_start, end_index

    def safely_remove_content(vault_path, marker, marker_type=None):
        try:
            with open(vault_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # Take a snapshot of all content blocks and chat messages
            original_blocks = [(m.start(), m.group()) for m in re.finditer(r'\n\n(Document:|Link:)[^\n]+\n', content)]
            original_chats = [(m.start(), m.group()) for m in re.finditer(r'\n\n(User:|Assistant:)[^\n]+', content)]

            # Find the boundaries of the content to remove
            start_index, end_index = find_content_boundaries(content, marker, marker_type)

            if start_index is None:
                print(f"Content not found in vault: {marker}")
                return False

            # Extract the content before and after the section to remove
            content_before = content[:start_index]
            content_after = content[end_index:]

            # Combine the content, ensuring proper spacing
            updated_content = content_before + content_after

            # Clean up any resulting multiple consecutive newlines
            while "\n\n\n" in updated_content:
                updated_content = updated_content.replace("\n\n\n", "\n\n")

            # Verify integrity of remaining content blocks and chat messages
            new_blocks = [(m.start(), m.group()) for m in
                          re.finditer(r'\n\n(Document:|Link:)[^\n]+\n', updated_content)]
            new_chats = [(m.start(), m.group()) for m in re.finditer(r'\n\n(User:|Assistant:)[^\n]+', updated_content)]

            # Remove the target block from original_blocks for comparison
            original_blocks = [block for block in original_blocks if marker not in block[1]]

            if len(new_blocks) != len(original_blocks) or len(new_chats) != len(original_chats):
                print("Warning: Content integrity check failed - aborting removal to prevent data loss")
                return False

            # Write back to file
            with open(vault_path, 'w', encoding='utf-8') as file:
                file.write(updated_content)

            # Verify the write was successful
            with open(vault_path, 'r', encoding='utf-8') as file:
                verification_content = file.read()
                final_blocks = [(m.start(), m.group()) for m in
                                re.finditer(r'\n\n(Document:|Link:)[^\n]+\n', verification_content)]
                final_chats = [(m.start(), m.group()) for m in
                               re.finditer(r'\n\n(User:|Assistant:)[^\n]+', verification_content)]

                if len(final_blocks) != len(original_blocks) or len(final_chats) != len(original_chats):
                    print("Warning: Post-write verification failed - content integrity may be compromised")
                    # Restore original content
                    with open(vault_path, 'w', encoding='utf-8') as restore_file:
                        restore_file.write(content)
                    return False

            return True

        except Exception as e:
            print(f"Error removing content from vault: {e}")
            return False

    def safely_add_content(vault_path, marker, content_to_add):
        try:
            # Read existing content
            if os.path.exists(vault_path):
                with open(vault_path, 'r', encoding='utf-8') as file:
                    existing_content = file.read()
            else:
                existing_content = ""

            # Count existing chat messages for verification
            original_chat_messages = len(
                [m for m in existing_content.split('\n') if m.strip().startswith(("User:", "Assistant:"))])

            # Check if content already exists
            if f"\n\n{marker}\n" in existing_content:
                print(f"Content already exists in vault: {marker}")
                return False

            # Find the last content block (Document or Link)
            last_content_pos = -1
            for pattern in ["\n\nDocument:", "\n\nLink:"]:
                pos = existing_content.rfind(pattern)
                last_content_pos = max(last_content_pos, pos)

            if last_content_pos == -1:
                # No existing content blocks, find first chat message
                first_chat = min(
                    (pos for pos in [
                        existing_content.find("\n\nUser:"),
                        existing_content.find("\n\nAssistant:")
                    ] if pos != -1),
                    default=len(existing_content)
                )
                insert_position = first_chat
            else:
                # Find the end of the last content block
                _, insert_position = find_content_boundaries(
                    existing_content,
                    existing_content[last_content_pos:].split('\n')[1].strip()
                )

            # Prepare the new content block
            separator = "=" * (len(marker) + 4)
            new_content_block = f"\n\n{marker}\n{separator}\n{content_to_add}"

            # Insert the new content
            updated_content = (
                    existing_content[:insert_position] +
                    new_content_block +
                    existing_content[insert_position:]
            )

            # Clean up any resulting multiple consecutive newlines
            while "\n\n\n" in updated_content:
                updated_content = updated_content.replace("\n\n\n", "\n\n")

            # Verify chat message preservation
            final_chat_messages = len(
                [m for m in updated_content.split('\n') if m.strip().startswith(("User:", "Assistant:"))])
            if final_chat_messages != original_chat_messages:
                print("Warning: Chat message count mismatch - aborting addition to prevent data loss")
                return False

            # Write back to file
            with open(vault_path, 'w', encoding='utf-8') as file:
                file.write(updated_content)

            return True

        except Exception as e:
            print(f"Error adding content to vault: {e}")
            return False

    def is_raw_file_url(url):
        raw_file_domains = ['raw.githubusercontent.com', 'gist.githubusercontent.com']
        return any(domain in url for domain in raw_file_domains)

    def scrape_raw_file_content(url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            # print(f"Error scraping content from {url}: {e}")
            messagebox.showerror("Error scraping", f"Content from {url} not added to vault.\n{e}")
            return None

    def add_link_to_vault(url, vault_path):
        content = scrape_raw_file_content(url)
        if content:
            marker = f"Link: {url}"
            if safely_add_content(vault_path, marker, content):
                # Update embeddings for the link
                embedding = generate_embedding(content)
                if embedding:
                    current_session.rag.store_embedding(marker, embedding)
                return True
        return False

    def remove_link_from_vault(url, vault_path):
        marker = f"Link: {url}"
        if safely_remove_content(vault_path, marker, "Link:"):
            print(f"Successfully removed content for link '{url}' from the vault.")
        else:
            print(f"Failed to remove content for link '{url}' from the vault.")

    def add_new_link():
        new_url = simpledialog.askstring("Add New Link", "Enter URL:")

        if new_url and current_session:
            # Check if the link already exists in the current session's links
            if new_url in current_session.links:
                messagebox.showerror("Duplicate Link", "This link has already been added.")
            else:
                vault_path = os.path.join("data", "conversations", current_session.id, "vault.md")
                success = True

                # Only attempt to add to vault if it's a raw file URL
                if is_raw_file_url(new_url):
                    success = add_link_to_vault(new_url, vault_path)

                # Only add to session and refresh list if everything succeeded
                if success:
                    current_session.add_link(new_url)
                    current_session.save()
                    refresh_links_list()
                else:
                    messagebox.showerror("Error", f"Failed to process link: {new_url}")

    def delete_selected_link():
        selected_link_index = links_list.curselection()
        if selected_link_index and current_session:
            url_to_remove = current_session.links.pop(selected_link_index[0])
            vault_path = os.path.join("data", "conversations", current_session.id, "vault.md")
            if is_raw_file_url(url_to_remove):
                remove_link_from_vault(url_to_remove, vault_path)
            current_session.save()
            refresh_links_list()

    def edit_selected_link():
        selected_link_index = links_list.curselection()
        if selected_link_index and current_session:
            selected_link = links_list.get(selected_link_index)
            new_url = simpledialog.askstring("Edit Link", "Enter new URL:", initialvalue=selected_link)
            if new_url:
                current_session.links[selected_link_index[0]] = new_url
                current_session.save()
                refresh_links_list()

    links_context_menu = Menu(ai_assistant_window, tearoff=0)

    def reverse_ingestion_from_vault(doc_path, vault_path):
        doc_name = os.path.basename(doc_path)
        marker = f"Document: {doc_name}"
        if safely_remove_content(vault_path, marker, "Document:"):
            print(f"Successfully removed document '{doc_name}' from the vault.")
        else:
            print(f"Failed to remove document '{doc_name}' from the vault.")

    def ingest_documents():
        global current_session
        if current_session:
            print(f"Ingesting documents for session {current_session.id}...")
            vault_path = os.path.join("data", "conversations", current_session.id, "vault.md")

            # Initialize RAG for this session
            rag = current_session.rag

            for idx, doc_data in enumerate(current_session.documents):
                doc_path = doc_data.get('path', '')
                is_checked = doc_data.get('checked', False)

                if doc_path and is_checked:
                    doc_name = os.path.basename(doc_path)
                    marker = f"Document: {doc_name}"

                    extracted_text = process_pdf_to_text(doc_path)
                    if extracted_text:
                        print(f"Extracted text for {doc_name}: {extracted_text[:100]}...")
                        if safely_add_content(vault_path, marker, extracted_text):
                            print(f"Successfully ingested document: {doc_name}")
                            # Update embeddings for this document
                            if rag.update_embeddings(doc_name):
                                print(f"Successfully updated embeddings for: {doc_name}")
                            else:
                                print(f"Failed to update embeddings for: {doc_name}")
                        else:
                            print(f"Failed to ingest document: {doc_name}")

                elif doc_path and not is_checked:
                    reverse_ingestion_from_vault(doc_path, vault_path)
                    # Rebuild all embeddings after removal
                    if current_session.rag.update_embeddings():
                        print("Successfully updated embeddings after document removal")
                    else:
                        print("Failed to update embeddings after document removal")

    def show_links_context_menu(event):
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
                links_context_menu.add_command(
                    label="Add New Link", command=add_new_link
                )
            else:
                links_context_menu.add_command(
                    label="Add New Link", command=add_new_link
                )
        links_context_menu.post(event.x_root, event.y_root)

    links_list.bind("<Button-3>", show_links_context_menu)
    refresh_links_list()
    Separator(session_list_frame, orient="horizontal").pack(fill="x", pady=5)

    # Documents List
    Label(session_list_frame, text="DOCUMENTS", font=("Helvetica", 10, "bold")).pack(fill="x")
    documents_frame = Frame(session_list_frame)
    documents_frame.pack(fill="both", expand=True)
    document_paths = []
    document_checkbuttons = []

    # Function to change the button's appearance on hover
    def on_button_enter(e):
        ingest_button.config(background='#2E86C1', foreground='white', relief=RAISED)

    # Function to revert the button's appearance when the mouse leaves
    def on_button_leave(e):
        ingest_button.config(background='SystemButtonFace', foreground='black', relief=FLAT)

    # Create a frame for the ingest button at the bottom
    ingest_frame = Frame(session_list_frame)
    ingest_frame.pack(side="bottom", fill="x")

    # INGEST Button (Restored)
    # Button to ingest documents
    ingest_button = Button(ai_assistant_window, text="INGEST", command=ingest_documents)

    # Bind hover events to the button
    ingest_button.bind("<Enter>", on_button_enter)  # Mouse enters the button area
    ingest_button.bind("<Leave>", on_button_leave)  # Mouse leaves the button area

    ingest_button.pack(side="top")

    def refresh_documents_list():
        for widget in documents_frame.winfo_children():
            widget.destroy()

        # Create a canvas inside the documents_frame to allow scrolling
        documents_canvas = Canvas(documents_frame)
        documents_scrollbar = Scrollbar(documents_frame, orient="vertical", command=documents_canvas.yview)
        documents_canvas.configure(yscrollcommand=documents_scrollbar.set)

        documents_container = Frame(documents_canvas)  # Frame inside the canvas to hold the document checkbuttons
        documents_canvas.create_window((0, 0), window=documents_container, anchor="nw")

        # Pack the canvas and scrollbar
        documents_canvas.pack(side="left", fill="both", expand=True)
        documents_scrollbar.pack(side="right", fill="y")

        if current_session:
            for idx, doc_data in enumerate(current_session.documents):
                doc_path = doc_data.get('path', '')
                is_checked = doc_data.get('checked', False)
                if doc_path:
                    doc_name = os.path.basename(doc_path)
                    var = IntVar(value=int(is_checked))
                    checkbutton = Checkbutton(documents_container, text=doc_name, variable=var,
                                              command=lambda idx=idx, v=var: on_document_checkbox_change(idx, v))
                    checkbutton.pack(anchor="w")
                    checkbutton.bind("<Button-3>",
                                     lambda event, idx=idx, doc_name=doc_name: on_document_right_click(event, idx,
                                                                                                       doc_name))

        # Update scrollregion after adding all widgets
        documents_container.update_idletasks()  # Force the system to recalculate layout sizes
        documents_canvas.config(scrollregion=documents_canvas.bbox("all"))

        # Bind mousewheel scrolling to the canvas
        documents_canvas.bind_all("<MouseWheel>",
                                  lambda event: documents_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))

        # Bind right-click to show context menu when right-clicking on empty space in the document container
        documents_canvas.bind("<Button-3>", show_documents_context_menu_empty_space)

    def on_document_checkbox_change(document_index, var):
        is_checked = bool(var.get())
        current_session.update_document_checkbox(document_index, is_checked)

    def show_documents_context_menu_empty_space(event):
        documents_context_menu.delete(0, END)
        documents_context_menu.add_command(label="Add New Document", command=add_new_document)
        documents_context_menu.post(event.x_root, event.y_root)

    def on_document_right_click(event, document_index, doc_name):
        print(
            f"Right-clicked on document: {doc_name} (index {document_index})")  # Console print for right-click on a document

        # Configure context menu for document items (show 'Remove Document' and 'Add New Document')
        documents_context_menu.delete(0, END)
        documents_context_menu.add_command(label="Remove Document", command=lambda: remove_document(document_index))
        documents_context_menu.add_command(label="Add New Document", command=add_new_document)
        documents_context_menu.post(event.x_root, event.y_root)

    def remove_document(document_index):
        if current_session:
            current_session.documents.pop(document_index)
            current_session.save()
            refresh_documents_list()

    # Load supported file formats from JSON
    def load_file_formats(json_file='data/file_formats.json'):
        with open(json_file, 'r') as file:
            data = json.load(file)
        return data['text_file_formats']

    # Check if a format is supported
    def is_supported_format(file_extension, supported_formats):
        return file_extension in supported_formats

    def add_new_document():
        # Load supported formats (this can be done once globally if needed)
        supported_formats = load_file_formats()

        # Open file dialog for selecting files
        file_paths = filedialog.askopenfilenames(
            initialdir=".",
            title="Select documents",
            filetypes=[("All supported files", "*.*")] + [(ext[1:].upper() + " files", f"*{ext}") for ext in
                                                          supported_formats]
        )

        if file_paths and current_session:
            duplicates = []
            unsupported = []
            new_files = []

            for file_path in file_paths:
                file_extension = os.path.splitext(file_path)[1]

                if not is_supported_format(file_extension, supported_formats):
                    unsupported.append(os.path.basename(file_path))
                    continue

                if any(doc['path'] == file_path for doc in current_session.documents):
                    duplicates.append(os.path.basename(file_path))
                else:
                    new_files.append(file_path)
                    current_session.add_document(file_path)

            if unsupported:
                unsupported_list = "\n".join(unsupported)
                messagebox.showerror("Unsupported File Formats",
                                     f"The following files are unsupported:\n\n{unsupported_list}")

            if duplicates:
                duplicate_list = "\n".join(duplicates)
                messagebox.showerror("Duplicate Files",
                                     f"The following files are already in the document list:\n\n{duplicate_list}")

            if new_files:
                refresh_documents_list()

            if duplicates and not new_files and not unsupported:
                messagebox.showinfo("No New Files", "No new files were added to the document list.")

    def show_documents_context_menu(event):
        # Configure context menu for empty space (show only 'Add New Document')
        documents_context_menu.delete(0, END)
        documents_context_menu.add_command(label="Add New Document", command=add_new_document)
        documents_context_menu.post(event.x_root, event.y_root)

    documents_frame.bind("<Button-3>", show_documents_context_menu_empty_space)
    # Initialize the context menu
    documents_context_menu = Menu(ai_assistant_window, tearoff=0)

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
        global original_md_content
        original_md_content = script_text.get("1.0", END)
        if markdown_render_enabled:
            update_html_content()

    def update_html_content():
        global rendered_html_content
        rendered_html_content = markdown.markdown(original_md_content)
        html_display.set_html(rendered_html_content)

    def update_html_content_thread():
        global rendered_html_content
        rendered_html_content = markdown.markdown(original_md_content)
        html_display.set_html(rendered_html_content)

    def toggle_render_markdown(is_checked):
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

    def stream_output(process, history_manager):
        global current_session, original_md_content
        ai_response_buffer = ""
        try:
            while True:
                char = process.stdout.read(1)
                if char:
                    ai_response_buffer += char
                    # Do not insert char into output_text here
                elif process.poll() is not None:
                    break

            # After the AI response is fully received
            if ai_response_buffer:
                # Extract content between <output> and </output> tags or use the entire response
                output_content = extract_output_content(ai_response_buffer)

                # Add AI's response to history
                history_manager.add_message("ai", output_content)

                # Add message to current session
                current_session.add_message("ai", output_content)

                # Update UI
                output_text.insert(END, f"AI: {output_content}\n", "ai")
                append_to_vault(f"AI: {output_content}")
                original_md_content += f"\nAI: {output_content}\n"

                # Add TTS here
                if tts_enabled_var.get():
                    tts_manager.say(output_content)

        except Exception as e:
            output_text.insert(END, f"Error: {e}\n", "error")
        finally:
            on_processing_complete()

    def extract_output_content(text):
        """Extract only the content within <output> tags, or return the entire message if tags are absent."""
        output_pattern = r'<output>(.*?)</output>'
        matches = re.findall(output_pattern, text, re.DOTALL)
        if matches:
            return '\n'.join(matches).strip()
        else:
            # If no <output> tags are found, return the entire message
            return text.strip()

    def append_to_vault(content):
        if current_session:
            vault_path = os.path.join("data", "conversations", current_session.id, "vault.md")
            with open(vault_path, "a", encoding="utf-8") as vault_file:
                vault_file.write(content + "\n")
            print(f"Appended AI output to vault for session {current_session.id}.")

    def on_processing_complete():
        load_selected_agent()
        entry.config(state="normal")
        status_label_var.set("READY")

    def store_selected_agent(selected_agent):
        with open("data/agent_config.json", "w") as config_file:
            json.dump({"selected_agent": selected_agent}, config_file)

    def load_selected_agent():
        try:
            with open("data/config.json", "r") as config_file:
                config_data = json.load(config_file)
                return config_data.get("selected_agent", selected_agent_var)
        except FileNotFoundError:
            pass

    class OptimizedHistoryManager:
        def __init__(self, max_tokens: int = 4000, similarity_threshold: float = 0.85):
            self.history: List[Dict] = []
            self.message_hashes: Dict[str, datetime] = {}
            self.max_tokens = max_tokens
            self.similarity_threshold = similarity_threshold
            self.token_count = 0

        def _calculate_hash(self, content: str) -> str:
            """Generate a hash for message content"""
            return hashlib.md5(content.encode()).hexdigest()

        def _estimate_tokens(self, text: str) -> int:
            """Estimate token count (rough approximation)"""
            return len(text.split()) * 1.3  # Rough estimate: words * 1.3

        def _is_similar(self, text1: str, text2: str) -> bool:
            """Check if two texts are similar using sequence matcher"""
            return SequenceMatcher(None, text1, text2).ratio() > self.similarity_threshold

        def _extract_output_content(self, message: str) -> str:
            """Extract only the content within <output> tags, or return the entire message if tags are absent."""
            output_pattern = r'<output>(.*?)</output>'
            matches = re.findall(output_pattern, message, re.DOTALL)
            if matches:
                return '\n'.join(matches).strip()
            else:
                # If no <output> tags are found, return the entire message
                return message.strip()

        def _compress_similar_messages(self) -> None:
            """Compress similar consecutive messages"""
            if len(self.history) < 2:
                return

            i = 0
            while i < len(self.history) - 1:
                current = self.history[i]
                next_msg = self.history[i + 1]

                if (current['role'] == next_msg['role'] and
                        self._is_similar(current['content'], next_msg['content'])):
                    # Keep the more recent message
                    self.token_count -= self._estimate_tokens(current['content'])
                    self.history.pop(i)
                else:
                    i += 1

        def add_message(self, role: str, content: str) -> None:
            """Add a message to history with deduplication and compression"""
            # Extract content from output tags if present
            processed_content = self._extract_output_content(content)

            # Calculate hash of processed content
            content_hash = self._calculate_hash(processed_content)

            # Check for exact duplicates
            if content_hash in self.message_hashes:
                # Update timestamp only if it's a duplicate
                self.message_hashes[content_hash] = datetime.now()
                return

            # Add new message
            self.message_hashes[content_hash] = datetime.now()
            estimated_tokens = self._estimate_tokens(processed_content)

            # Add to history
            self.history.append({
                'role': role,
                'content': processed_content,
                'timestamp': datetime.now(),
                'token_estimate': estimated_tokens
            })

            self.token_count += estimated_tokens

            # Compress similar messages
            self._compress_similar_messages()

            # Trim history if exceeding token limit
            self._trim_history()

            print(f"Added message to history: Role: {role}, Content: {content}")

        def _trim_history(self) -> None:
            """Trim history to keep only the last 3 messages."""
            while len(self.history) > 3:
                removed_msg = self.history.pop(0)
                self.token_count -= removed_msg['token_estimate']
                # Remove from hash tracking
                content_hash = self._calculate_hash(removed_msg['content'])
                self.message_hashes.pop(content_hash, None)

        def get_history(self, max_tokens: Optional[int] = None) -> str:
            """Get optimized conversation history limited to the last 3 messages."""
            if not self.history:
                return ""

            # Only consider the last 3 messages
            last_messages = self.history[-3:]
            history_messages = [
                f"{msg['role'].title()}: {msg['content']}" for msg in last_messages
            ]

            return "\n".join(history_messages)

    def build_command_with_context(script_content: str,
                                   ai_command: str,
                                   relevant_docs: List[Dict],
                                   history_manager: OptimizedHistoryManager) -> str:
        """Build command with optimized context and history"""
        parts = []

        if script_content:
            parts.append(script_content)

        # Add the user's current input
        parts.append(f"User: {ai_command}")

        # Get optimized history (limited to last 3 messages)
        history = history_manager.get_history()
        if history:
            parts.append("\nPrevious conversation (last 3 messages):\n" + history)

        # Add relevant documents
        if relevant_docs:
            context_text = "\nRelevant context:\n" + "\n---\n".join(
                f"{doc['content']}" for doc in relevant_docs
            )
            parts.append(context_text)

        return "\n".join(parts)

    def get_script_content(opened_script_var, selected_text_var):
        """Extract script content based on selection or full script"""
        if selected_text_var.get():
            try:
                return (
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
                return ""
        elif opened_script_var.get():
            return "```\n" + script_text.get("1.0", END) + "```\n\n"
        return ""

    def update_ui_display(ai_command):
        """Update the UI with the user's command"""
        global original_md_content
        # Display the user's input in the UI
        output_text.insert("end", f"You: {ai_command}\n", "user")
        output_text.insert("end", "-" * 80 + "\n")
        # Append to vault and update original markdown content
        append_to_vault(f"USER: {ai_command}")
        original_md_content += f"\n{ai_command}\n"
        original_md_content += "-" * 80 + "\n"

    def execute_ai_assistant_command(opened_script_var, selected_text_var, ai_command):
        global original_md_content, selected_agent_var, current_session

        if not current_session:
            create_session()

        # Ensure current_session is initialized before accessing its history_manager
        history_manager = current_session.history_manager

        if ai_command.strip():
            # Get script content and relevant docs
            script_content = get_script_content(opened_script_var, selected_text_var)
            relevant_docs = current_session.get_relevant_context(ai_command)

            # Combine command with context
            combined_command = build_command_with_context(
                script_content,
                ai_command,
                relevant_docs,
                history_manager
            )

            # Add user's input to history
            history_manager.add_message("user", ai_command)

            # Add the user's message to the current session
            current_session.add_message("user", ai_command)

            # Update UI
            update_ui_display(ai_command)

            # Append relevant context if available
            if relevant_docs:
                context_text = "\n\nRelevant context:\n" + "\n---\n".join(
                    f"{doc['content']}" for doc in relevant_docs
                )
                combined_command += context_text

            # Update UI with the combined command (optional)
            # update_ui_display(combined_command)

            entry.delete(0, END)
            entry.config(state="disabled")
            status_label_var.set("AI is thinking...")

            # Prepare the command for processing by the AI assistant
            ai_script_path = "src/models/ai_assistant.py"
            if persistent_agent_selection_var.get():
                selected_agent = selected_agent_var
                store_selected_agent(selected_agent)
            else:
                selected_agent_var = "Assistant"
                selected_agent = selected_agent_var

            command = create_ai_command(ai_script_path, combined_command, selected_agent)
            process_ai_command(command)
        else:
            entry.config(state="normal")

    def create_ai_command(ai_script_path, user_prompt, agent_name=None):
        if platform.system() == "Windows":
            python_executable = os.path.join("venv", "Scripts", "python")
        else:
            python_executable = os.path.join("venv", "bin", "python3")
        if agent_name:
            return [python_executable, ai_script_path, user_prompt, agent_name]
        else:
            return [python_executable, ai_script_path, user_prompt]

    def process_ai_command(command):
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
            threading.Thread(
                target=stream_output,
                args=(process, current_session.history_manager)
            ).start()
        except Exception as e:
            output_text.insert(END, f"Error: {e}\n")
            on_processing_complete()
        finally:
            update_html_content()
            status_label_var.set(f"{selected_agent_var} is thinking")

    def read_ai_command(command_name, user_prompt):
        commands_file = "data/commands.json"
        try:
            with open(commands_file, "r", encoding="utf-8") as f:
                commands_data = json.load(f)

            def find_command(commands, command_name):
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
        selected_text = output_text.get("sel.first", "sel.last")
        if selected_text.strip():
            fix_user_prompt = read_ai_command(command, selected_text)
            execute_ai_assistant_command(
                add_current_main_opened_script_var,
                add_current_selected_text_var,
                fix_user_prompt,
            )

    def nlp_custom():
        selected_text = output_text.get("sel.first", "sel.last")
        if selected_text.strip():
            print(read_ai_command("code-optimize", selected_text))

    def show_context_menu(event):
        commands_file = "data/commands.json"

        def load_commands():
            try:
                with open(commands_file, "r", encoding="utf-8") as f:  # Specify UTF-8 encoding
                    commands_data = json.load(f)
                return commands_data.get("customCommands", [])  # Use get to avoid KeyError
            except (FileNotFoundError, json.JSONDecodeError) as e:
                messagebox.showerror("Error", f"Failed to load commands: {e}")
                return []
            except UnicodeDecodeError as e:
                messagebox.showerror("Error", f"Encoding error: {e}")
                return []

        def add_commands_to_menu(menu, commands):
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
        custom_commands = load_commands()
        add_commands_to_menu(context_menu, custom_commands)
        context_menu.add_separator()
        context_menu.add_command(label="Custom AI request", command=nlp_custom)
        context_menu.post(event.x_root, event.y_root)
        context_menu.focus_set()

        def destroy_menu():
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
        def __init__(self, session_id, load_existing=True):
            self.id = session_id
            self.name = ""
            self.file_path = os.path.join("data", "conversations", self.id, f"session_{self.id}.json")
            self.vault_path = os.path.join("data", "conversations", self.id, "vault.md")
            self.messages = []
            self.links = []
            self.documents = []
            self.rag = VaultRAG(self.id)  # Initialize the RAG system for this session
            self.state = "NOT_INGESTED"  # Initial state for vault
            self.chat_history = []
            self.history_manager = OptimizedHistoryManager()
            if load_existing and os.path.exists(self.file_path):
                self.load()
            else:
                self.name = f"Session {self.id}"
                self.save()

        def get_relevant_context(self, query_text, max_results=3):
            try:
                # Get similar documents from RAG
                results = self.query_rag(query_text)

                # Load and format the relevant content
                relevant_docs = []
                seen_content = set()  # To avoid duplicate content

                for doc_id, score in results:
                    if len(relevant_docs) >= max_results:
                        break

                    content = self.get_document_content(doc_id)
                    if content and content not in seen_content:
                        # Format the content to be more readable
                        formatted_content = self.format_document_content(content)
                        if formatted_content:
                            relevant_docs.append({
                                'doc_id': doc_id,
                                'content': formatted_content,
                                'similarity': score
                            })
                            seen_content.add(content)

                return relevant_docs

            except Exception as e:
                print(f"ERROR: Failed to get relevant context: {str(e)}")
                return []

        def get_document_content(self, doc_id):
            try:
                # If it's a vault chunk, read from vault file
                if doc_id.startswith('vault_content_'):
                    with open(self.vault_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # Find the specific chunk
                    chunks = self.rag.chunk_content(content)
                    chunk_num = int(doc_id.split('_')[-1])
                    if chunk_num < len(chunks):
                        return chunks[chunk_num]

                # If it's a regular document
                elif doc_id.startswith('Document: '):
                    doc_path = doc_id.replace('Document: ', '')
                    if os.path.exists(doc_path):
                        with open(doc_path, 'r', encoding='utf-8') as f:
                            return f.read()

                # If it's a link
                elif doc_id.startswith('Link: '):
                    # Return the stored content for the link
                    return self.get_link_content(doc_id)

            except Exception as e:
                print(f"ERROR: Failed to get document content: {str(e)}")
            return None

        def format_document_content(self, content):
            try:
                if not content:
                    return None

                # Remove excessive whitespace
                content = ' '.join(content.split())

                # Limit content length if too long
                max_length = 500
                if len(content) > max_length:
                    content = content[:max_length] + "..."

                # Clean up any markdown or code formatting
                content = content.replace('```', '')

                # Remove any system-specific formatting
                content = content.replace('\r', '').replace('\n\n\n', '\n\n')

                return content.strip()
            except Exception as e:
                print(f"ERROR: Failed to format content: {str(e)}")
                return None

        def add_message(self, role, content):
            # Create message object
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }

            # Add to messages list
            self.messages.append(message)

            # Add to chat history in format expected by AI models
            self.chat_history.append({
                "role": role,
                "content": content
            })

            # Keep chat history at a maximum of the last 3 messages
            self.chat_history = self.chat_history[-3:]

            self.save()

        def get_conversation_context(self):
            """
            Get formatted conversation history for AI context
            """
            formatted_history = ""
            for msg in self.chat_history:
                role = "You" if msg["role"] == "user" else "Assistant"
                formatted_history += f"{role}: {msg['content']}\n"
            return formatted_history

        def add_link(self, url):
            self.links.append(url)
            self.save()
            # Update embeddings for the new link
            current_session.rag.update_embeddings()  # Rebuild the embeddings with the updated content

        def load_file_formats(json_file='file_formats.json'):
            with open(json_file, 'r') as file:
                data = json.load(file)
            return data['text_file_formats']

        def process_txt_to_text(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()

        # You can define other process functions based on file format here
        def process_txt_to_text(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()

        def process_md_to_text(file_path):
            return process_txt_to_text(file_path)

        def process_latex_to_text(file_path):
            return process_txt_to_text(file_path)  # Simplified, LaTeX may need special handling

        def process_other_file_to_text(file_path):
            return process_txt_to_text(file_path)  # For other plain text files

        def add_document(self, document_path):
            self.documents.append({"path": document_path, "checked": False})
            self.save()

            # Load supported file formats from JSON
            supported_formats = load_file_formats()

            # Get file extension
            file_extension = os.path.splitext(document_path)[1].lower()

            # Ingest document content based on its format
            extracted_text = None
            try:
                if file_extension == '.pdf':
                    extracted_text = process_pdf_to_text(document_path)  # Handle PDF separately
                    try:
                        extracted_text = process_pdf_to_text(document_path)  # Assume we have this function
                        embedding = self.rag.model.encode([extracted_text], convert_to_numpy=True)
                        if embedding is not None:
                            self.rag.store_embedding(f"Document: {os.path.basename(document_path)}", embedding)
                    except Exception as e:
                        print(f"ERROR: Error processing document or updating embeddings: {e}")

                '''elif file_extension == '.txt':
                    extracted_text = process_txt_to_text(document_path)
                elif file_extension == '.md':
                    extracted_text = process_md_to_text(document_path)
                elif file_extension in ['.tex', '.latex', '.ltx', '.sty']:
                    extracted_text = process_latex_to_text(document_path)
                else:
                    # Handle other text-based formats dynamically from JSON
                    if file_extension in supported_formats:
                        extracted_text = process_other_file_to_text(document_path)
                    else:
                        raise ValueError(f"Unsupported file type: {file_extension}")'''

            except Exception as e:
                # Handle error, file format unsupported or processing failed
                print(f"Error processing file {document_path}: {e}")
                # return  # Optionally return or handle further
                raise ValueError(f"Unsupported file type: {file_extension}")

            # If text extraction was successful, proceed
            if extracted_text:
                embedding = generate_embedding(extracted_text)
                if embedding:
                    self.rag.store_embedding(f"Document: {os.path.basename(document_path)}", embedding)
                # Add content to the vault safely
                if safely_add_content(self.vault_path, f"Document: {os.path.basename(document_path)}", extracted_text):
                    # Update the embeddings with the new document content
                    self.rag.update_embeddings()

        def update_document_checkbox(self, document_index, checked):
            self.documents[document_index]["checked"] = checked
            self.save()

        def query_rag(self, query_text):
            try:
                print(f"INFO: Querying with question: {query_text}")

                # Generate embedding for the query text
                query_embedding = self.rag.model.encode([query_text], convert_to_numpy=True)

                # Search for similar documents using the embedding
                results = self.rag.query(query_embedding)

                print(f"Query: {query_text}")
                print(f"Relevant Docs: {results}")

                return results

            except Exception as e:
                import traceback
                print(f"ERROR: Error in RAG query: {str(e)}")
                traceback.print_exc()
                return []

        def save(self):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            data = {
                "session_id": self.id,
                "session_name": self.name,
                "links": self.links,
                "documents": self.documents,
                "messages": self.messages,
                "chat_history": self.chat_history,  # Save chat history
                "vault_state": self.state
            }
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        def load(self):
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.name = data.get("session_name", f"Session {self.id}")
                self.messages = data.get("messages", [])
                self.links = data.get("links", [])
                self.documents = data.get("documents", [])
                self.chat_history = data.get("chat_history", [])  # Load chat history
                self.state = data.get("vault_state", "NOT_INGESTED")
            # Initialize history manager with existing messages
            self.history_manager = OptimizedHistoryManager()
            for msg in self.chat_history:
                self.history_manager.add_message(msg["role"], msg["content"])

        def update_vault(self, content, increment=True):
            if increment:
                with open(self.vault_path, "a", encoding="utf-8") as vault_file:
                    vault_file.write(content + "\n")
                self.state = "INCREMENTED"  # Update the state to INCREMENTED
            else:
                with open(self.vault_path, "w", encoding="utf-8") as vault_file:
                    vault_file.write("")  # Clear the vault
                self.state = "DECREMENTED"  # Update the state to DECREMENTED
            self.save()

    def reset_vault():
        global current_session
        if current_session:
            current_session.update_vault("", increment=False)
            print(f"Vault cleared for session {current_session.id}.")

    def read_vault(self):
        if os.path.exists(self.vault_path):
            with open(self.vault_path, "r", encoding="utf-8") as vault_file:
                return vault_file.read()
        return ""

    def create_session():
        global current_session, session_data
        new_session_id = datetime.now().strftime("%Y%m%d%H%M%S")
        current_session = Session(new_session_id, load_existing=False)
        session_data.append(current_session)
        update_sessions_list()
        select_session(len(session_data) - 1)

    def update_chat_display():
        output_text.delete("1.0", END)
        if current_session:
            for message in current_session.messages:
                role_tag = "user" if message["role"] == "user" else "ai"
                output_text.insert(
                    END, f"{message['role']}: {message['content']}\n", role_tag
                )
        output_text.see(END)

    def load_session(session_id):
        global current_session
        for session in session_data:
            if session.id == session_id:
                current_session = session
                current_session.load()
                break
        update_chat_display()
        refresh_links_list()
        refresh_documents_list()

    def select_session(index):
        global current_session, history_manager
        sessions_list.selection_clear(0, END)
        sessions_list.selection_set(index)
        sessions_list.activate(index)
        sessions_list.see(index)
        current_session = session_data[index]
        current_session.load()
        history_manager = current_session.history_manager
        update_chat_display()
        refresh_links_list()
        refresh_documents_list()
        write_config_parameter("options.network_settings.last_selected_session_id", index + 1)

    def update_sessions_list():
        sessions_list.delete(0, END)
        for session in session_data:
            sessions_list.insert(END, session.name)

    def load_sessions(session_listbox):
        # TODO:
        sessions_path = os.path.join("data", "conversations")
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
        global session_data, current_session
        sessions_path = os.path.join("data", "conversations")
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
        selected_indices = sessions_list.curselection()
        if selected_indices:
            index = selected_indices[0]
            load_session(session_data[index].id)

    def show_session_context_menu(event, session_index):
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
        print(f"Saving session {session_index}...")
        session = session_data[session_index]
        with open(f"session_{session['id']}.txt", "w") as f:
            f.write(session["content"])
            messagebox.showinfo(
                "Delete Session", f"Session {session['id']} deleted successfully."
            )

    def rename_session(session_index):
        session = session_data[session_index]
        new_name = simpledialog.askstring(
            "Rename Session", "Enter new session name:", initialvalue=session.name
        )
        if new_name:
            session.name = new_name
            session.save()
            update_sessions_list()

    def archive_session(session_index):
        print(f"Archiving session {session_index}...")
        messagebox.showinfo(
            "Archive Session",
            f"Session {session_data[session_index]['id']} archived successfully.",
        )

    def delete_session(session_index):
        global current_session, session_data

        try:
            # Get the session to delete
            session = session_data[session_index]
            session_folder = os.path.join("data", "conversations", session.id)

            # Remove from session_data first
            session_data.pop(session_index)

            # Delete the folder and its contents
            if os.path.exists(session_folder):
                shutil.rmtree(session_folder)

            # Update the UI
            update_sessions_list()

            # If we deleted the current session, select a new one
            if current_session and current_session.id == session.id:
                if session_data:
                    # Select the last session if available
                    select_session(len(session_data) - 1)
                else:
                    # Create a new session if none left
                    create_session()

            messagebox.showinfo(
                "Delete Session",
                f"Session '{session.name}' deleted successfully."
            )

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to delete session: {str(e)}"
            )

    def handle_session_click(event):
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

    def on_ai_assistant_window_close():
        # Stop the TTS manager thread
        tts_manager.queue.put(None)  # Send None to signal the thread to exit
        ai_assistant_window.destroy()

    ai_assistant_window.protocol("WM_DELETE_WINDOW", on_ai_assistant_window_close)

