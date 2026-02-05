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
        self.all_issues = []

        self._create_widgets()
        self._setup_event_listeners()

    def _setup_event_listeners(self):
        self.event_system.subscribe(Events.UPDATE_ACTIVE_ISSUES, self._on_issues_updated)

    def _on_issues_updated(self, issues):
        self.all_issues = issues
        if self.winfo_viewable():
            self._on_search()

    def _create_widgets(self):
        # Main container with a nice border
        main_container = tb.Frame(self, padding=2, bootstyle=DARK)
        main_container.pack(fill=BOTH, expand=True)

        # Header with Gradient-like feel
        header = tb.Frame(main_container, bootstyle=SECONDARY, padding=20)
        header.pack(fill=X)

        title_frame = tb.Frame(header, bootstyle=SECONDARY)
        title_frame.pack(side=LEFT)

        tb.Label(title_frame, text="🐛", font=('Segoe UI', 24), bootstyle="inverse-secondary").pack(side=LEFT, padx=(0, 10))
        tb.Label(title_frame, text="ISSUE MANAGER", font=('Segoe UI', 20, 'bold'), bootstyle="inverse-secondary").pack(side=LEFT)

        close_btn = tb.Button(header, text="✕ CLOSE", command=self.hide, bootstyle=(DANGER, OUTLINE), width=10)
        close_btn.pack(side=RIGHT)

        # Stats Bar
        self.stats_frame = tb.Frame(main_container, padding=(20, 10), bootstyle=LIGHT)
        self.stats_frame.pack(fill=X)

        # Filters & Search Bar
        filter_bar = tb.Frame(main_container, padding=(20, 10), bootstyle=LIGHT)
        filter_bar.pack(fill=X)

        tb.Label(filter_bar, text="FILTERS:", font=('Segoe UI', 9, 'bold')).pack(side=LEFT, padx=(0, 10))

        self.crit_var = tk.BooleanVar(value=True)
        self.warn_var = tk.BooleanVar(value=True)
        self.res_var = tk.BooleanVar(value=True)

        self.crit_filter = tb.Checkbutton(filter_bar, text="Critical", variable=self.crit_var,
                                          bootstyle=(DANGER, TOOLBUTTON), width=10, command=self._on_filter_change)
        self.crit_filter.pack(side=LEFT, padx=2)
        self.warn_filter = tb.Checkbutton(filter_bar, text="Warning", variable=self.warn_var,
                                          bootstyle=(WARNING, TOOLBUTTON), width=10, command=self._on_filter_change)
        self.warn_filter.pack(side=LEFT, padx=2)
        self.res_filter = tb.Checkbutton(filter_bar, text="Resolved", variable=self.res_var,
                                          bootstyle=(SUCCESS, TOOLBUTTON), width=10, command=self._on_filter_change)
        self.res_filter.pack(side=LEFT, padx=2)

        tb.Separator(filter_bar, orient=VERTICAL).pack(side=LEFT, padx=20, fill=Y)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._on_search())
        search_entry = tb.Entry(filter_bar, textvariable=self.search_var, width=40)
        search_entry.pack(side=LEFT, padx=5)
        tb.Label(filter_bar, text="🔍 Search issues...", font=('Segoe UI', 9, 'italic'), foreground="#888888").pack(side=LEFT)

        tb.Button(filter_bar, text="🗑️ Clear Resolved", bootstyle="secondary-outline-sm",
                  command=lambda: self.event_system.publish("clear_resolved_issues")).pack(side=RIGHT, padx=5)
        tb.Button(filter_bar, text="📊 Export Wiki", bootstyle="info-outline-sm",
                  command=lambda: self.event_system.publish("generate_wiki")).pack(side=RIGHT, padx=5)

        # Main Content - Scrollable area for Issue Cards
        self.scroll_frame = ScrolledFrame(main_container, autohide=True, bootstyle=LIGHT, padding=20)
        self.scroll_frame.pack(fill=BOTH, expand=True)

    def show(self, issues=None):
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lift()
        if issues:
            self.all_issues = issues
            self._display_issues(issues)
        elif self.all_issues:
            self._display_issues(self.all_issues)
        else:
            # Mock if absolutely nothing
            self._load_mock_issues()

    def _on_filter_change(self):
        self._on_search()

    def _on_search(self, *args):
        search_term = self.search_var.get().lower()

        filtered = []
        for issue in self.all_issues:
            # Severity check
            severity = issue.get('severity', 'info').lower()
            status = issue.get('status', 'Open').lower()

            show_by_sev = False
            if severity == 'critical' and self.crit_var.get(): show_by_sev = True
            elif severity == 'warning' and self.warn_var.get(): show_by_sev = True
            elif status == 'resolved' and self.res_var.get(): show_by_sev = True
            elif severity == 'info' and self.warn_var.get(): show_by_sev = True # Group info with warning

            if not show_by_sev: continue

            # Search check
            if search_term and search_term not in issue.get('title', '').lower() and \
               search_term not in issue.get('description', '').lower():
                continue

            filtered.append(issue)

        self._display_issues(filtered, update_all=False)

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

    def _display_issues(self, issues, update_all=True):
        if update_all:
            self.all_issues = issues

        for child in self.scroll_frame.winfo_children():
            child.destroy()

        if not issues:
            tb.Label(self.scroll_frame, text="No issues found matching filters.",
                     font=('Segoe UI', 12, 'italic'), foreground="#888888").pack(pady=50)
            return

        for issue in issues:
            self._create_issue_card(issue)

    def _on_search(self):
        # Implementation of search filtering
        pass

    def _create_issue_card(self, issue):
        # Card container with hover-like effect using style
        card_outer = tb.Frame(self.scroll_frame, padding=1, bootstyle=LIGHT)
        card_outer.pack(fill=X, pady=10)

        card = tb.Frame(card_outer, bootstyle=SECONDARY, padding=25)
        card.pack(fill=X)

        # Left Accent Border based on severity
        severity = issue.get('severity', 'info').lower()
        accent_color = "#ff4444" if severity == 'critical' else ("#ffcc00" if severity == 'warning' else "#38a169")
        accent = tb.Frame(card, width=5, bootstyle=DANGER if severity == 'critical' else (WARNING if severity == 'warning' else SUCCESS))
        accent.place(relx=0, rely=0, relheight=1, x=-25)

        # Header Row
        header = tb.Frame(card, bootstyle=SECONDARY)
        header.pack(fill=X)

        title_text = f"#{issue.get('id', '??')} - {issue.get('title', 'Untitled Issue')}"
        tb.Label(header, text=title_text, font=('Segoe UI', 16, 'bold'), foreground=accent_color).pack(side=LEFT)

        status_text = issue.get('status', 'OPEN').upper()
        if issue.get('auto_fixed'): status_text += " (AUTO-FIXED ✓)"

        badge_style = "inverse-danger" if severity == 'critical' else ("inverse-warning" if severity == 'warning' else "inverse-success")
        tb.Label(header, text=status_text, bootstyle=badge_style, padding=(10, 2)).pack(side=RIGHT)

        # Meta Info
        meta = tb.Frame(card, bootstyle=SECONDARY)
        meta.pack(fill=X, pady=(5, 15))
        meta_text = f"Task: {issue.get('task', 'N/A')}  |  Phase: {issue.get('phase', 'N/A')}  |  Created: {issue.get('created_at', 'Now')}"
        tb.Label(meta, text=meta_text, font=('Segoe UI', 9), foreground="#888888").pack(side=LEFT)

        # Description
        tb.Label(card, text=issue.get('description', ''), font=('Segoe UI', 11), wraplength=800, bootstyle="inverse-secondary").pack(anchor=W, pady=(0, 15))

        # Context (JSON) - Collapsible or always visible? Let's make it a nice code block
        if issue.get('context'):
            ctx_header = tb.Frame(card, bootstyle=SECONDARY)
            ctx_header.pack(fill=X, pady=(5, 0))
            tb.Label(ctx_header, text="📋 CONTEXT DATA", font=('Segoe UI', 9, 'bold'), foreground="#aaaaaa").pack(side=LEFT)

            ctx_frame = tb.Frame(card, bootstyle=DARK, padding=15)
            ctx_frame.pack(fill=X, pady=10)

            try:
                ctx_str = json.dumps(issue['context'], indent=2)
            except:
                ctx_str = str(issue['context'])

            tb.Label(ctx_frame, text=ctx_str, font=('Consolas', 10), foreground="#00ff00", justify=LEFT).pack(anchor=W)

        # Suggestions Section
        if issue.get('suggestions'):
            tb.Separator(card, orient=HORIZONTAL).pack(fill=X, pady=15)
            tb.Label(card, text="💡 AI SUGGESTED SOLUTIONS", font=('Segoe UI', 10, 'bold'), foreground=accent_color).pack(anchor=W, pady=(0, 10))

            for i, sug in enumerate(issue['suggestions']):
                s_frame = tb.Frame(card, bootstyle=SECONDARY, padding=5)
                s_frame.pack(fill=X, pady=2)

                tb.Label(s_frame, text=f"{i+1}.", font=('Segoe UI', 10, 'bold'), width=3).pack(side=LEFT)
                tb.Label(s_frame, text=sug, font=('Segoe UI', 10), wraplength=600).pack(side=LEFT, padx=5)

                # Check if it looks like a code fix
                btn_text = "Apply Fix"
                if "```" in sug: btn_text = "Apply Code Fix"

                tb.Button(s_frame, text=btn_text, bootstyle="success-sm",
                          command=lambda s=sug: self._apply_fix(issue.get('id'), s)).pack(side=RIGHT)

        # Bottom Actions Bar
        tb.Separator(card, orient=HORIZONTAL).pack(fill=X, pady=15)
        actions = tb.Frame(card, bootstyle=SECONDARY)
        actions.pack(fill=X)

        if issue.get('status', '').lower() != 'resolved':
            tb.Button(actions, text="📝 Manual Fix", bootstyle=(INFO, OUTLINE),
                      command=lambda: self.event_system.publish(Events.MANUAL_FIX_ISSUE, issue)).pack(side=LEFT, padx=5)
            tb.Button(actions, text="⏭️ Skip for Now", bootstyle=(SECONDARY, OUTLINE),
                      command=lambda: self.event_system.publish(Events.SKIP_ISSUE, issue)).pack(side=LEFT, padx=5)
            tb.Button(actions, text="🗑️ Ignore", bootstyle=(DANGER, OUTLINE),
                      command=lambda: self.event_system.publish(Events.IGNORE_ISSUE, issue)).pack(side=LEFT, padx=5)
        else:
            tb.Button(actions, text="📄 View Diff", bootstyle=(INFO, OUTLINE),
                      command=lambda: self.event_system.publish("view_issue_diff", issue)).pack(side=LEFT, padx=5)
            tb.Button(actions, text="🔄 Revert Fix", bootstyle=(WARNING, OUTLINE),
                      command=lambda: self.event_system.publish("revert_issue_fix", issue)).pack(side=LEFT, padx=5)
            tb.Button(actions, text="🗑️ Delete", bootstyle=(DANGER, OUTLINE),
                      command=lambda: self.event_system.publish("delete_issue", issue)).pack(side=LEFT, padx=5)

    def _apply_fix(self, issue_id, suggestion):
        self.event_system.publish(Events.APPLY_FIX, {'issue_id': issue_id, 'suggestion': suggestion})
        self.hide()
