import os
import re
import threading
from tkinter import (
    Toplevel, Label, Entry, Button, Checkbutton, BooleanVar, END, filedialog, StringVar,
    Frame, Scrollbar
)
from tkinter.ttk import Treeview


class FindInFilesWindow:
    def __init__(self):
        """Initialize the Find in Files window"""
        self.find_window = Toplevel()
        self.find_window.title("Find in Files")
        self.find_window.geometry("600x400")

        # Make the window modal
        self.find_window.transient()
        self.find_window.grab_set()

        # Configure grid weights for resizing
        self.find_window.grid_columnconfigure(1, weight=1)
        self.find_window.grid_rowconfigure(4, weight=1)

        # Setup UI components
        self.setup_ui()

    def setup_ui(self):
        # Search input
        Label(self.find_window, text="Search:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.search_entry = Entry(self.find_window, width=30)
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Case sensitivity option
        self.case_sensitive_var = BooleanVar()
        Checkbutton(self.find_window, text="Case Sensitive", variable=self.case_sensitive_var).grid(row=0, column=2,
                                                                                                    padx=5)

        # Path input
        Label(self.find_window, text="Path:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.path_entry = Entry(self.find_window, width=30)
        self.path_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.path_entry.insert(0, os.getcwd())

        # Browse button
        Button(self.find_window, text="Browse", command=self.browse_directory).grid(row=1, column=2, padx=5, pady=5)

        # Filter input
        Label(self.find_window, text="Filter:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.filter_entry = Entry(self.find_window, width=30)
        self.filter_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        self.filter_entry.insert(0, "*.py")

        # Include subdirectories option
        self.include_subdirs_var = BooleanVar(value=True)
        Checkbutton(self.find_window, text="Include Subdirectories", variable=self.include_subdirs_var).grid(row=2,
                                                                                                             column=2,
                                                                                                             padx=5)

        # Results frame with Treeview
        self.results_frame = Frame(self.find_window)
        self.results_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

        # Set up Treeview for results display
        self.setup_results_tree()

        # Progress label
        self.progress_var = StringVar(value="Ready")
        self.progress_label = Label(self.find_window, textvariable=self.progress_var)
        self.progress_label.grid(row=5, column=0, columnspan=3, pady=5)

        # Find and Cancel buttons
        Button(self.find_window, text="Find", command=self.start_search).grid(row=3, column=1, padx=5, pady=5,
                                                                              sticky="e")
        Button(self.find_window, text="Cancel", command=self.find_window.destroy).grid(row=3, column=2, padx=5, pady=5,
                                                                                       sticky="w")

    def setup_results_tree(self):
        columns = ("File", "Line", "Text")
        self.results_tree = Treeview(self.results_frame, columns=columns, show="headings")

        # Configure columns
        self.results_tree.heading("File", text="File")
        self.results_tree.heading("Line", text="Line")
        self.results_tree.heading("Text", text="Text")

        self.results_tree.column("File", width=200)
        self.results_tree.column("Line", width=60)
        self.results_tree.column("Text", width=300)

        # Add scrollbars
        vsb = Scrollbar(self.results_frame, orient="vertical", command=self.results_tree.yview)
        hsb = Scrollbar(self.results_frame, orient="horizontal", command=self.results_tree.xview)
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
            self.path_entry.delete(0, END)
            self.path_entry.insert(0, directory)

    def start_search(self):
        """Start the search in a separate thread"""
        threading.Thread(target=self.search_worker, daemon=True).start()

    def search_worker(self):
        """Worker function to run the search in a separate thread"""
        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

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

        # Convert wildcard pattern to regex
        file_pattern = re.compile(file_filter.replace(".", "\\.").replace("*", ".*"))

        # Collect files to search
        files_to_process = []
        for root, dirs, files in os.walk(search_path):
            dirs[:] = [d for d in dirs if d != "__pycache__" and not d.startswith(".")]
            for file in files:
                if file_pattern.match(file):
                    files_to_process.append(os.path.join(root, file))
            if not include_subdirs:
                break

        if not files_to_process:
            self.progress_var.set("No matching files found")
            return

        # Update progress
        self.progress_var.set(f"Searching {len(files_to_process)} files...")
        self.find_window.update_idletasks()

        # Process files in chunks
        total_results = 0
        for filepath in files_to_process:
            results = self.search_file(filepath, pattern)
            if results:
                self.update_results(results)
                total_results += len(results)

        self.progress_var.set(f"Found {total_results} matches in {len(files_to_process)} files")

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
        for filepath, line_num, line in results:
            rel_path = os.path.relpath(filepath, self.path_entry.get())
            self.results_tree.insert("", "end", values=(rel_path, line_num, line))
        self.find_window.update_idletasks()

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

