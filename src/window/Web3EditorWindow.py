import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import customtkinter as ctk
import logging
import threading
import subprocess
import os
from src.ui.themed_window import ThemedWindow

class Web3DevStudio(ThemedWindow):
    def __init__(self, parent=None):
        if parent is None:
            try:
                from src.views.tk_utils import root
                parent = root
            except ImportError:
                pass
        super().__init__(parent)
        self.root = self
        self.title("Web3 Development Studio")
        self.geometry("1400x900")

        self.current_contract_path = None
        self.network_configs = {
            'Mainnet': {'rpc_url': '', 'chain_id': 1},
            'Goerli': {'rpc_url': '', 'chain_id': 5},
            'Sepolia': {'rpc_url': '', 'chain_id': 11155111}
        }

        self.setup_ui()

    def setup_ui(self):
        # Navigation Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200)
        self.sidebar.pack(side="left", fill="y", padx=5, pady=5)

        ctk.CTkLabel(self.sidebar, text="Web3 Studio", font=("Arial", 16, "bold")).pack(pady=20)

        ctk.CTkButton(self.sidebar, text="Editor", command=self.show_editor_view).pack(pady=5, padx=10, fill="x")
        ctk.CTkButton(self.sidebar, text="Testing", command=self.show_testing_view).pack(pady=5, padx=10, fill="x")
        ctk.CTkButton(self.sidebar, text="Deployment", command=self.show_deployment_view).pack(pady=5, padx=10, fill="x")
        ctk.CTkButton(self.sidebar, text="Settings", command=self.show_settings_view).pack(pady=5, padx=10, fill="x")

        # Main Workspace
        self.workspace = ctk.CTkFrame(self)
        self.workspace.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # Default view
        self.show_editor_view()

    def clear_workspace(self):
        for widget in self.workspace.winfo_children():
            widget.destroy()

    def show_editor_view(self):
        self.clear_workspace()

        editor_frame = ctk.CTkFrame(self.workspace)
        editor_frame.pack(fill="both", expand=True, padx=10, pady=10)

        btn_frame = ctk.CTkFrame(editor_frame)
        btn_frame.pack(fill="x", pady=5)

        ctk.CTkButton(btn_frame, text="New", width=80, command=self.create_new_contract).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Open", width=80, command=self.open_contract).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Save", width=80, command=self.save_contract).pack(side="left", padx=5)

        self.text_editor = ctk.CTkTextbox(editor_frame, font=("Consolas", 12))
        self.text_editor.pack(fill="both", expand=True, pady=5)

    def create_new_contract(self):
        name = simpledialog.askstring("New Contract", "Enter Contract Name:")
        if name:
            template = f"// SPDX-License-Identifier: MIT\npragma solidity ^0.8.0;\n\ncontract {name} {{\n    // Your code here\n}}"
            self.text_editor.delete("1.0", "end")
            self.text_editor.insert("1.0", template)

    def open_contract(self):
        path = filedialog.askopenfilename(filetypes=[("Solidity Files", "*.sol")])
        if path:
            with open(path, 'r') as f:
                self.text_editor.delete("1.0", "end")
                self.text_editor.insert("1.0", f.read())
            self.current_contract_path = path

    def save_contract(self):
        if not self.current_contract_path:
            self.current_contract_path = filedialog.asksaveasfilename(defaultextension=".sol")
        if self.current_contract_path:
            with open(self.current_contract_path, 'w') as f:
                f.write(self.text_editor.get("1.0", "end"))

    def show_testing_view(self):
        self.clear_workspace()
        ctk.CTkLabel(self.workspace, text="Testing Interface", font=("Arial", 14, "bold")).pack(pady=20)
        # Add testing UI elements

    def show_deployment_view(self):
        self.clear_workspace()
        ctk.CTkLabel(self.workspace, text="Deployment Interface", font=("Arial", 14, "bold")).pack(pady=20)
        # Add deployment UI elements

    def show_settings_view(self):
        self.clear_workspace()
        ctk.CTkLabel(self.workspace, text="Settings", font=("Arial", 14, "bold")).pack(pady=20)
        # Add settings UI elements
