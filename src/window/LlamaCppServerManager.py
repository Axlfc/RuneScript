
import io
import os
import signal
import subprocess
import time
from threading import Thread
from tkinter import (messagebox, Label, DoubleVar, Toplevel, Menu, Button, Entry, StringVar, BooleanVar,
                     Checkbutton, Text, Scrollbar, filedialog)
from tkinter.ttk import Progressbar, Combobox, Notebook, Treeview, LabelFrame, Frame
from datetime import datetime
import queue
import psutil
import requests
import multiprocessing
import sys

from src.controllers.parameters import write_config_parameter, read_config_parameter
from src.views.tk_utils import status_label_var, my_font
from src.controllers.message_queue import MessageQueue


class LlamaCppServerManager:
    DEFAULT_MODEL_DIR = os.path.join("src", "models", "model", "text")
    MODELS_INFO_URL = "https://huggingface.co/TheBloke/models-json/raw/main/models.json"

    def __init__(self, message_queue=None):
        """
        Initialize the Llama.cpp Server Manager

        Args:
            message_queue (MessageQueue, optional): Shared message queue for inter-window communication
        """
        # Use provided message queue or create a new one
        self.message_queue = message_queue or MessageQueue()

        # Server management variables
        self.server_process = None
        self.server_output_queue = multiprocessing.Queue()
        self.server_control_queue = multiprocessing.Queue()

        # UI Setup
        self.window = Toplevel()
        self.window.title("Llama.cpp Server Settings")
        self.window.geometry("800x600")

        # Close event handling
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        # Load saved settings
        self.port = read_config_parameter("options.llama_cpp.port")
        self.model_path = read_config_parameter("options.llama_cpp.model_path")
        self.available_models = []

        self.output_queue = multiprocessing.Queue()

        # Advanced settings with defaults
        self.settings = {
            "n_ctx": read_config_parameter("options.llama_cpp.n_ctx") or "512",
            "n_threads": read_config_parameter("options.llama_cpp.n_threads") or str(psutil.cpu_count(logical=False)),
            "n_batch": read_config_parameter("options.llama_cpp.n_batch") or "8",
            "n_gpu_layers": read_config_parameter("options.llama_cpp.n_gpu_layers") or "0",
        }

        # Create notebook for tabbed interface
        self.notebook = Notebook(self.window)
        self.notebook.pack(expand=True, fill="both", padx=5, pady=5)


        # Create tabs
        self.create_server_tab()
        self.create_models_tab()
        self.create_advanced_tab()
        self.create_monitoring_tab()

        # Start model and output processing
        self.scan_for_models()
        self.start_output_processing()

        # Check if we should autostart
        if read_config_parameter("options.llama_cpp.autostart") == "true":
            self.window.after(1000, self.autostart_server)

    def start_output_processing(self):
        """Start background threads for processing server output"""

        def process_server_output():
            """Continuously process server output"""
            while True:
                try:
                    # Non-blocking check for output
                    try:
                        message = self.server_output_queue.get_nowait()
                        self.handle_server_output(message)
                    except queue.Empty:
                        pass

                    # Check for control messages
                    try:
                        control_msg = self.server_control_queue.get_nowait()
                        self.handle_control_message(control_msg)
                    except queue.Empty:
                        pass

                    # Small sleep to prevent tight loop
                    time.sleep(0.1)
                except Exception as e:
                    print(f"Error in output processing: {e}")

        # Start output processing thread
        output_thread = Thread(target=process_server_output, daemon=True)
        output_thread.start()

    def handle_server_output(self, message):
        """
        Handle server output messages

        Args:
            message (dict): Message containing output details
        """
        # Update status text
        self.update_status(message.get('text', ''))

        # Update UI based on message type
        if message.get('type') == 'status':
            status = message.get('status', '')
            if status == 'starting':
                status_label_var.set("Starting Server")
                self.start_button.config(state="disabled")
            elif status == 'running':
                status_label_var.set("Server Running")
                self.start_button.config(state="disabled")
                self.stop_button.config(state="normal")
            elif status == 'stopped':
                status_label_var.set("Server Stopped")
                self.start_button.config(state="normal")
                self.stop_button.config(state="disabled")
            elif status == 'error':
                status_label_var.set("Server Error")

        # Optionally send message to global message queue
        self.message_queue.put({
            'source': 'llama_cpp_server',
            'type': 'output',
            **message
        })

    def handle_control_message(self, message):
        """
        Handle control messages from the server process

        Args:
            message (dict): Control message details
        """
        if message.get('action') == 'stop':
            self.stop_server()

    def safe_decode(self, input_data):
        """Safely decode bytes to string, handling any encoding issues."""
        if isinstance(input_data, str):
            return input_data  # Already a string
        try:
            return input_data.decode('utf-8')  # Try UTF-8 first
        except UnicodeDecodeError:
            try:
                return input_data.decode(sys.getdefaultencoding())  # Try system default encoding
            except UnicodeDecodeError:
                try:
                    return input_data.decode('latin-1')  # Fall back to latin-1
                except Exception:
                    return input_data.decode('utf-8', errors='replace')  # Last resort

    def process_output(self):
        """Process server output from the queue and update UI"""
        try:
            while True:
                message = self.output_queue.get_nowait()
                self.update_status(message)

                # Update status based on server messages
                if "loaded meta data" in message:
                    status_label_var.set("Loading Model")
                elif "llama_model_load: tensor" in message:
                    status_label_var.set("Loading Tensors")
                elif "llama server listening" in message:
                    status_label_var.set("Server Running")
                elif "error" in message.lower() and not message.startswith("ERROR: llama_model_loader:"):
                    status_label_var.set("Server Error")
        except queue.Empty:
            pass
        finally:
            # Schedule the next update
            self.window.after(100, self.process_output)

    def on_close(self):
        """Handles window close event, ensuring server stops if running."""
        if self.server_process:
            if messagebox.askyesno("Exit", "Server is still running. Do you want to stop it and exit?"):
                self.stop_server()
        self.window.destroy()

    def browse_model(self):
        """Open a file dialog to browse and select a model file."""
        model_file_path = filedialog.askopenfilename(
            initialdir=self.DEFAULT_MODEL_DIR,
            title="Select Model File",
            filetypes=[("GGUF files", "*.gguf"), ("All files", "*.*")]
        )
        if model_file_path:
            self.model_path_var.set(model_file_path)

    def create_server_tab(self):
        server_frame = Frame(self.notebook)
        self.notebook.add(server_frame, text="Server")

        # Model selection
        model_frame = LabelFrame(server_frame, text="Model Selection", padding=10)
        model_frame.pack(fill="x", padx=10, pady=5)

        self.model_path_var = StringVar(value=self.model_path)
        self.model_combo = Combobox(model_frame, textvariable=self.model_path_var)
        self.model_combo.pack(fill="x", pady=5)

        model_buttons = Frame(model_frame)
        model_buttons.pack(fill="x")
        Button(model_buttons, text="Browse", command=self.browse_model).pack(side="left", padx=5)
        Button(model_buttons, text="Refresh Models", command=self.scan_for_models).pack(side="left", padx=5)

        # Server settings
        settings_frame = LabelFrame(server_frame, text="Server Settings", padding=10)
        settings_frame.pack(fill="x", padx=10, pady=5)

        self.port_var = StringVar(value=self.port)
        Label(settings_frame, text="Port:").pack(anchor="w")
        port_entry = Entry(settings_frame, textvariable=self.port_var)
        port_entry.pack(fill="x")

        # Autostart checkbox
        self.autostart_var = BooleanVar(
            value=read_config_parameter("options.llama_cpp.autostart") == "true")
        Checkbutton(settings_frame, text="Autostart server", variable=self.autostart_var,
                        command=lambda: write_config_parameter("options.llama_cpp.autostart",
                                                               str(self.autostart_var.get()))
                        ).pack(anchor="w", pady=5)

        # Server control
        control_frame = Frame(server_frame, padding=10)
        control_frame.pack(fill="x", padx=10, pady=5)

        self.start_button = Button(control_frame, text="Start Server", command=self.start_server)
        self.start_button.pack(side="left", padx=5)

        self.stop_button = Button(control_frame, text="Stop Server", command=self.stop_server, state="disabled")
        self.stop_button.pack(side="left", padx=5)

        # Status display
        status_frame = LabelFrame(server_frame, text="Server Status", padding=10)
        status_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.status_text = Text(status_frame, height=8, wrap="word", font=my_font)
        status_scroll = Scrollbar(status_frame, orient="vertical", command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=status_scroll.set)

        self.status_text.pack(side="left", fill="both", expand=True)
        status_scroll.pack(side="right", fill="y")

    def create_models_tab(self):
        models_frame = Frame(self.notebook)
        self.notebook.add(models_frame, text="Download Models")

        # Search frame
        search_frame = Frame(models_frame)
        search_frame.pack(fill="x", padx=10, pady=5)

        self.search_var = StringVar()
        self.search_var.trace("w", self.filter_models)
        Entry(search_frame, textvariable=self.search_var).pack(side="left", fill="x", expand=True)
        Button(search_frame, text="Refresh List", command=self.fetch_models_list).pack(side="right", padx=5)

        # Models list
        list_frame = Frame(models_frame)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("name", "size", "type", "context")
        self.models_tree = Treeview(list_frame, columns=columns, show="headings")

        # Set column headings
        self.models_tree.heading("name", text="Model Name")
        self.models_tree.heading("size", text="Size")
        self.models_tree.heading("type", text="Type")
        self.models_tree.heading("context", text="Context")

        # Set column widths
        self.models_tree.column("name", width=200)
        self.models_tree.column("size", width=100)
        self.models_tree.column("type", width=100)
        self.models_tree.column("context", width=100)

        tree_scroll = Scrollbar(list_frame, orient="vertical", command=self.models_tree.yview)
        self.models_tree.configure(yscrollcommand=tree_scroll.set)

        self.models_tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        # Download button
        Button(models_frame, text="Download Selected Model", command=self.download_model).pack(pady=10)

        # Initial fetch of models list
        # self.fetch_models_list()

    def create_advanced_tab(self):
        advanced_frame = Frame(self.notebook)
        self.notebook.add(advanced_frame, text="Advanced")

        settings_frame = LabelFrame(advanced_frame, text="Advanced Settings", padding=10)
        settings_frame.pack(fill="x", padx=10, pady=5)

        # Context size
        Label(settings_frame, text="Context Size (n_ctx):").pack(anchor="w")
        self.n_ctx_var = StringVar(value=self.settings["n_ctx"])
        Entry(settings_frame, textvariable=self.n_ctx_var).pack(fill="x", pady=2)
        Label(settings_frame, text="Higher values use more memory but allow longer context", font=("", 8)).pack(
            anchor="w")

        # CPU Threads
        Label(settings_frame, text="CPU Threads:").pack(anchor="w", pady=(10, 0))
        self.n_threads_var = StringVar(value=self.settings["n_threads"])
        Entry(settings_frame, textvariable=self.n_threads_var).pack(fill="x", pady=2)
        Label(settings_frame, text=f"Recommended: {psutil.cpu_count(logical=False)} (physical cores)",
                  font=("", 8)).pack(anchor="w")

        # Batch size
        Label(settings_frame, text="Batch Size:").pack(anchor="w", pady=(10, 0))
        self.n_batch_var = StringVar(value=self.settings["n_batch"])
        Entry(settings_frame, textvariable=self.n_batch_var).pack(fill="x", pady=2)
        Label(settings_frame, text="Higher values may improve performance but use more memory", font=("", 8)).pack(
            anchor="w")

        # GPU Layers
        Label(settings_frame, text="GPU Layers:").pack(anchor="w", pady=(10, 0))
        self.n_gpu_layers_var = StringVar(value=self.settings["n_gpu_layers"])
        Entry(settings_frame, textvariable=self.n_gpu_layers_var).pack(fill="x", pady=2)
        Label(settings_frame, text="Number of layers to offload to GPU (0 for CPU-only)", font=("", 8)).pack(
            anchor="w")

        # Save button
        Button(advanced_frame, text="Save Settings", command=self.save_advanced_settings).pack(pady=10)

    def create_monitoring_tab(self):
        monitoring_frame = Frame(self.notebook)
        self.notebook.add(monitoring_frame, text="Monitoring")

        # Resource usage
        resources_frame = LabelFrame(monitoring_frame, text="Resource Usage", padding=10)
        resources_frame.pack(fill="x", padx=10, pady=5)

        # CPU Usage
        self.cpu_var = StringVar(value="CPU: 0%")
        Label(resources_frame, textvariable=self.cpu_var).pack(anchor="w")

        # Memory Usage
        self.memory_var = StringVar(value="Memory: 0 MB")
        Label(resources_frame, textvariable=self.memory_var).pack(anchor="w")

        # Server Statistics
        stats_frame = LabelFrame(monitoring_frame, text="Server Statistics", padding=10)
        stats_frame.pack(fill="x", padx=10, pady=5)

        self.requests_var = StringVar(value="Requests Processed: 0")
        Label(stats_frame, textvariable=self.requests_var).pack(anchor="w")

        self.uptime_var = StringVar(value="Uptime: 0:00:00")
        Label(stats_frame, textvariable=self.uptime_var).pack(anchor="w")

        # Start monitoring update loop
        self.update_monitoring()

    def scan_for_models(self):
        """Scan the default model directory for GGUF files"""
        self.available_models = []
        if os.path.exists(self.DEFAULT_MODEL_DIR):
            for file in os.listdir(self.DEFAULT_MODEL_DIR):
                if file.endswith(".gguf"):
                    full_path = os.path.join(self.DEFAULT_MODEL_DIR, file)
                    self.available_models.append(full_path)

        self.model_combo["values"] = self.available_models
        if self.available_models and not self.model_path_var.get():
            self.model_path_var.set(self.available_models[0])

    def fetch_models_list(self):
        """Fetch available models from HuggingFace"""
        try:
            response = requests.get(self.MODELS_INFO_URL)
            response.raise_for_status()  # Raise an error for HTTP errors

            # Try parsing JSON
            try:
                models = response.json()
            except ValueError:
                messagebox.showerror("Error", "Failed to parse models list. The response was not valid JSON.")
                return

            # Clear existing items in tree view
            for item in self.models_tree.get_children():
                self.models_tree.delete(item)

            # Add new items if they contain ".gguf"
            for model in models:
                if "gguf" in model["filename"]:
                    self.models_tree.insert("", "end", values=(
                        model["name"],
                        f"{model['size_mb']:.1f} MB",
                        model["type"],
                        model.get("context_length", "N/A")
                    ))
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Failed to fetch models list: {e}")

    def filter_models(self, *args):
        """Filter the models list based on search text"""
        search_term = self.search_var.get().lower()
        for item in self.models_tree.get_children():
            name = self.models_tree.item(item)["values"][0].lower()
            if search_term in name:
                self.models_tree.reattach(item, "", "end")
            else:
                self.models_tree.detach(item)

    def download_model(self):
        selection = self.models_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a model to download")
            return
    
        model_name = self.models_tree.item(selection[0])["values"][0]
        save_path = os.path.join(self.DEFAULT_MODEL_DIR, f"{model_name}.gguf")
    
        progress_window = Toplevel(self.window)
        progress_window.title("Downloading Model")
        progress_window.geometry("300x150")
    
        progress_var = DoubleVar()
        progress_bar = Progressbar(progress_window, length=200, mode='determinate', variable=progress_var)
        progress_bar.pack(pady=20, padx=10)
    
        status_label = Label(progress_window, text="Starting download...")
        status_label.pack(pady=10)
    
        def download_thread():
            try:
                url = f"https://huggingface.co/TheBloke/{model_name}/resolve/main/{model_name}.gguf"
                response = requests.get(url, stream=True)
                total_size = int(response.headers.get('content-length', 0))
                block_size = 1024  # 1 KB
                downloaded = 0
    
                with open(save_path, 'wb') as f:
                    for data in response.iter_content(block_size):
                        f.write(data)
                        downloaded += len(data)
                        progress = (downloaded / total_size) * 100
                        progress_var.set(progress)
                        status_label.config(
                            text=f"Downloaded: {downloaded // 1024 // 1024}MB / {total_size // 1024 // 1024}MB")
    
                self.scan_for_models()
                progress_window.destroy()
                messagebox.showinfo("Success", "Model downloaded successfully!")
    
            except Exception as e:
                messagebox.showerror("Error", f"Download failed: {str(e)}")
                progress_window.destroy()
    
        Thread(target=download_thread, daemon=True).start()
    
    def save_advanced_settings(self):
        """Save advanced settings to config"""
        settings = {
            "n_ctx": self.n_ctx_var.get(),
            "n_threads": self.n_threads_var.get(),
            "n_batch": self.n_batch_var.get(),
            "n_gpu_layers": self.n_gpu_layers_var.get()
        }
    
        for key, value in settings.items():
            write_config_parameter(f"options.llama_cpp.{key}", value)
    
        self.settings.update(settings)
        messagebox.showinfo("Success", "Settings saved successfully!")
    
    def update_monitoring(self):
        """Update monitoring information"""
        if self.server_process:
            try:
                process = psutil.Process(self.server_process.pid)
                cpu = process.cpu_percent()
                memory = process.memory_info().rss / 1024 / 1024  # MB
    
                self.cpu_var.set(f"CPU: {cpu:.1f}%")
                self.memory_var.set(f"Memory: {memory:.1f} MB")
    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.cpu_var.set("CPU: N/A")
                self.memory_var.set("Memory: N/A")
    
        self.window.after(1000, self.update_monitoring)
    
    def autostart_server(self):
        """Automatically start server if enabled"""
        if self.autostart_var.get() and self.model_path_var.get():
            self.start_server()

    def start_server(self):
        """
        Launch Llama.cpp server with robust path and environment handling
        """
        # Detect virtual environment Python interpreter
        venv_python = sys.executable  # Typically points to venv Python

        # Construct absolute paths
        model_path = os.path.abspath(self.model_path_var.get())

        # Validate model and port
        if not self.validate_server_start():
            return

        # Construct server launch command
        cmd = [
            venv_python,
            "-m", "llama_cpp.server",
            "--port", self.port_var.get(),
            "--model", model_path
        ]

        # Add optional parameters from advanced settings
        optional_params = {
            '--n_ctx': self.settings.get('n_ctx'),
            '--n_threads': self.settings.get('n_threads'),
            '--n_batch': self.settings.get('n_batch'),
            '--n_gpu_layers': self.settings.get('n_gpu_layers')
        }

        for param, value in optional_params.items():
            if value and value.strip():  # Ensure value is not empty or just whitespace
                cmd.extend([param, value])

        try:
            # Launch server process
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )

            # Update UI to reflect server status
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            status_label_var.set("Server Starting")

            # Start monitoring output
            self.monitor_output()

        except Exception as e:
            messagebox.showerror("Server Launch Error", f"Could not start server: {e}")
            self.update_status(f"Server launch failed: {e}")

    def validate_server_start(self):
        """
        Validate server start conditions

        Returns:
            bool: True if validation passes, False otherwise
        """
        if not self.model_path_var.get():
            messagebox.showerror("Error", "Please select a model file first.")
            return False

        if not os.path.exists(self.model_path_var.get()):
            messagebox.showerror("Error", "Selected model file does not exist.")
            return False

        port = self.port_var.get()
        if not port.isdigit():
            messagebox.showerror("Error", "Port must be a number.")
            return False

        # Save settings
        write_config_parameter("options.llama_cpp.port", port)
        write_config_parameter("options.llama_cpp.model_path", self.model_path_var.get())

        return True

    def monitor_process(self):
        """
        Monitor the overall server process lifecycle.
        """
        try:
            # Wait for process to complete
            return_code = self.server_process.wait()

            # Update UI to reflect server termination
            status_msg = f"Server stopped with return code: {return_code}"
            self.window.after(0, self.update_status, status_msg)
            self.window.after(0, self.update_server_buttons)

        except Exception as e:
            error_msg = f"Process monitoring error: {e}"
            self.window.after(0, self.update_status, error_msg)

    def update_server_buttons(self):
        """
        Reset the UI buttons after the server stops.
        """
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        status_label_var.set("Server Stopped")

    def monitor_output(self):
        """
        Continuously monitor server process output and update UI in real-time
        """
        def capture_output(pipe, output_type):
            """
            Capture and process output from server process

            Args:
                pipe (io.TextIOWrapper): Process pipe (stdout or stderr)
                output_type (str): Type of output stream ('stdout' or 'stderr')
            """
            try:
                for line in iter(pipe.readline, ''):
                    # Clean and process the line
                    cleaned_line = line.strip()
                    if cleaned_line:
                        # Update status text widget
                        self.window.after(0, self.update_status,
                                          f"[{output_type.upper()}] {cleaned_line}")

                        # Optional: Log to console for debugging
                        print(f"[Server {output_type}] {cleaned_line}")

                        # Optional: Send to message queue for broader application logging
                        self.message_queue.put({
                            'source': 'llama_cpp_server',
                            'type': output_type,
                            'message': cleaned_line
                        })
            except Exception as e:
                error_msg = f"Error capturing {output_type} output: {e}"
                self.window.after(0, self.update_status, error_msg)
                print(error_msg)
            finally:
                pipe.close()

        # Capture stdout and stderr in separate threads
        stdout_thread = Thread(
            target=capture_output,
            args=(self.server_process.stdout, 'stdout'),
            daemon=True
        )
        stderr_thread = Thread(
            target=capture_output,
            args=(self.server_process.stderr, 'stderr'),
            daemon=True
        )
        process_monitor_thread = Thread(
            target=self.monitor_process,
            daemon=True
        )

        # Start monitoring threads
        stdout_thread.start()
        stderr_thread.start()
        process_monitor_thread.start()



    def stop_server(self):
        """Stop the server process"""
        if self.server_process:
            try:
                # Send stop signal
                self.server_control_queue.put({'action': 'stop'})

                # Additional termination methods
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.server_process.pid)])
                else:
                    os.kill(self.server_process.pid, signal.SIGTERM)

                # Reset UI and state
                self.server_process = None
                self.start_button.config(state="normal")
                self.stop_button.config(state="disabled")
                status_label_var.set("Server Stopped")
                self.update_status("Server stopped")

            except Exception as e:
                self.update_status(f"Error stopping server: {str(e)}")

    def update_status(self, message):
        """
        Thread-safe method to update status text widget

        Args:
            message (str): Message to display in status widget
        """
        try:
            # Ensure UI updates happen on main thread
            self.window.after(0, self._insert_status_message, message)
        except Exception as e:
            print(f"Status update error: {e}")

    def _insert_status_message(self, message):
        """
        Internal method to insert message into text widget

        Args:
            message (str): Message to insert
        """
        try:
            # Insert message with timestamp
            timestamp = datetime.now().strftime("%H:%M:%S")
            full_message = f"[{timestamp}] {message}\n"

            self.status_text.insert("end", full_message)
            self.status_text.see("end")  # Auto-scroll to bottom
        except Exception as e:
            print(f"Message insertion error: {e}")
    

def create_llama_cpp_menu(menu_bar):
    """Create the Llama.cpp server menu"""
    run_menu = Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Run", menu=run_menu)
    run_menu.add_command(
        label="Llama.cpp Server Settings",
        command=lambda: LlamaCppServerManager()
    )
