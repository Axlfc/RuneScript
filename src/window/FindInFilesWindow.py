import os
import re
import threading
import fnmatch
import tkinter as tk
import customtkinter as ctk
from src.utils.thread_manager import thread_manager
from tkinter import (
    BooleanVar, tk.END, filedialog, StringVar
)
from tkinter.ttk import Treeview
from src.ui.themed_window import ThemedWindow


class FindInFilesWindow(ThemedWindow):
    def __init__(self, parent=None):
        """Initialize the Find in Files window"""
        if parent is None:
            try:
                from src.views.tk_utils import root
                parent = root
            except ImportError:
                pass
        super().__init__(parent)
        self.find_window = self # self is the window
        self.title("Find in Files")
        self.geometry("800x600")

        # Make the window modal
        self.transient(parent)
        self.grab_set()

        # Configure grid weights for resizing
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Setup UI components
        self.setup_ui()

    def setup_ui(self):
        # Input frame
        input_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        # Search input
        ctk.CTkLabel(input_frame, text="Search:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.search_entry = ctk.CTkEntry(input_frame, width=300)
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Case sensitivity option
        self.case_sensitive_var = tk.BooleanVar()
        ctk.CTkCheckBox(input_frame, text="Case Sensitive", variable=self.case_sensitive_var).grid(row=0, column=2,
                                                                                                    padx=5)

        # Path input
        ctk.CTkLabel(input_frame, text="Path:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.path_entry = ctk.CTkEntry(input_frame, width=300)
        self.path_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.path_entry.insert(0, os.getcwd())

        # Browse button
        ctk.CTkButton(input_frame, text="Browse", width=80, command=self.browse_directory).grid(row=1, column=2, padx=5, pady=5)

        # Filter input
        ctk.CTkLabel(input_frame, text="Filter:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.filter_entry = ctk.CTkEntry(input_frame, width=300)
        self.filter_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        self.filter_entry.insert(0, "*.py")

        # Include subdirectories option
        self.include_subdirs_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(input_frame, text="Include Subdirectories", variable=self.include_subdirs_var).grid(row=2,
                                                                                                             column=2,
                                                                                                             padx=5)

        # Button frame
        button_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        # Find and Cancel buttons
        ctk.CTkButton(button_frame, text="Find", width=100, command=self.start_search).pack(side=tk.RIGHT, padx=5)
        ctk.CTkButton(button_frame, text="Cancel", width=100, command=self.destroy).pack(side=tk.RIGHT, padx=5)

        # Results frame with Treeview
        self.results_frame = ctk.CTkFrame(self.main_container)
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Set up Treeview for results display
        self.setup_results_tree()

        # Progress label
        self.progress_var = tk.StringVar(value="Ready")
        self.progress_label = ctk.CTkLabel(self.main_container, textvariable=self.progress_var)
        self.progress_label.pack(fill=tk.X, pady=5)

    def setup_results_tree(self):
        columns = ("File", "Line", "Text")
        self.results_tree = Treeview(self.results_frame, columns=columns, show="headings")

        # Configure columns
        self.results_tree.heading("File", text="File")
        self.results_tree.heading("Line", text="Line")
        self.results_tree.heading("Text", text="Text")

        self.results_tree.column("File", width=250)
        self.results_tree.column("Line", width=60)
        self.results_tree.column("Text", width=400)

        # Add scrollbars
        vsb = ctk.CTkScrollbar(self.results_frame, orientation="vertical", command=self.results_tree.yview)
        hsb = ctk.CTkScrollbar(self.results_frame, orientation="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid scrollbars and treeview
        self.results_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Configure frame grid weights
        self.results_frame.grid_columnconfigure(0, weight=1)
        self.results_frame.grid_rowconfigure(0, weight=1)

        # Double-click event to open file at line
        self.results_tree.bind("<Double-1>", self.on_double_click)

    def browse_directory(self):
        directory = filedialog.askdirectory(initialdir=self.path_entry.get())
        if directory:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, directory)

    def start_search(self):
        """Start the search in a separate thread"""
        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        task_id = "search_in_files"
        thread_manager.update_status_bar("Searching in files...", show_progress=True, show_cancel=True, task_id=task_id)
        thread_manager.run_in_thread(self.search_worker, task_id, on_complete=lambda _: thread_manager.update_status_bar("Search complete"))

    def search_worker(self, stop_event):
        """Worker function to run the search in a separate thread"""
        search_text = self.search_entry.get()
        search_path = self.path_entry.get()
        file_filter = self.filter_entry.get()
        case_sensitive = self.case_sensitive_var.get()
        include_subdirs = self.include_subdirs_var.get()

        if not search_text or not search_path:
            self.progress_var.set("Please enter search text and path")
            return

        # Compile regex pattern
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            pattern = re.compile(re.escape(search_text), flags)
        except re.error:
            self.progress_var.set("Invalid search pattern")
            return

        # Collect files to search
        files_to_process = []
        try:
            for root, dirs, files in os.walk(search_path):
                if stop_event.is_set(): break
                dirs[:] = [d for d in dirs if d != "__pycache__" and not d.startswith(".")]
                for file in files:
                    if fnmatch.fnmatch(file, file_filter):
                        files_to_process.append(os.path.join(root, file))
                if not include_subdirs:
                    break
        except Exception as e:
            self.find_window.after(0, lambda: self.progress_var.set(f"Error: {str(e)}"))
            return

        if not files_to_process:
            self.find_window.after(0, lambda: self.progress_var.set("No matching files found"))
            return

        # Update progress
        self.find_window.after(0, lambda: self.progress_var.set(f"Searching {len(files_to_process)} files..."))

        # Process files
        total_results = 0
        for i, filepath in enumerate(files_to_process):
            if stop_event.is_set(): break

            if i % 10 == 0: # Update progress every 10 files
                self.find_window.after(0, lambda idx=i: self.progress_var.set(f"Searching {idx}/{len(files_to_process)} files..."))

            results = self.search_file(filepath, pattern)
            if results:
                self.find_window.after(0, lambda res=results: self.update_results(res))
                total_results += len(results)

        self.find_window.after(0, lambda: self.progress_var.set(
            f"Found {total_results} matches in {len(files_to_process)} files" if not stop_event.is_set() else "Search cancelled"
        ))

    def search_file(self, filepath, pattern):
        """Search a single file for matches"""
        results = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as file:
                for line_num, line in enumerate(file, start=1):
                    if pattern.search(line):
                        results.append((filepath, line_num, line.strip()))
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
        return results

    def update_results(self, results):
        """Update results in the main thread"""
        if not self.find_window.winfo_exists(): return
        for filepath, line_num, line in results:
            try:
                rel_path = os.path.relpath(filepath, self.path_entry.get())
                self.results_tree.insert("", "end", values=(rel_path, line_num, line))
            except: pass

    def on_double_click(self, event):
        selection = self.results_tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.results_tree.item(item)["values"]
        if values:
            file_path, line_num, _ = values
            full_path = os.path.join(self.path_entry.get(), file_path)
            print(f"Opening {full_path} at line {line_num}")


