import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from src.utils.event_system import EventSystem, Events

class RightPanel(tb.Frame):
    """
    Right Panel component containing Metrics and Active Issues.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.event_system = EventSystem.get_instance()

        self.container = ScrolledFrame(self, autohide=True)
        self.container.pack(fill=BOTH, expand=True)

        self._create_metrics_section()
        self._create_issues_section()
        self._create_ai_output_section()

        self._setup_event_listeners()

    def _create_metrics_section(self):
        frame = tb.Labelframe(self.container, text="📊 METRICS", padding=10)
        frame.pack(fill=X, padx=5, pady=5)

        self.tests_var = tk.StringVar(value="✅ Tests: 0/0")
        self.coverage_var = tk.StringVar(value="📈 Coverage: 0%")
        self.quality_var = tk.StringVar(value="⚠️ Quality Issues: 0")

        tb.Label(frame, textvariable=self.tests_var, font=('Segoe UI', 9)).pack(anchor=W)
        tb.Label(frame, textvariable=self.coverage_var, font=('Segoe UI', 9)).pack(anchor=W)
        tb.Label(frame, textvariable=self.quality_var, font=('Segoe UI', 9)).pack(anchor=W)

        self.coverage_progress = ttk.Progressbar(frame, bootstyle=SUCCESS, value=0)
        self.coverage_progress.pack(fill=X, pady=5)

    def _create_issues_section(self):
        self.issues_frame = tb.Labelframe(self.container, text="🚨 ACTIVE ISSUES", padding=10)
        self.issues_frame.pack(fill=X, padx=5, pady=5)

        header = tb.Frame(self.issues_frame)
        header.pack(fill=X)
        tb.Button(header, text="View All ↗", bootstyle="link",
                  command=lambda: self.event_system.publish(Events.OPEN_ISSUE_MANAGER)).pack(side=RIGHT)

        self.issues_list = tb.Frame(self.issues_frame)
        self.issues_list.pack(fill=X, pady=5)

        tb.Label(self.issues_list, text="No active issues", foreground="#888888").pack()

    def _create_ai_output_section(self):
        frame = tb.Labelframe(self.container, text="💬 AI OUTPUT", padding=10)
        frame.pack(fill=BOTH, expand=True, padx=5, pady=5)

        self.ai_text = tk.Text(frame, height=10, wrap=WORD, background="#2b2b2b",
                               foreground="#cccccc", font=('Segoe UI', 9), state=DISABLED)
        self.ai_text.pack(fill=BOTH, expand=True)

    def _setup_event_listeners(self):
        self.event_system.subscribe("update_metrics", self.update_metrics)
        self.event_system.subscribe(Events.UPDATE_ACTIVE_ISSUES, self.update_issues)
        self.event_system.subscribe("ai_message", self.append_ai_message)

    def update_metrics(self, data):
        if 'tests' in data: self.tests_var.set(f"✅ Tests: {data['tests']}")
        if 'coverage' in data:
            self.coverage_var.set(f"📈 Coverage: {data['coverage']}%")
            self.coverage_progress['value'] = data['coverage']
        if 'quality' in data: self.quality_var.set(f"⚠️ Quality Issues: {data['quality']}")

    def update_issues(self, issues):
        for child in self.issues_list.winfo_children():
            child.destroy()

        if not issues:
            tb.Label(self.issues_list, text="No active issues", foreground="#888888").pack()
            return

        for issue in issues[:3]: # Show only top 3
            card = tb.Frame(self.issues_list, bootstyle=SECONDARY, padding=5)
            card.pack(fill=X, pady=2)

            severity_icon = "🔴" if issue.get('priority') == 'Critical' else "🟡"
            tb.Label(card, text=f"{severity_icon} #{issue.get('id')} {issue.get('title')[:20]}...",
                     font=('Segoe UI', 8, 'bold')).pack(anchor=W)

            btn_frame = tb.Frame(card)
            btn_frame.pack(fill=X)
            tb.Button(btn_frame, text="View", bootstyle=(INFO, OUTLINE), size=SMALL,
                      command=lambda i=issue: self.event_system.publish("view_issue", i)).pack(side=LEFT, padx=2)
            if issue.get('auto_fixable'):
                tb.Button(btn_frame, text="Fix", bootstyle=(SUCCESS, OUTLINE), size=SMALL,
                          command=lambda i=issue: self.event_system.publish(Events.APPLY_FIX, i)).pack(side=LEFT, padx=2)

    def append_ai_message(self, message):
        self.ai_text.configure(state=NORMAL)
        self.ai_text.insert(END, f"AI: {message}\n\n")
        self.ai_text.see(END)
        self.ai_text.configure(state=DISABLED)
