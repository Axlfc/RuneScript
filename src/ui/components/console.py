import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from src.utils.event_system import EventSystem, Events
from datetime import datetime

class TabbedConsole(tb.Frame):
    """
    Tabbed Console component for Errors, Warnings, All Logs, Git, and Issues.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.event_system = EventSystem.get_instance()

        self.tabs = ttk.Notebook(self, bootstyle=INFO)
        self.tabs.pack(fill=BOTH, expand=True)

        self.log_widgets = {} # {category: text_widget}
        categories = [
            ('All Logs', Events.LOG_MESSAGE),
            ('🔴 Errors', 'log_error'),
            ('⚠️ Warnings', 'log_warning'),
            ('🔧 Git', 'log_git'),
            ('🐛 Issues', 'log_issue')
        ]

        for label, event in categories:
            frame = tb.Frame(self.tabs)
            self.tabs.add(frame, text=label)

            text_area = tk.Text(frame, wrap=WORD, background="#1e1e1e",
                                foreground="#cccccc", font=('Consolas', 10), state=DISABLED)
            text_area.pack(fill=BOTH, expand=True)

            # Tag configurations for colors
            text_area.tag_configure("timestamp", foreground="#666666")
            text_area.tag_configure("error", foreground="#ff4444")
            text_area.tag_configure("warning", foreground="#ffcc00")
            text_area.tag_configure("info", foreground="#cccccc")
            text_area.tag_configure("git", foreground="#00bfff")

            self.log_widgets[label] = text_area

        self._setup_event_listeners()

    def _setup_event_listeners(self):
        self.event_system.subscribe(Events.LOG_MESSAGE, self.log_all)
        self.event_system.subscribe("log_error", lambda m: self.log_category('🔴 Errors', m, 'error'))
        self.event_system.subscribe("log_warning", lambda m: self.log_category('⚠️ Warnings', m, 'warning'))
        self.event_system.subscribe("log_git", lambda m: self.log_category('🔧 Git', m, 'git'))
        self.event_system.subscribe("log_issue", lambda m: self.log_category('🐛 Issues', m, 'info'))

    def log_all(self, message):
        self.log_category('All Logs', message)

        # Auto-routing based on content
        lower_msg = message.lower()
        if "error" in lower_msg or "exception" in lower_msg or "failed" in lower_msg:
            self.log_category('🔴 Errors', message, 'error')
        elif "warning" in lower_msg or "warn" in lower_msg:
            self.log_category('⚠️ Warnings', message, 'warning')
        elif "git" in lower_msg or "commit" in lower_msg or "checkpoint" in lower_msg:
            self.log_category('🔧 Git', message, 'git')
        elif "issue" in lower_msg:
            self.log_category('🐛 Issues', message, 'info')

    def log_category(self, category, message, tag='info'):
        if category in self.log_widgets:
            widget = self.log_widgets[category]
            widget.configure(state=NORMAL)
            timestamp = datetime.now().strftime("[%H:%M:%S] ")
            widget.insert(END, timestamp, "timestamp")
            widget.insert(END, message + "\n", tag)
            widget.see(END)
            widget.configure(state=DISABLED)

    def clear(self):
        for widget in self.log_widgets.values():
            widget.configure(state=NORMAL)
            widget.delete("1.0", END)
            widget.configure(state=DISABLED)
