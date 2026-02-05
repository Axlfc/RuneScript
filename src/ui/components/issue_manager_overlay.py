import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from src.utils.event_system import EventSystem, Events
import json

class IssueManagerOverlay(tb.Frame):
    """
    In-app Issue Manager Overlay (Frame-based).
    Allows managing errors, warnings, and applying auto-fixes.
    """
    def __init__(self, parent):
        super().__init__(parent, bootstyle=LIGHT)
        self.event_system = EventSystem.get_instance()

        self._create_widgets()

    def _create_widgets(self):
        # Header
        header = tb.Frame(self, bootstyle=SECONDARY, padding=15)
        header.pack(fill=X)

        tb.Label(header, text="🐛 ISSUE MANAGER", font=('Segoe UI', 18, 'bold'), bootstyle=INVERSE_SECONDARY).pack(side=LEFT)
        tb.Button(header, text="✕ Close Overlay", command=self.hide, bootstyle=DANGER).pack(side=RIGHT)

        # Filters Bar
        filter_bar = tb.Frame(self, padding=10)
        filter_bar.pack(fill=X)

        tb.Label(filter_bar, text="Filters:").pack(side=LEFT, padx=5)
        tb.Button(filter_bar, text="🔴 Critical", bootstyle=(DANGER, OUTLINE)).pack(side=LEFT, padx=2)
        tb.Button(filter_bar, text="🟡 Warning", bootstyle=(WARNING, OUTLINE)).pack(side=LEFT, padx=2)
        tb.Button(filter_bar, text="🟢 Resolved", bootstyle=(SUCCESS, OUTLINE)).pack(side=LEFT, padx=2)

        self.search_var = tk.StringVar()
        search_entry = tb.Entry(filter_bar, textvariable=self.search_var)
        search_entry.pack(side=RIGHT, padx=10, fill=X, expand=True)

        # Main Content - Scrollable area for Issue Cards
        self.scroll_frame = ScrolledFrame(self, autohide=True, bootstyle=LIGHT)
        self.scroll_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)

    def show(self, issues=None):
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lift()
        if issues:
            self._display_issues(issues)
        else:
            # Mock or request
            self._load_mock_issues()

    def hide(self):
        self.place_forget()

    def _load_mock_issues(self):
        mock_issues = [
            {
                'id': 47, 'title': 'Git Rollback Failure', 'severity': 'critical',
                'priority': 'Critical', 'status': 'Open', 'task': '2. HTML Structure',
                'phase': 'GREEN → RED', 'created_at': '2025-01-15 14:32:18',
                'description': 'Permission denied when trying to unlink .jsonl file.',
                'auto_fixed': False, 'auto_fixable': False,
                'context': {'error': 'PermissionError: [WinError 32]', 'files': ['loop_15.jsonl']},
                'suggestions': ['Ensure no processes are locking .jsonl files', 'Use force=True in git.reset()']
            },
            {
                'id': 48, 'title': 'Quality Issue: Line Count Exceeded', 'severity': 'warning',
                'priority': 'High', 'status': 'Open', 'task': '2. HTML Structure',
                'phase': 'GREEN', 'created_at': '2025-01-15 14:33:05',
                'description': 'index.html exceeded maximum line count.',
                'auto_fixed': True, 'auto_fixable': True,
                'context': {'file': 'index.html', 'current_lines': 79, 'max_lines': 50},
                'suggestions': ['Automatically expanded placeholder code']
            }
        ]
        self._display_issues(mock_issues)

    def _display_issues(self, issues):
        for child in self.scroll_frame.winfo_children():
            child.destroy()

        for issue in issues:
            self._create_issue_card(issue)

    def _create_issue_card(self, issue):
        card = tb.Frame(self.scroll_frame, bootstyle=SECONDARY, padding=20)
        card.pack(fill=X, pady=10)

        # Header Row
        header = tb.Frame(card, bootstyle=SECONDARY)
        header.pack(fill=X)

        severity_color = "#ff4444" if issue['priority'] == 'Critical' else "#ffcc00"
        tb.Label(header, text=f"#{issue['id']} - {issue['title']}",
                 font=('Segoe UI', 14, 'bold'), foreground=severity_color).pack(side=LEFT)

        status_text = "RESOLVED" if issue['status'] == 'Resolved' else issue['priority'].upper()
        tb.Label(header, text=status_text, bootstyle=INVERSE_DANGER if issue['priority'] == 'Critical' else INVERSE_WARNING).pack(side=RIGHT)

        # Meta Info
        meta = tb.Frame(card, bootstyle=SECONDARY)
        meta.pack(fill=X, pady=5)
        tb.Label(meta, text=f"Task: {issue['task']} | Phase: {issue['phase']} | Created: {issue['created_at']}",
                 font=('Segoe UI', 9), foreground="#aaaaaa").pack(side=LEFT)

        # Context
        if issue.get('context'):
            ctx_frame = tb.Frame(card, bootstyle=DARK, padding=10)
            ctx_frame.pack(fill=X, pady=10)
            tb.Label(ctx_frame, text=json.dumps(issue['context'], indent=2),
                     font=('Consolas', 10), foreground="#00ff00").pack(anchor=W)

        # Suggestions
        if issue.get('suggestions'):
            tb.Label(card, text="💡 AI Suggestions:", font=('Segoe UI', 10, 'bold')).pack(anchor=W, pady=(10, 5))
            for i, sug in enumerate(issue['suggestions']):
                s_frame = tb.Frame(card, bootstyle=SECONDARY)
                s_frame.pack(fill=X, pady=2)
                tb.Label(s_frame, text=f"{i+1}. {sug}", font=('Segoe UI', 10)).pack(side=LEFT)
                tb.Button(s_frame, text=f"Apply Fix", bootstyle=SUCCESS, size=SMALL,
                          command=lambda s=sug: self._apply_fix(issue['id'], s)).pack(side=RIGHT)

        # Actions
        actions = tb.Frame(card, bootstyle=SECONDARY)
        actions.pack(fill=X, pady=(15, 0))
        tb.Button(actions, text="Manual Fix", bootstyle=(INFO, OUTLINE)).pack(side=LEFT, padx=5)
        tb.Button(actions, text="Skip for Now", bootstyle=(SECONDARY, OUTLINE)).pack(side=LEFT, padx=5)
        tb.Button(actions, text="Ignore Permanently", bootstyle=(DANGER, OUTLINE)).pack(side=LEFT, padx=5)

    def _apply_fix(self, issue_id, suggestion):
        self.event_system.publish("apply_fix", {'issue_id': issue_id, 'suggestion': suggestion})
        self.hide()
