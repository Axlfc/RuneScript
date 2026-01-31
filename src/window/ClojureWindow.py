import os
import re
import subprocess
import time
import shutil
import json
import threading
import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox, simpledialog
from src.ui.themed_window import ThemedWindow
import queue

class ClojureKeywords:
    KEYWORDS = ["def", "defn", "defn-", "defmacro", "defmethod", "defmulti", "defprotocol",
                "defrecord", "deftype", "fn", "if", "when", "let", "do", "loop", "recur",
                "cond", "condp", "case", "and", "or", "not", "ns", "require", "use", "import",
                "refer", "try", "catch", "finally", "throw", "with-open", "for", "doseq",
                "dotimes", "while", "map", "reduce", "filter", "some", "concat", "lazy-seq",
                "thread-last", "->", "->>"]
    CORE_FUNCTIONS = ["range", "vector", "list", "hash-map", "hash-set", "seq", "first", "rest",
                      "last", "cons", "conj", "assoc", "dissoc", "get", "nth", "take", "drop",
                      "repeat", "iterate", "partition", "apply", "partial", "comp", "constantly",
                      "identity", "juxt", "every?", "not-any?", "str", "keyword", "symbol",
                      "gensym", "println", "pr", "prn", "print", "flush", "atom", "swap!", "reset!"]

class ClojureWindow(ThemedWindow):
    def __init__(self, parent=None):
        if parent is None:
            try:
                from src.views.tk_utils import root
                parent = root
            except ImportError:
                pass
        super().__init__(parent)
        self.window = self
        self.title("Clojure IDE")
        self.geometry("1200x800")

        self.repl_process = None
        self.repl_queue = queue.Queue()
        self.history = []
        self.history_index = 0
        self.current_file = None

        self.setup_ui()
        self.process_repl_queue()
        self.start_clojure_repl()

    def setup_ui(self):
        self.paned = ctk.CTkFrame(self)
        self.paned.pack(fill="both", expand=True)

        # Left: Project Tree
        self.left_pane = ctk.CTkFrame(self.paned, width=200)
        self.left_pane.pack(side="left", fill="y", padx=5, pady=5)

        ctk.CTkLabel(self.left_pane, text="Project", font=("Arial", 12, "bold")).pack(pady=5)
        self.project_tree = ttk.Treeview(self.left_pane)
        self.project_tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Center: Editor
        self.center_pane = ctk.CTkFrame(self.paned)
        self.center_pane.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.editor = ctk.CTkTextbox(self.center_pane, font=("Consolas", 12))
        self.editor.pack(fill="both", expand=True, padx=5, pady=5)

        # Bottom: REPL
        self.bottom_pane = ctk.CTkFrame(self)
        self.bottom_pane.pack(fill="x", side="bottom", padx=5, pady=5)

        self.repl_output = ctk.CTkTextbox(self.bottom_pane, height=150)
        self.repl_output.pack(fill="x", padx=5, pady=2)

        self.repl_input = ctk.CTkEntry(self.bottom_pane, placeholder_text="Enter Clojure code...")
        self.repl_input.pack(fill="x", padx=5, pady=2)
        self.repl_input.bind("<Return>", self.send_to_repl)

        self.setup_menu()

    def setup_menu(self):
        menubar = tk.Menu(self)
        self.configure(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_file)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)

        run_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Run", menu=run_menu)
        run_menu.add_command(label="Evaluate Buffer", command=self.evaluate_buffer)

    def evaluate_buffer(self):
        code = self.editor.get("1.0", "end").strip()
        if code:
            self.send_to_repl_code(code)

    def send_to_repl(self, event=None):
        code = self.repl_input.get()
        if code:
            self.send_to_repl_code(code)
            self.repl_input.delete(0, "end")

    def send_to_repl_code(self, code):
        if self.repl_process and self.repl_process.stdin:
            try:
                self.repl_process.stdin.write(code + "\n")
                self.repl_process.stdin.flush()
            except Exception as e:
                self.repl_output.insert("end", f"Error: {e}\n")
        else:
            self.repl_output.insert("end", "REPL not running.\n")

    def start_clojure_repl(self):
        try:
            self.repl_process = subprocess.Popen(
                ["lein", "repl"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                shell=True
            )
            threading.Thread(target=self.read_repl_output, daemon=True).start()
        except Exception as e:
            self.repl_output.insert("end", f"Failed to start REPL: {e}\n")

    def read_repl_output(self):
        if not self.repl_process: return
        for line in self.repl_process.stdout:
            self.repl_queue.put(line)

    def process_repl_queue(self):
        try:
            while True:
                line = self.repl_queue.get_nowait()
                self.repl_output.insert("end", line)
                self.repl_output.see("end")
        except queue.Empty:
            pass
        self.after(100, self.process_repl_queue)

    def new_file(self):
        self.editor.delete("1.0", "end")
        self.current_file = None

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("Clojure files", "*.clj"), ("All files", "*.*")])
        if path:
            with open(path, 'r', encoding='utf-8') as f:
                self.editor.delete("1.0", "end")
                self.editor.insert("1.0", f.read())
            self.current_file = path

    def save_file(self):
        if not self.current_file:
            self.current_file = filedialog.asksaveasfilename(defaultextension=".clj")
        if self.current_file:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(self.editor.get("1.0", "end"))

    def _on_close(self):
        if self.repl_process:
            self.repl_process.terminate()
        super()._on_close()
