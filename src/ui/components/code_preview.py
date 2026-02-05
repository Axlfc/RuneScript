import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from src.utils.event_system import EventSystem, Events

class CodePreview(tb.Frame):
    """
    Code Preview component with multi-tab support.
    Uses basic tkinter Text tags for syntax highlighting (implemented in Phase 4).
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.event_system = EventSystem.get_instance()

        self.tabs = ttk.Notebook(self, bootstyle=SECONDARY)
        self.tabs.pack(fill=BOTH, expand=True)

        self.editors = {} # {filepath: text_widget}

        self._setup_event_listeners()

    def _setup_event_listeners(self):
        self.event_system.subscribe("open_file", self.open_file)
        self.event_system.subscribe("file_modified", self._on_file_modified)

    def open_file(self, data):
        filepath = data.get('filepath')
        content = data.get('content', '')

        if filepath in self.editors:
            self.tabs.select(self.editors[filepath]['frame'])
            return

        frame = tb.Frame(self.tabs)
        self.tabs.add(frame, text=filepath.split('/')[-1])

        # Text widget with scrollbars
        text_area = tk.Text(frame, wrap=NONE, undo=True,
                            background="#1e1e1e", foreground="#d4d4d4",
                            insertbackground="white", font=('Consolas', 11))
        text_area.pack(side=LEFT, fill=BOTH, expand=True)

        vsb = tb.Scrollbar(frame, orient=VERTICAL, command=text_area.yview)
        vsb.pack(side=RIGHT, fill=Y)
        text_area.configure(yscrollcommand=vsb.set)

        hsb = tb.Scrollbar(frame, orient=HORIZONTAL, command=text_area.xview)
        hsb.pack(side=BOTTOM, fill=X)
        text_area.configure(xscrollcommand=hsb.set)

        # Configure syntax tags
        self._setup_syntax_tags(text_area)

        text_area.insert("1.0", content)
        self._apply_highlighting(text_area)

        text_area.edit_modified(False)

        self.editors[filepath] = {
            'frame': frame,
            'text': text_area
        }
        self.tabs.select(frame)

    def _setup_syntax_tags(self, text_widget):
        text_widget.tag_configure("keyword", foreground="#569cd6", font=('Consolas', 11, 'bold'))
        text_widget.tag_configure("string", foreground="#ce9178")
        text_widget.tag_configure("comment", foreground="#6a9955", font=('Consolas', 11, 'italic'))
        text_widget.tag_configure("function", foreground="#dcdcaa")
        text_widget.tag_configure("number", foreground="#b5cea8")

    def _apply_highlighting(self, text_widget):
        content = text_widget.get("1.0", tk.END)

        # Simple Regex-based highlighting
        import re

        # Keywords (Python + HTML tags)
        keywords = r'\b(def|class|if|else|elif|for|while|return|import|from|as|try|except|finally|with|in|is|not|and|or|lambda|None|True|False|html|head|body|div|span|p|h1|h2|h3|h4|h5|h6|ul|ol|li|a|img|table|tr|td|th|form|input|button|label|style|script|meta|link)\b'
        for match in re.finditer(keywords, content):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            text_widget.tag_add("keyword", start, end)

        # Strings
        strings = r'(\"[^\"]*\"|\'[^\']*\')'
        for match in re.finditer(strings, content):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            text_widget.tag_add("string", start, end)

        # Comments (Python, JS, HTML)
        comments = r'(#.*|//.*|<!--.*?-->)'
        for match in re.finditer(comments, content, re.DOTALL):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            text_widget.tag_add("comment", start, end)

    def _on_file_modified(self, data):
        filepath = data.get('filepath')
        if filepath in self.editors:
            text_area = self.editors[filepath]['text']
            # Re-apply highlighting if needed or update content
            self._apply_highlighting(text_area)

    def get_current_text(self):
        selected = self.tabs.select()
        for fp, editor in self.editors.items():
            if str(editor['frame']) == selected:
                return editor['text'].get("1.0", tk.END)
        return ""
