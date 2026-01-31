import os
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
import psutil
from src.ui.themed_window import ThemedWindow

class GraphicEngineWindow(ThemedWindow):
    def __init__(self, parent=None):
        if parent is None:
            try:
                from src.views.tk_utils import root
                parent = root
            except ImportError:
                pass
        super().__init__(parent)
        self.root = self
        self.title("Genesis AI Engine")
        self.geometry("1400x900")

        # State variables
        self.current_scene_path = None
        self.is_processing = False
        self._running = False
        self.physics_state = ctk.StringVar(value="Idle")
        self.memory_usage = ctk.StringVar(value="Memory Usage: 0%")
        self.last_command = ctk.StringVar(value="")

        self.setup_ui()
        self.start_monitoring()

    def setup_ui(self):
        # Top toolbar
        self.toolbar = ctk.CTkFrame(self, height=40)
        self.toolbar.pack(side="top", fill="x")

        ctk.CTkButton(self.toolbar, text="Play", width=60, command=self.play_scene).pack(side="left", padx=5)
        ctk.CTkButton(self.toolbar, text="Pause", width=60, command=self.pause_scene).pack(side="left", padx=5)
        ctk.CTkButton(self.toolbar, text="Stop", width=60, command=self.stop_scene).pack(side="left", padx=5)

        # Main horizontal split
        self.main_split = ctk.CTkFrame(self)
        self.main_split.pack(fill="both", expand=True)

        # Left: Hierarchy
        self.hierarchy_frame = ctk.CTkFrame(self.main_split, width=250)
        self.hierarchy_frame.pack(side="left", fill="y", padx=5, pady=5)
        ctk.CTkLabel(self.hierarchy_frame, text="Hierarchy", font=("Arial", 12, "bold")).pack(pady=5)
        self.hierarchy_tree = ttk.Treeview(self.hierarchy_frame)
        self.hierarchy_tree.pack(fill="both", expand=True)

        # Center: Main Workspace
        self.workspace = ctk.CTkFrame(self.main_split)
        self.workspace.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # Output Log
        self.output_text = ctk.CTkTextbox(self.workspace, height=200)
        self.output_text.pack(side="bottom", fill="x", padx=5, pady=5)

        # Right: AI Input & Inspector
        self.right_pane = ctk.CTkFrame(self.main_split, width=300)
        self.right_pane.pack(side="left", fill="y", padx=5, pady=5)

        ctk.CTkLabel(self.right_pane, text="AI Command", font=("Arial", 12, "bold")).pack(pady=5)
        self.prompt_input = ctk.CTkEntry(self.right_pane, placeholder_text="Ask AI to create something...")
        self.prompt_input.pack(fill="x", padx=10, pady=5)
        self.send_button = ctk.CTkButton(self.right_pane, text="Send", command=self.send_prompt)
        self.send_button.pack(pady=5)

        # Status Bar
        self.status_bar = ctk.CTkLabel(self, text="Ready", anchor="w")
        self.status_bar.pack(side="bottom", fill="x", padx=10)

    def send_prompt(self):
        prompt = self.prompt_input.get().strip()
        if prompt:
            self.log_message(f"User: {prompt}")
            self.prompt_input.delete(0, "end")
            # Logic to handle AI response would go here

    def log_message(self, message):
        self.output_text.insert("end", message + "\n")
        self.output_text.see("end")

    def play_scene(self): self.physics_state.set("Playing"); self.log_message("Playing...")
    def pause_scene(self): self.physics_state.set("Paused"); self.log_message("Paused.")
    def stop_scene(self): self.physics_state.set("Stopped"); self.log_message("Stopped.")

    def start_monitoring(self):
        self._running = True
        threading.Thread(target=self.monitor_resources, daemon=True).start()

    def monitor_resources(self):
        while self._running:
            mem = psutil.virtual_memory()
            usage = f"Memory Usage: {mem.percent}%"
            self.memory_usage.set(usage)
            status = f"State: {self.physics_state.get()} | {usage}"
            self.after(0, lambda s=status: self.status_bar.configure(text=s))
            time.sleep(2)

    def _on_close(self):
        self._running = False
        super()._on_close()
