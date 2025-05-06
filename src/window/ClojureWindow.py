"""
Fixed version of the Clojure IDE with:
- Proper REPL communication
- Thread safety for UI updates
- Missing methods defined
- Better error handling
"""

import os
import re
import subprocess
import time
import shutil
import json
import threading
from tkinter import *
from tkinter import ttk, filedialog, messagebox, simpledialog
from tkinter.font import Font
from threading import Thread
import tkinter.scrolledtext as scrolledtext
from functools import partial
import webbrowser
import configparser
import pkg_resources
from pathlib import Path
import tempfile
import queue


class ClojureKeywords:
    """Common Clojure keywords for syntax highlighting"""
    KEYWORDS = [
        "def", "defn", "defn-", "defmacro", "defmethod", "defmulti", "defprotocol",
        "defrecord", "deftype", "fn", "if", "when", "let", "do", "loop", "recur",
        "cond", "condp", "case", "and", "or", "not", "ns", "require", "use", "import",
        "refer", "try", "catch", "finally", "throw", "with-open", "for", "doseq",
        "dotimes", "while", "map", "reduce", "filter", "some", "concat", "lazy-seq",
        "thread-last", "->", "->>"
    ]

    CORE_FUNCTIONS = [
        "range", "vector", "list", "hash-map", "hash-set", "seq", "first", "rest",
        "last", "cons", "conj", "assoc", "dissoc", "get", "nth", "take", "drop",
        "repeat", "iterate", "partition", "apply", "partial", "comp", "constantly",
        "identity", "juxt", "every?", "not-any?", "str", "keyword", "symbol",
        "gensym", "println", "pr", "prn", "print", "flush", "atom", "swap!", "reset!"
    ]


class AutoCompleteWindow:
    def __init__(self, editor, functions_list=None):
        self.editor = editor
        self.functions_list = functions_list or []
        self.listbox = None
        self.scrollbar = None
        self.toplevel = None
        self.current_prefix = ""
        self.matched_functions = []
        self.is_active = False

    def show(self, event=None):
        self.hide()  # Hide the current window if it exists

        try:
            # Get the current position
            index = self.editor.index(INSERT)
            line, col = map(int, index.split("."))

            # Get the current line text up to the cursor
            line_text = self.editor.get(f"{line}.0", f"{line}.{col}")

            # Find the last word being typed (potential prefix for autocomplete)
            match = re.search(r'[a-zA-Z0-9_\-\.]+$', line_text)
            if not match:
                return

            self.current_prefix = match.group(0)
            if len(self.current_prefix) < 2:  # Require at least 2 characters to show suggestions
                return

            # Find matching functions
            self.matched_functions = [fn for fn in self.functions_list if fn.startswith(self.current_prefix)]

            if not self.matched_functions:
                return

            # Calculate position for the popup
            bbox = self.editor.bbox(index)
            if not bbox:
                return

            x, y, _, h = bbox

            # Create popup window
            self.toplevel = Toplevel(self.editor)
            self.toplevel.wm_overrideredirect(True)

            # Position the window
            editor_x = self.editor.winfo_rootx() + x
            editor_y = self.editor.winfo_rooty() + y + h

            self.toplevel.geometry(f"+{editor_x}+{editor_y}")

            # Create listbox with scrollbar
            frame = Frame(self.toplevel, bd=1, relief=SOLID)
            frame.pack(fill=BOTH, expand=True)

            self.scrollbar = Scrollbar(frame)
            self.scrollbar.pack(side=RIGHT, fill=Y)

            self.listbox = Listbox(frame, width=50, height=min(10, len(self.matched_functions)),
                                   yscrollcommand=self.scrollbar.set)
            self.listbox.pack(side=LEFT, fill=BOTH)
            self.scrollbar.config(command=self.listbox.yview)

            # Populate listbox
            for func in self.matched_functions:
                self.listbox.insert(END, func)

            # Select first item
            self.listbox.selection_set(0)

            # Bind events
            self.listbox.bind("<Double-Button-1>", self._on_select)
            self.listbox.bind("<Return>", self._on_select)
            self.listbox.bind("<Escape>", lambda e: self.hide())

            self.is_active = True

        except Exception as e:
            print(f"Autocomplete error: {e}")

    def select_next(self):
        if not self.is_active or not self.listbox:
            return

        current = self.listbox.curselection()
        if current:
            next_index = current[0] + 1
            if next_index < self.listbox.size():
                self.listbox.selection_clear(0, END)
                self.listbox.selection_set(next_index)
                self.listbox.see(next_index)

    def select_previous(self):
        if not self.is_active or not self.listbox:
            return

        current = self.listbox.curselection()
        if current:
            prev_index = current[0] - 1
            if prev_index >= 0:
                self.listbox.selection_clear(0, END)
                self.listbox.selection_set(prev_index)
                self.listbox.see(prev_index)

    def _on_select(self, event=None):
        if not self.listbox:
            return

        selection = self.listbox.curselection()
        if selection:
            selected_function = self.matched_functions[selection[0]]

            # Remove the current prefix and insert the selected function
            cursor_pos = self.editor.index(INSERT)
            line, col = map(int, cursor_pos.split("."))
            start_pos = f"{line}.{col - len(self.current_prefix)}"

            self.editor.delete(start_pos, INSERT)
            self.editor.insert(INSERT, selected_function)

        self.hide()

    def hide(self):
        if self.toplevel:
            self.toplevel.destroy()
            self.toplevel = None
            self.listbox = None
            self.scrollbar = None
            self.is_active = False


class ClojureNamespace:
    def __init__(self):
        self.name = ""
        self.imports = []
        self.requires = []
        self.functions = []
        self.vars = []

    def parse_namespace(self, text):
        # Simple parser for detecting namespace elements
        self.name = ""
        self.imports = []
        self.requires = []
        self.functions = []
        self.vars = []

        # Find namespace declaration
        ns_match = re.search(r'\(ns\s+([^\s\)\(]+)', text)
        if ns_match:
            self.name = ns_match.group(1)

        # Find imports
        import_matches = re.finditer(r':import\s+\[([^\]]+)\]', text)
        for match in import_matches:
            import_text = match.group(1)
            # Extract Java imports
            imports = re.findall(r'([^\s\[\]]+)', import_text)
            self.imports.extend(imports)

        # Find requires
        require_matches = re.finditer(r':require\s+\[([^\]]+)\]', text)
        for match in require_matches:
            require_text = match.group(1)
            # Extract required namespaces
            requires = re.findall(r'([^\s\[\]]+)', require_text)
            self.requires.extend(requires)

        # Find function definitions
        fn_matches = re.finditer(r'\(defn\s+([^\s\)\(]+)', text)
        for match in fn_matches:
            self.functions.append(match.group(1))

        # Find var definitions
        var_matches = re.finditer(r'\(def\s+([^\s\)\(]+)', text)
        for match in var_matches:
            self.vars.append(match.group(1))

        return self.name

    def get_all_symbols(self):
        return self.functions + self.vars


class Project:
    def __init__(self, project_path=None):
        self.path = project_path
        self.name = os.path.basename(project_path) if project_path else ""
        self.namespaces = {}
        self.dependencies = []

    def load_project(self, path):
        self.path = path
        self.name = os.path.basename(path)
        self.namespaces = {}
        self.dependencies = []

        # Parse project.clj for dependencies
        project_file = os.path.join(path, "project.clj")
        if os.path.exists(project_file):
            with open(project_file, "r", encoding="utf-8") as f:
                content = f.read()
                # Simple regex to extract dependencies
                deps_match = re.search(r':dependencies\s+\[(.*?)\]', content, re.DOTALL)
                if deps_match:
                    deps_text = deps_match.group(1)
                    # Extract dependency vectors [group-id/artifact-id "version"]
                    dep_matches = re.finditer(r'\[([^\[\]]+?)\s+"([^"]+?)"\]', deps_text)
                    for match in dep_matches:
                        self.dependencies.append((match.group(1), match.group(2)))

        # Scan for Clojure files and parse namespaces
        src_dir = os.path.join(path, "src")
        if os.path.exists(src_dir):
            for root, _, files in os.walk(src_dir):
                for file in files:
                    if file.endswith(".clj"):
                        file_path = os.path.join(root, file)
                        self._parse_file_namespace(file_path)

    def _parse_file_namespace(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                namespace = ClojureNamespace()
                ns_name = namespace.parse_namespace(content)
                if ns_name:
                    self.namespaces[ns_name] = namespace
        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")

    def get_all_namespaces(self):
        return list(self.namespaces.keys())

    def get_all_functions(self):
        functions = []
        for ns in self.namespaces.values():
            for fn in ns.functions:
                functions.append(f"{ns.name}/{fn}")
        return functions


class ClojureHighlighter:
    def __init__(self, text_widget):
        self.text = text_widget

        # Configure tags for different syntax elements
        self.text.tag_configure("keyword", foreground="#C586C0")
        self.text.tag_configure("function", foreground="#DCDCAA")
        self.text.tag_configure("string", foreground="#CE9178")
        self.text.tag_configure("comment", foreground="#6A9955")
        self.text.tag_configure("paren", foreground="#D4D4D4")
        self.text.tag_configure("bracket", foreground="#D4D4D4")
        self.text.tag_configure("brace", foreground="#D4D4D4")
        self.text.tag_configure("number", foreground="#B5CEA8")

        # Configure rainbow paren tags
        self.rainbow_colors = ["#E06C75", "#61AFEF", "#98C379", "#C678DD", "#56B6C2", "#D19A66", "#E5C07B"]
        for i, color in enumerate(self.rainbow_colors):
            self.text.tag_configure(f"rainbow_{i}", foreground=color)

    def highlight_syntax(self, event=None):
        # Remove all tags
        for tag in self.text.tag_names():
            if tag not in ("sel", "insert"):
                self.text.tag_remove(tag, "1.0", "end")

        # Get all text
        content = self.text.get("1.0", "end-1c")

        # Highlight strings
        string_pattern = r'"(?:[^"\\]|\\.)*"'
        self._apply_regex_highlight(string_pattern, "string")

        # Highlight comments
        comment_pattern = r';.*$'
        self._apply_regex_highlight(comment_pattern, "comment", re.MULTILINE)

        # Highlight keywords
        for keyword in ClojureKeywords.KEYWORDS:
            self._highlight_word(keyword, "keyword")

        # Highlight core functions
        for func in ClojureKeywords.CORE_FUNCTIONS:
            self._highlight_word(func, "function")

        # Highlight numbers
        number_pattern = r'\b\d+(?:\.\d+)?\b'
        self._apply_regex_highlight(number_pattern, "number")

        # Highlight parentheses
        self._highlight_rainbow_parens()

    def _apply_regex_highlight(self, pattern, tag_name, flags=0):
        content = self.text.get("1.0", "end-1c")
        for match in re.finditer(pattern, content, flags):
            start_idx = match.start()
            end_idx = match.end()

            # Convert character position to line.column format
            start_line = content[:start_idx].count('\n') + 1
            start_col = start_idx - content[:start_idx].rfind('\n') - 1 if start_idx > 0 and '\n' in content[
                                                                                                     :start_idx] else start_idx

            end_line = content[:end_idx].count('\n') + 1
            end_col = end_idx - content[:end_idx].rfind('\n') - 1 if end_idx > 0 and '\n' in content[
                                                                                             :end_idx] else end_idx

            start_pos = f"{start_line}.{start_col}"
            end_pos = f"{end_line}.{end_col}"

            self.text.tag_add(tag_name, start_pos, end_pos)

    def _highlight_word(self, word, tag_name):
        content = self.text.get("1.0", "end-1c")
        pattern = r'\b' + re.escape(word) + r'\b'

        for match in re.finditer(pattern, content):
            start_idx = match.start()
            end_idx = match.end()

            # Convert character position to line.column format
            start_line = content[:start_idx].count('\n') + 1
            start_col = start_idx - content[:start_idx].rfind('\n') - 1 if start_idx > 0 and '\n' in content[
                                                                                                     :start_idx] else start_idx

            end_line = content[:end_idx].count('\n') + 1
            end_col = end_idx - content[:end_idx].rfind('\n') - 1 if end_idx > 0 and '\n' in content[
                                                                                             :end_idx] else end_idx

            start_pos = f"{start_line}.{start_col}"
            end_pos = f"{end_line}.{end_col}"

            self.text.tag_add(tag_name, start_pos, end_pos)

    def _highlight_rainbow_parens(self):
        content = self.text.get("1.0", "end-1c")
        paren_stack = []

        for i, char in enumerate(content):
            if char in '([{':
                depth = len(paren_stack) % len(self.rainbow_colors)
                paren_stack.append((i, depth))

                # Convert position to line.column format
                line = content[:i].count('\n') + 1
                col = i - content[:i].rfind('\n') - 1 if i > 0 and '\n' in content[:i] else i
                pos = f"{line}.{col}"

                self.text.tag_add(f"rainbow_{depth}", pos)

            elif char in ')]}':
                if paren_stack:
                    start_idx, depth = paren_stack.pop()

                    # Convert position to line.column format
                    line = content[:i].count('\n') + 1
                    col = i - content[:i].rfind('\n') - 1 if i > 0 and '\n' in content[:i] else i
                    pos = f"{line}.{col}"

                    self.text.tag_add(f"rainbow_{depth}", pos)


class LineNumberCanvas(Canvas):
    def __init__(self, parent, text_widget, **kwargs):
        super().__init__(parent, **kwargs)
        self.text_widget = text_widget
        self.textfont = None

        self.config(bd=0, highlightthickness=0)
        self.bind("<Configure>", self._on_configure)

    def _on_configure(self, event=None):
        self.redraw()

    def redraw(self):
        self.delete("all")  # Clear canvas

        i = self.text_widget.index("@0,0")
        while True:
            dline = self.text_widget.dlineinfo(i)
            if dline is None:
                break

            y = dline[1]
            linenum = str(i).split(".")[0]
            self.create_text(2, y, anchor="nw", text=linenum, font=self.textfont, fill="#858585")
            i = self.text_widget.index(f"{i}+1line")


class ClojureWindow:
    def __init__(self, master=None):
        # Single window approach: window and master are the same object
        if master is None:
            self.master = Tk()
        else:
            self.master = master

        self.window = self.master  # No Toplevel windows
        self.window.title("Clojure IDE")
        self.window.geometry("1200x800")

        self.config_dir = os.path.join(os.path.expanduser("~"), ".clojure_ide")
        os.makedirs(self.config_dir, exist_ok=True)

        self.current_file = None
        self.project = Project()
        self.repl_process = None
        self.repl_thread = None
        self.stop_repl_thread = False
        self.repl_queue = queue.Queue()  # Queue for thread-safe UI updates
        self.history = []
        self.history_index = -1
        self.paren_pairs = {')': '(', ']': '[', '}': '{'}

        self.setup_config()
        self.setup_ui()
        self.setup_bindings()
        self.load_functions_database()

        # Start the UI update timer
        self.window.after(100, self.process_repl_queue)

        if self.config.get('General', 'auto_start_repl', fallback='true').lower() == 'true':
            self.start_clojure_repl()

        self.recent_files = self.load_recent_files()
        self.update_recent_files_menu()

        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_config(self):
        self.config = configparser.ConfigParser()
        config_file = os.path.join(self.config_dir, "config.ini")

        # Default configuration
        if not os.path.exists(config_file):
            self.config['General'] = {
                'auto_start_repl': 'true',
                'font_family': 'Consolas',
                'font_size': '11',
                'theme': 'dark'
            }

            self.config['Editor'] = {
                'tab_size': '2',
                'auto_indent': 'true',
                'rainbow_parens': 'true',
                'highlight_current_line': 'true'
            }

            self.config['REPL'] = {
                'history_size': '1000',
                'startup_namespace': 'user'
            }

            with open(config_file, 'w') as f:
                self.config.write(f)
        else:
            self.config.read(config_file)

    def save_config(self):
        config_file = os.path.join(self.config_dir, "config.ini")
        with open(config_file, 'w') as f:
            self.config.write(f)

    def setup_theme(self):
        self.colors = {
            "editor_bg": "#1e1e1e",
            "editor_fg": "#d4d4d4",
            "cursor": "#ffffff",
            "repl_bg": "#1e1e1e",
            "repl_fg": "#d4d4d4",
            "console_bg": "#1e1e1e",
            "console_fg": "#d4d4d4",
            "test_bg": "#1e1e1e",
            "test_fg": "#d4d4d4",
        }

        style = ttk.Style(self.window)
        style.theme_use("clam")
        style.configure("TFrame", background=self.colors["editor_bg"])
        style.configure("TLabel", background=self.colors["editor_bg"], foreground=self.colors["editor_fg"])
        style.configure("TButton", background=self.colors["editor_bg"], foreground=self.colors["editor_fg"])
        style.configure("TNotebook", background=self.colors["editor_bg"])
        style.configure("TNotebook.Tab", background=self.colors["editor_bg"], foreground=self.colors["editor_fg"])
        style.configure("Treeview", background=self.colors["editor_bg"], foreground=self.colors["editor_fg"],
                        fieldbackground=self.colors["editor_bg"])
        style.configure("TEntry", fieldbackground=self.colors["editor_bg"], foreground=self.colors["editor_fg"])
        style.configure("TCombobox", fieldbackground=self.colors["editor_bg"], foreground=self.colors["editor_fg"])
        style.configure("TCheckbutton", background=self.colors["editor_bg"], foreground=self.colors["editor_fg"])
        style.configure("TRadiobutton", background=self.colors["editor_bg"], foreground=self.colors["editor_fg"])
        style.configure("TMenubutton", background=self.colors["editor_bg"], foreground=self.colors["editor_fg"])
        style.configure("TScrollbar", background=self.colors["editor_bg"], troughcolor=self.colors["editor_bg"])
        style.configure("TProgressbar", background=self.colors["editor_fg"], troughcolor=self.colors["editor_bg"])

    def setup_fonts(self):
        font_family = self.config.get('General', 'font_family', fallback='Consolas')
        font_size = self.config.getint('General', 'font_size', fallback=11)
        self.code_font = Font(family=font_family, size=font_size)

    def setup_bindings(self):
        self.editor.bind("<KeyRelease>", self.highlighter.highlight_syntax)
        self.editor.bind("<KeyRelease>", self.update_cursor_position)
        self.editor.bind("<ButtonRelease>", self.update_cursor_position)
        self.editor.bind("<KeyRelease>", self.handle_autocomplete)
        self.editor.bind("<Control-space>", self.autocomplete.show)
        self.editor.bind("<Control-n>", lambda e: self.autocomplete.select_next())
        self.editor.bind("<Control-p>", lambda e: self.autocomplete.select_previous())

        self.editor.bind("<MouseWheel>", lambda e: self.line_numbers.redraw())  # Windows
        self.editor.bind("<Button-4>", lambda e: self.line_numbers.redraw())  # Linux scroll up
        self.editor.bind("<Button-5>", lambda e: self.line_numbers.redraw())  # Linux scroll down

    def update_cursor_position(self, event=None):
        try:
            index = self.editor.index(INSERT)
            line, col = index.split(".")
            self.position_indicator.config(text=f"Línea {line}, Col {int(col) + 1}")
        except Exception:
            self.position_indicator.config(text="")

    def handle_autocomplete(self, event=None):
        if event and event.keysym in ("Up", "Down", "Return", "Escape"):
            return
        self.autocomplete.show()

    def setup_ui(self):
        self.setup_theme()
        self.setup_fonts()

        # Main frame
        self.main_frame = ttk.Frame(self.window)
        self.main_frame.pack(fill=BOTH, expand=True)

        # Create paned window for sidebar and content
        self.h_paned = ttk.PanedWindow(self.main_frame, orient=HORIZONTAL)
        self.h_paned.pack(fill=BOTH, expand=True)

        # Sidebar frame
        self.sidebar_frame = ttk.Frame(self.h_paned, width=200)
        self.h_paned.add(self.sidebar_frame, weight=1)

        # Setup notebook for project/docs
        self.sidebar_notebook = ttk.Notebook(self.sidebar_frame)
        self.sidebar_notebook.pack(fill=BOTH, expand=True)

        # Project browser tab
        self.project_frame = ttk.Frame(self.sidebar_notebook)
        self.sidebar_notebook.add(self.project_frame, text="Project")

        # Project toolbar
        project_toolbar = ttk.Frame(self.project_frame)
        project_toolbar.pack(fill=X)

        ttk.Button(project_toolbar, text="Open Project", command=self.open_project).pack(side=LEFT)
        ttk.Button(project_toolbar, text="Refresh", command=self.refresh_project).pack(side=LEFT)

        # Project treeview
        self.project_tree = ttk.Treeview(self.project_frame)
        self.project_tree.pack(fill=BOTH, expand=True)
        self.project_tree.bind("<Double-1>", self.on_tree_double_click)

        # Documentation tab
        self.docs_frame = ttk.Frame(self.sidebar_notebook)
        self.sidebar_notebook.add(self.docs_frame, text="Docs")

        # Search for docs
        ttk.Label(self.docs_frame, text="Search:").pack(anchor=W, padx=5, pady=5)
        self.docs_search = ttk.Entry(self.docs_frame)
        self.docs_search.pack(fill=X, padx=5)
        self.docs_search.bind("<Return>", self.search_docs)

        self.docs_results = ttk.Treeview(self.docs_frame, columns=("name", "namespace"))
        self.docs_results.heading("name", text="Name")
        self.docs_results.heading("namespace", text="Namespace")
        self.docs_results.column("#0", width=0, stretch=NO)
        self.docs_results.column("name", width=100)
        self.docs_results.column("namespace", width=100)
        self.docs_results.pack(fill=BOTH, expand=True, padx=5, pady=5)
        self.docs_results.bind("<Double-1>", self.show_doc_for_selected)

        # Content frame
        self.content_frame = ttk.Frame(self.h_paned)
        self.h_paned.add(self.content_frame, weight=4)

        # Create paned window for editor and REPL
        self.v_paned = ttk.PanedWindow(self.content_frame, orient=VERTICAL)
        self.v_paned.pack(fill=BOTH, expand=True)

        # Create editor frame with line numbers
        self.editor_frame = ttk.Frame(self.v_paned)
        self.v_paned.add(self.editor_frame, weight=3)

        # Line numbers and editor in a horizontal layout
        self.editor_h_frame = ttk.Frame(self.editor_frame)
        self.editor_h_frame.pack(fill=BOTH, expand=True)

        # Editor with scrollbars
        self.editor_scroll_frame = ttk.Frame(self.editor_h_frame)
        self.editor_scroll_frame.pack(side=LEFT, fill=BOTH, expand=True)

        self.editor = Text(self.editor_scroll_frame, wrap=NONE, font=self.code_font,
                           bg=self.colors["editor_bg"], fg=self.colors["editor_fg"],
                           insertbackground=self.colors["cursor"], undo=True,
                           padx=5, pady=5)

        # Line numbers canvas
        self.line_numbers = LineNumberCanvas(self.editor_h_frame, self.editor, width=30,
                                             bg=self.colors["editor_bg"], highlightthickness=0)
        self.line_numbers.textfont = self.code_font
        self.line_numbers.pack(side=LEFT, fill=Y)

        # Editor scrollbars
        self.editor_y_scroll = ttk.Scrollbar(self.editor_scroll_frame, orient=VERTICAL, command=self.editor.yview)
        self.editor_y_scroll.pack(side=RIGHT, fill=Y)

        self.editor_x_scroll = ttk.Scrollbar(self.editor_scroll_frame, orient=HORIZONTAL, command=self.editor.xview)
        self.editor_x_scroll.pack(side=BOTTOM, fill=X)

        def on_text_scroll(*args):
            self.editor_y_scroll.set(*args)
            self.line_numbers.redraw()

        self.editor.config(yscrollcommand=on_text_scroll, xscrollcommand=self.editor_x_scroll.set)
        self.editor_y_scroll.config(command=lambda *args: [self.editor.yview(*args), self.line_numbers.redraw()])
        self.editor.pack(side=LEFT, fill=BOTH, expand=True)

        # Set up syntax highlighter
        self.highlighter = ClojureHighlighter(self.editor)

        # Set up autocomplete
        self.autocomplete = AutoCompleteWindow(self.editor, ClojureKeywords.KEYWORDS + ClojureKeywords.CORE_FUNCTIONS)

        # Configure line number updating
        self.editor.bind("<<Modified>>", self._on_editor_modified)
        self.editor.bind("<KeyRelease>", self._on_editor_key_release)
        self.editor.bind("<ButtonRelease>", self._on_editor_mouse_release)

        # Create tabs for output sections
        self.output_notebook = ttk.Notebook(self.v_paned)
        self.v_paned.add(self.output_notebook, weight=1)

        # REPL tab
        self.repl_frame = ttk.Frame(self.output_notebook)
        self.output_notebook.add(self.repl_frame, text="REPL")

        self.repl_output = scrolledtext.ScrolledText(
            self.repl_frame,
            wrap=WORD,
            bg=self.colors["repl_bg"],
            fg=self.colors["repl_fg"],
            font=self.code_font
        )

        self.repl_output.pack(fill=BOTH, expand=True)

        self.repl_input = ttk.Entry(self.repl_frame, font=self.code_font)
        self.repl_input.pack(fill=X)
        self.repl_input.bind("<Return>", self.send_to_repl)
        self.repl_input.bind("<Up>", self.history_prev)
        self.repl_input.bind("<Down>", self.history_next)

        # Console tab
        self.console_frame = ttk.Frame(self.output_notebook)
        self.output_notebook.add(self.console_frame, text="Console")

        self.console_output = scrolledtext.ScrolledText(self.console_frame, wrap=WORD, bg=self.colors["console_bg"],
                                                        fg=self.colors["console_fg"], font=self.code_font)
        self.console_output.pack(fill=BOTH, expand=True)
        self.console_output.config(state=DISABLED)

        # Test output tab
        self.test_frame = ttk.Frame(self.output_notebook)
        self.output_notebook.add(self.test_frame, text="Tests")

        self.test_output = scrolledtext.ScrolledText(self.test_frame, wrap=WORD, bg=self.colors["test_bg"],
                                                     fg=self.colors["test_fg"], font=self.code_font)
        self.test_output.pack(fill=BOTH, expand=True)
        self.test_output.config(state=DISABLED)

        # Status bar
        self.status_frame = ttk.Frame(self.window)
        self.status_frame.pack(side=BOTTOM, fill=X)

        self.status_bar = ttk.Label(self.status_frame, text="Listo", relief=SUNKEN, anchor=W)
        self.status_bar.pack(side=LEFT, fill=X, expand=True)

        self.position_indicator = ttk.Label(self.status_frame, width=15, relief=SUNKEN)
        self.position_indicator.pack(side=RIGHT)

        # Set up menus
        self.setup_menu()

    def _on_editor_modified(self, event=None):
        self.editor.edit_modified(False)  # Reset the modified flag
        self.highlighter.highlight_syntax()
        self.line_numbers.redraw()

    def _on_editor_key_release(self, event=None):
        self.line_numbers.redraw()
        self.update_cursor_position()
        self.handle_autocomplete(event)

    def _on_editor_mouse_release(self, event=None):
        self.line_numbers.redraw()
        self.update_cursor_position()

    def show_about(self):
        messagebox.showinfo("Acerca de", "Clojure IDE en Tkinter\nDesarrollado con ❤️ por tu equipo.")

    def load_functions_database(self):
        if self.project:
            all_functions = self.project.get_all_functions()
            self.autocomplete.functions_list = (
                    ClojureKeywords.KEYWORDS +
                    ClojureKeywords.CORE_FUNCTIONS +
                    all_functions
            )

    def setup_menu(self):
        menu_bar = Menu(self.window)
        self.window.config(menu=menu_bar)

        # File menu
        self.file_menu = Menu(menu_bar, tearoff=0)
        self.file_menu.add_command(label="Nuevo", accelerator="Ctrl+N", command=self.new_file)
        self.file_menu.add_command(label="Abrir...", accelerator="Ctrl+O", command=self.open_file)
        self.file_menu.add_command(label="Guardar", accelerator="Ctrl+S", command=self.save_file)
        self.file_menu.add_command(label="Guardar como...", command=self.save_as)
        # Add recent files submenu
        self.recent_files_menu = Menu(self.file_menu, tearoff=0)
        self.file_menu.add_cascade(label="Recientes", menu=self.recent_files_menu)

        self.file_menu.add_separator()
        self.file_menu.add_command(label="Salir", command=self.on_close)
        menu_bar.add_cascade(label="Archivo", menu=self.file_menu)

        # Ejecutar menu
        self.run_menu = Menu(menu_bar, tearoff=0)
        self.run_menu.add_command(label="Evaluar selección", accelerator="Ctrl+E", command=self.evaluate_selection)
        self.run_menu.add_command(label="Evaluar buffer", command=self.evaluate_buffer)
        self.run_menu.add_command(label="Evaluar forma", command=self.evaluate_current_form)
        self.run_menu.add_separator()
        self.run_menu.add_command(label="Doc símbolo", command=self.clojure_doc_prompt)
        self.run_menu.add_command(label="Source símbolo", command=self.clojure_source_prompt)
        self.run_menu.add_separator()
        self.run_menu.add_command(label="Ejecutar tarea Leiningen...", command=self.run_lein_task)
        menu_bar.add_cascade(label="Ejecutar", menu=self.run_menu)

        # Ayuda menu
        self.help_menu = Menu(menu_bar, tearoff=0)
        self.help_menu.add_command(label="Acerca de", command=self.show_about)
        menu_bar.add_cascade(label="Ayuda", menu=self.help_menu)

    def update_status(self, message):
        self.status_bar.config(text=message)

    def update_repl(self, text):
        """Thread-safe update to the REPL output via queue"""
        self.repl_queue.put(text)

    def process_repl_queue(self):
        try:
            while True:
                message = self.repl_queue.get_nowait()
                self.repl_output.insert(END, message + "\n")
                self.repl_output.see(END)
        except queue.Empty:
            pass
        self.window.after(100, self.process_repl_queue)

    def start_clojure_repl(self):
        if self.repl_process:
            return
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
            self.repl_thread = threading.Thread(target=self.read_repl_output, daemon=True)
            self.repl_thread.start()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start Leiningen REPL: {e}")

    def read_repl_output(self):
        try:
            for line in self.repl_process.stdout:
                self.repl_queue.put(line.strip())
        except Exception as e:
            self.repl_queue.put(f"REPL error: {e}")

    def send_to_repl(self, event=None):
        code = self.repl_input.get()
        if self.repl_process and self.repl_process.stdin:
            try:
                self.repl_process.stdin.write(code + "\n")
                self.repl_process.stdin.flush()
                self.history.append(code)
                self.history_index = len(self.history)
                self.repl_input.delete(0, END)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to send code to REPL: {e}")
        else:
            messagebox.showwarning("Warning", "REPL is not running.")

    def history_prev(self, event=None):
        if self.history and self.history_index > 0:
            self.history_index -= 1
            self.repl_input.delete(0, END)
            self.repl_input.insert(0, self.history[self.history_index])

    def history_next(self, event=None):
        if self.history and self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.repl_input.delete(0, END)
            self.repl_input.insert(0, self.history[self.history_index])
        else:
            self.repl_input.delete(0, END)

    def on_close(self):
        if self.repl_process:
            self.repl_process.terminate()
        self.window.destroy()

    def open_project(self):
        path = filedialog.askdirectory(title="Select Clojure project directory")
        if path:
            self.project.load_project(path)
            self.refresh_project()
            self.update_status(f"Project loaded: {path}")

    def refresh_project(self):
        self.project_tree.delete(*self.project_tree.get_children())
        for ns in self.project.get_all_namespaces():
            node = self.project_tree.insert("", "end", text=ns)
            for fn in self.project.namespaces[ns].functions:
                self.project_tree.insert(node, "end", text=fn)

    def on_tree_double_click(self, event=None):
        selected_item = self.project_tree.selection()
        if selected_item:
            item_text = self.project_tree.item(selected_item[0], "text")
            self.update_status(f"Double-clicked: {item_text}")

    def search_docs(self, event=None):
        query = self.docs_search.get().strip().lower()
        self.docs_results.delete(*self.docs_results.get_children())
        for fn in self.project.get_all_functions():
            if query in fn.lower():
                ns, name = fn.split("/")
                self.docs_results.insert("", "end", values=(name, ns))

    def show_doc_for_selected(self, event=None):
        selected_item = self.docs_results.selection()
        if selected_item:
            name = self.docs_results.item(selected_item[0], "values")[0]
            self.send_to_repl(f"(doc {name})")

    def evaluate_selection(self):
        try:
            selection = self.editor.get(SEL_FIRST, SEL_LAST)
            if selection.strip():
                self.send_to_repl(selection)
        except TclError:
            self.update_status("No selection.")

    def evaluate_buffer(self):
        code = self.editor.get("1.0", END).strip()
        if code:
            self.send_to_repl(code)

    def evaluate_current_form(self):
        index = self.editor.index(INSERT)
        line, col = map(int, index.split('.'))
        lines = self.editor.get("1.0", END).split('\n')
        pos = sum(len(l) + 1 for l in lines[:line - 1]) + col
        text = '\n'.join(lines)
        start = end = pos
        depth = 0
        while start > 0:
            start -= 1
            if text[start] == ')':
                depth += 1
            elif text[start] == '(':
                if depth == 0: break
                depth -= 1
        depth = 0
        while end < len(text):
            if text[end] == '(':
                depth += 1
            elif text[end] == ')':
                if depth == 0: break
                depth -= 1
            end += 1
        form = text[start:end + 1].strip()
        if form:
            self.send_to_repl(form)

    def clojure_doc_prompt(self):
        sym = simpledialog.askstring("Doc", "Symbol:")
        if sym:
            self.send_to_repl(f"(doc {sym})")

    def clojure_source_prompt(self):
        sym = simpledialog.askstring("Source", "Symbol:")
        if sym:
            self.send_to_repl(f"(source {sym})")

    def run_lein_task(self):
        task = simpledialog.askstring("Lein Task", "Enter lein task:")
        if task:
            try:
                output = subprocess.check_output(["lein"] + task.split(), text=True)
                self.console_output.config(state=NORMAL)
                self.console_output.insert(END, output + "\n")
                self.console_output.config(state=DISABLED)
            except Exception as e:
                self.update_status(f"Error running task: {e}")

    def new_file(self):
        self.editor.delete("1.0", END)
        self.current_file = None
        self.update_status("New file created.")

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("Clojure files", "*.clj"), ("All files", "*.*")])
        if path:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.editor.delete("1.0", END)
            self.editor.insert("1.0", content)
            self.current_file = path
            self.add_to_recent_files(path)
            self.update_status(f"Opened file: {path}")

    def save_file(self):
        if not self.current_file:
            return self.save_as()
        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(self.editor.get("1.0", END))
            self.update_status("File saved.")
        except Exception as e:
            self.update_status(f"Save failed: {e}")

    def save_as(self):
        path = filedialog.asksaveasfilename(defaultextension=".clj", filetypes=[("Clojure files", "*.clj")])
        if path:
            self.current_file = path
            self.save_file()

    def load_recent_files(self):
        path = os.path.join(self.config_dir, "recent.json")
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return []

    def add_to_recent_files(self, path):
        if not path: return
        recent = self.load_recent_files()
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        recent = recent[:10]
        with open(os.path.join(self.config_dir, "recent.json"), 'w') as f:
            json.dump(recent, f)
        self.update_recent_files_menu()

    def update_recent_files_menu(self):
        self.recent_files_menu.delete(0, END)
        for path in self.load_recent_files():
            self.recent_files_menu.add_command(label=path, command=lambda p=path: self.open_recent(p))

    def open_recent(self, path):
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.editor.delete("1.0", END)
            self.editor.insert("1.0", content)
            self.current_file = path
            self.update_status(f"Opened recent file: {path}")
        else:
            self.update_status(f"File not found: {path}")


def main():
    app = ClojureWindow()
    app.window.mainloop()


if __name__ == "__main__":
    main()