import tkinter as tk
import customtkinter as ctk
import io
import os
import signal
import subprocess
import time
from threading import Thread
from datetime import datetime
import queue
import psutil
import sys
from src.ui.themed_window import ThemedWindow
from src.controllers.parameters import write_config_parameter, read_config_parameter
from src.views.tk_utils import status_label_var

class LlamaCppServerManager(ThemedWindow):
    def __init__(self, parent=None):
        if parent is None:
            try:
                from src.views.tk_utils import root
                parent = root
            except ImportError:
                pass
        super().__init__(parent)
        self.window = self
        self.title("Llama.cpp Server Manager")
        self.geometry("900x700")

        self.server_process = None
        self.message_queue = queue.Queue()
        self.server_control_queue = queue.Queue()

        self.setup_variables()
        self.setup_ui()
        self.update_monitoring()

    def setup_variables(self):
        self.port_var = ctk.StringVar(value=read_config_parameter("options.llama_cpp.port", "8000"))
        self.model_path_var = ctk.StringVar(value=read_config_parameter("options.llama_cpp.model_path", ""))
        self.autostart_var = ctk.BooleanVar(value=False)
        self.cpu_var = ctk.StringVar(value="CPU: N/A")
        self.memory_var = ctk.StringVar(value="Memory: N/A")

        self.n_ctx_var = ctk.StringVar(value="2048")
        self.n_threads_var = ctk.StringVar(value="4")
        self.n_batch_var = ctk.StringVar(value="512")
        self.n_gpu_layers_var = ctk.StringVar(value="0")

    def setup_ui(self):
        # Top Configuration
        config_frame = ctk.CTkFrame(self)
        config_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(config_frame, text="Model Path:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        ctk.CTkEntry(config_frame, textvariable=self.model_path_var, width=400).grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkButton(config_frame, text="Browse", width=80, command=self.browse_model).grid(row=0, column=2, padx=5, pady=5)

        ctk.CTkLabel(config_frame, text="Port:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        ctk.CTkEntry(config_frame, textvariable=self.port_var, width=100).grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Controls
        ctrl_frame = ctk.CTkFrame(self)
        ctrl_frame.pack(fill="x", padx=10, pady=5)

        self.start_button = ctk.CTkButton(ctrl_frame, text="Start Server", command=self.start_server)
        self.start_button.pack(side="left", padx=10, pady=10)

        self.stop_button = ctk.CTkButton(ctrl_frame, text="Stop Server", fg_color="red", state="disabled", command=self.stop_server)
        self.stop_button.pack(side="left", padx=10, pady=10)

        ctk.CTkLabel(ctrl_frame, textvariable=self.cpu_var).pack(side="right", padx=10)
        ctk.CTkLabel(ctrl_frame, textvariable=self.memory_var).pack(side="right", padx=10)

        # Log Area
        self.status_text = ctk.CTkTextbox(self, height=400)
        self.status_text.pack(fill="both", expand=True, padx=10, pady=10)

    def browse_model(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(filetypes=[("GGUF Models", "*.gguf")])
        if path:
            self.model_path_var.set(path)

    def start_server(self):
        if not self.model_path_var.get():
            from tkinter import messagebox
            messagebox.showerror("Error", "Please select a model")
            return

        cmd = [sys.executable, "-m", "llama_cpp.server", "--port", self.port_var.get(), "--model", self.model_path_var.get()]

        try:
            self.server_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.monitor_output()
        except Exception as e:
            self.update_status(f"Error: {e}")

    def stop_server(self):
        if self.server_process:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.server_process.pid)])
            else:
                self.server_process.terminate()
            self.server_process = None
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")

    def monitor_output(self):
        def capture(pipe, name):
            for line in iter(pipe.readline, ''):
                self.update_status(f"[{name}] {line.strip()}")
            pipe.close()

        if self.server_process:
            Thread(target=capture, args=(self.server_process.stdout, "OUT"), daemon=True).start()
            Thread(target=capture, args=(self.server_process.stderr, "ERR"), daemon=True).start()

    def update_monitoring(self):
        if self.server_process:
            try:
                proc = psutil.Process(self.server_process.pid)
                self.cpu_var.set(f"CPU: {proc.cpu_percent()}%")
                self.memory_var.set(f"Memory: {proc.memory_info().rss // 1024 // 1024}MB")
            except Exception:
                self.cpu_var.set("CPU: N/A")
                self.memory_var.set("Memory: N/A")
        self.after(2000, self.update_monitoring)

    def update_status(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.after(0, lambda: self.status_text.insert("end", f"[{timestamp}] {message}\n"))
        self.after(0, lambda: self.status_text.see("end"))

    def _on_close(self):
        self.stop_server()
        super()._on_close()
