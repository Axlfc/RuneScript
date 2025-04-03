import subprocess
import threading
import queue
from tkinter import Toplevel, Frame, Button, Scrollbar
from tkinter.ttk import Notebook
from tkinter.ttk import Treeview


class SystemInfoWindow(Toplevel):
    def __init__(self):
        super().__init__()
        self.title("System Information Viewer")
        self.geometry("800x600")

        self.notebook = Notebook(self)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        # Initialize commands dictionaries
        self._init_commands()

        # Create tabs
        self._create_tabs()

        # Add refresh button
        self.refresh_button = Button(self, text="Refresh All", command=self.refresh_all)
        self.refresh_button.pack(pady=10)

    def _init_commands(self):
        self.system_commands = {
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

        self.hardware_commands = {
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
            "Connected Monitors": "Get-CimInstance -Namespace root\\wmi -Class WmiMonitorID | ForEach-Object { $name = ($_.UserFriendlyName -notmatch 0 | ForEach-Object { [char]$_ }) -join ''; $name }",
            "Display Resolutions": "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::AllScreens | ForEach-Object { \"$($_.DeviceName): $($_.Bounds.Width)x$($_.Bounds.Height)\" }",
            "Battery Status": "Get-CimInstance Win32_Battery | Select-Object Name, EstimatedChargeRemaining, BatteryStatus | Format-Table -AutoSize",
        }

        self.network_commands = {
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

        self.software_commands = {
            "Installed Applications": "Get-ItemProperty @('HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*','HKLM:\\Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*') | Where-Object { $_.DisplayName } | Select-Object DisplayName, DisplayVersion, InstallDate | Sort-Object DisplayName | Format-Table -AutoSize",
            "Running Processes": "Get-Process | Select-Object ProcessName, Id, CPU, WorkingSet | Format-Table -AutoSize",
            "Startup Programs": "Get-CimInstance Win32_StartupCommand | Select-Object Name, Command, Location | Format-Table -AutoSize",
        }

        self.security_commands = {
            "User Accounts": "Get-LocalUser | Select-Object Name, Enabled | Format-Table -AutoSize",
            "Group Memberships": "Get-LocalGroupMember -Group 'Administrators' | Select-Object Name, ObjectClass | Format-Table -AutoSize",
            "Antivirus Software": "Get-CimInstance -Namespace 'root\\SecurityCenter2' -ClassName AntiVirusProduct | Select-Object displayName, productState | Format-Table -AutoSize",
            "Firewall Configuration": "Get-NetFirewallProfile | Select-Object Name, Enabled | Format-Table -AutoSize",
            "Disk Encryption Status": "Get-BitLockerVolume | Select-Object MountPoint, VolumeStatus | Format-Table -AutoSize",
        }

        self.development_commands = {
            "Version Control Systems": "Get-Command git, svn -ErrorAction SilentlyContinue | Select-Object Name, Version | Format-Table -AutoSize",
            "Programming Languages": "Get-Command python, java -ErrorAction SilentlyContinue | Select-Object Name, Version | Format-Table -AutoSize",
            "Environment Variables": "[Environment]::GetEnvironmentVariables() | Format-Table -AutoSize",
        }

        self.miscellaneous_commands = {
            "Locale and Language Settings": "Get-Culture | Select-Object Name, DisplayName",
            "Installed Fonts": "Get-ChildItem -Path $env:windir\\Fonts -Include *.ttf,*.otf -Recurse | Select-Object Name | Format-Table -AutoSize",
            "Recent Application Events": "Get-EventLog -LogName Application -Newest 10 | Format-Table -AutoSize",
        }

        self.user_commands = {
            "Home Directory Contents": "Get-ChildItem -Path $env:USERPROFILE | Select-Object Name | Format-Table -AutoSize",
            "Installed Browsers": "Get-ItemProperty 'HKLM:\\Software\\Clients\\StartMenuInternet\\*' | Select-Object '(default)' | Format-Table -AutoSize",
        }

    def _run_command(self, command, result_queue, label):
        try:
            powershell_path = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
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

    def _worker(self, commands, result_queue):
        for label, cmd in commands.items():
            self._run_command(cmd, result_queue, label)

    def _create_info_frame(self, parent, commands):
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
        thread = threading.Thread(target=self._worker, args=(commands, result_queue))
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

    def _create_tabs(self):
        tabs_config = [
            ("System", self.system_commands),
            ("Hardware", self.hardware_commands),
            ("Network", self.network_commands),
            ("Software", self.software_commands),
            ("Security", self.security_commands),
            ("Development", self.development_commands),
            ("Miscellaneous", self.miscellaneous_commands),
            ("User", self.user_commands),
        ]

        self.tabs = {}
        for tab_name, commands in tabs_config:
            tab = self._create_info_frame(self.notebook, commands)
            self.notebook.add(tab, text=tab_name)
            self.tabs[tab_name] = tab

    def refresh_all(self):
        for tab_name, tab in self.tabs.items():
            tree = tab.winfo_children()[0]
            tree.delete(*tree.get_children())

            commands = getattr(self, f"{tab_name.lower()}_commands")
            result_queue = queue.Queue()
            thread = threading.Thread(target=self._worker, args=(commands, result_queue))
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