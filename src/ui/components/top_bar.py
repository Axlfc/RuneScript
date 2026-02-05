import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from src.utils.event_system import EventSystem, Events
from datetime import datetime, timedelta

class TopBar(tb.Frame):
    """
    Top Bar component for project control and real-time telemetry.
    """
    def __init__(self, parent, on_generate, on_pause, on_stop):
        super().__init__(parent, style='TopBar.TFrame')
        self.on_generate = on_generate
        self.on_pause = on_pause
        self.on_stop = on_stop

        self.event_system = EventSystem.get_instance()

        self._create_widgets()
        self._setup_event_listeners()

        self.start_time = None
        self._update_timer()

    def _create_widgets(self):
        # 1. Control Row
        control_frame = tb.Frame(self, style='TopBar.TFrame')
        control_frame.pack(fill=X, side=TOP, padx=10, pady=5)

        self.prompt_entry = tb.Entry(control_frame, width=50)
        self.prompt_entry.pack(side=LEFT, padx=5, fill=X, expand=True)

        self.gen_btn = tb.Button(control_frame, text="Generate Project", command=self.on_generate, bootstyle=SUCCESS)
        self.gen_btn.pack(side=LEFT, padx=2)

        self.nia_btn = tb.Button(control_frame, text="nIA Mode", command=lambda: self.on_generate(nia_mode=True), bootstyle=INFO)
        self.nia_btn.pack(side=LEFT, padx=2)

        self.pause_btn = tb.Button(control_frame, text="⏸ Pause", command=self.on_pause, bootstyle=WARNING)
        self.pause_btn.pack(side=LEFT, padx=2)

        self.stop_btn = tb.Button(control_frame, text="⏹ Stop", command=self.on_stop, bootstyle=DANGER)
        self.stop_btn.pack(side=LEFT, padx=2)

        # Toggle Buttons
        ttk.Separator(control_frame, orient=VERTICAL).pack(side=LEFT, padx=10, fill=Y)

        self.toggle_left_btn = tb.Button(control_frame, text="📁", command=lambda: self.event_system.publish("toggle_left_panel"), bootstyle="link")
        self.toggle_left_btn.pack(side=LEFT, padx=2)

        self.toggle_bottom_btn = tb.Button(control_frame, text="📋", command=lambda: self.event_system.publish("toggle_console"), bootstyle="link")
        self.toggle_bottom_btn.pack(side=LEFT, padx=2)

        self.toggle_right_btn = tb.Button(control_frame, text="📊", command=lambda: self.event_system.publish("toggle_right_panel"), bootstyle="link")
        self.toggle_right_btn.pack(side=LEFT, padx=2)

        # 2. Telemetry Row
        telemetry_frame = tb.Frame(self, style='TopBar.TFrame')
        telemetry_frame.pack(fill=X, side=TOP, padx=10, pady=5)

        self.progress_var = tk.StringVar(value="Progress: Task 0/0")
        self.loop_var = tk.StringVar(value="Loop 0/0")
        self.phase_var = tk.StringVar(value="Phase: IDLE")
        self.timer_var = tk.StringVar(value="⏱️ 00:00:00")

        tb.Label(telemetry_frame, textvariable=self.progress_var, style='Telemetry.TLabel').pack(side=LEFT, padx=10)
        tb.Label(telemetry_frame, text="|", style='Telemetry.TLabel').pack(side=LEFT)
        tb.Label(telemetry_frame, textvariable=self.loop_var, style='Telemetry.TLabel').pack(side=LEFT, padx=10)
        tb.Label(telemetry_frame, text="|", style='Telemetry.TLabel').pack(side=LEFT)
        self.phase_label = tb.Label(telemetry_frame, textvariable=self.phase_var, style='Telemetry.TLabel')
        self.phase_label.pack(side=LEFT, padx=10)
        tb.Label(telemetry_frame, text="|", style='Telemetry.TLabel').pack(side=LEFT)
        tb.Label(telemetry_frame, textvariable=self.timer_var, style='Telemetry.TLabel').pack(side=LEFT, padx=10)

        # 3. Issues Badges
        self.issues_frame = tb.Frame(telemetry_frame, style='TopBar.TFrame')
        self.issues_frame.pack(side=RIGHT, padx=10)

        tb.Label(self.issues_frame, text="Issues:", style='Telemetry.TLabel').pack(side=LEFT, padx=5)

        self.crit_badge = tb.Label(self.issues_frame, text="🔴 0", style='StatusBadge.TLabel', foreground='#e53e3e', cursor="hand2")
        self.crit_badge.pack(side=LEFT, padx=2)
        self.crit_badge.bind("<Button-1>", lambda e: self.event_system.publish(Events.OPEN_ISSUE_MANAGER))

        self.warn_badge = tb.Label(self.issues_frame, text="🟡 0", style='StatusBadge.TLabel', foreground='#d69e2e', cursor="hand2")
        self.warn_badge.pack(side=LEFT, padx=2)
        self.warn_badge.bind("<Button-1>", lambda e: self.event_system.publish(Events.OPEN_ISSUE_MANAGER))

        self.res_badge = tb.Label(self.issues_frame, text="🟢 0", style='StatusBadge.TLabel', foreground='#38a169', cursor="hand2")
        self.res_badge.pack(side=LEFT, padx=2)
        self.res_badge.bind("<Button-1>", lambda e: self.event_system.publish(Events.OPEN_ISSUE_MANAGER))

        link = tb.Label(self.issues_frame, text="[Click to open Issue Manager]", font=('Segoe UI', 9), foreground='#3182ce', cursor="hand2")
        link.pack(side=LEFT, padx=5)
        link.bind("<Button-1>", lambda e: self.event_system.publish(Events.OPEN_ISSUE_MANAGER))

    def _setup_event_listeners(self):
        self.event_system.subscribe(Events.TELEMETRY_UPDATE, self._on_telemetry_update)
        self.event_system.subscribe(Events.PHASE_CHANGED, self._on_phase_changed)
        self.event_system.subscribe(Events.UPDATE_ISSUE_COUNTS, self._on_issues_update)

    def _on_telemetry_update(self, data):
        if 'task_current' in data and 'task_total' in data:
            self.progress_var.set(f"Progress: Task {data['task_current']}/{data['task_total']}")
        if 'loop_current' in data and 'loop_total' in data:
            self.loop_var.set(f"Loop {data['loop_current']}/{data['loop_total']}")
        if 'start_timer' in data and data['start_timer']:
            self.start_time = datetime.now()
        if 'stop_timer' in data and data['stop_timer']:
            self.start_time = None

    def _on_phase_changed(self, phase):
        self.phase_var.set(f"Phase: {phase}")
        color = '#ffffff'
        if 'RED' in phase: color = '#ff4444'
        elif 'GREEN' in phase: color = '#44ff44'
        elif 'REFACTOR' in phase: color = '#4444ff'
        self.phase_label.configure(foreground=color)

    def _on_issues_update(self, data):
        self.crit_badge.configure(text=f"🔴 {data.get('critical', 0)}")
        self.warn_badge.configure(text=f"🟡 {data.get('warning', 0)}")
        self.res_badge.configure(text=f"🟢 {data.get('resolved', 0)}")

    def _update_timer(self):
        if self.start_time:
            delta = datetime.now() - self.start_time
            # Format as HH:MM:SS
            time_str = str(timedelta(seconds=int(delta.total_seconds())))
            if len(time_str) == 7: time_str = "0" + time_str # Ensure HH:MM:SS
            self.timer_var.set(f"⏱️ {time_str}")
        self.after(1000, self._update_timer)
