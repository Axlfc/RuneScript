import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from src.utils.event_system import EventSystem, Events

class TDDVisualizer(tb.Frame):
    """
    TDD Phase Visualizer (🔴 → 🟢 → 🔵).
    Purely informational with pulse animation for the active phase.
    """
    PHASES = {
        'RED': {'color': '#ff4444', 'icon': '🔴', 'label': 'RED'},
        'GREEN': {'color': '#44ff44', 'icon': '🟢', 'label': 'GREEN'},
        'REFACTOR': {'color': '#4444ff', 'icon': '🔵', 'label': 'REFACTOR'},
        'IDLE': {'color': '#888888', 'icon': '⚪', 'label': 'IDLE'}
    }

    def __init__(self, parent):
        super().__init__(parent)
        self.event_system = EventSystem.get_instance()
        self.current_phase = 'IDLE'
        self.pulse_val = 1.0
        self.pulse_dir = -0.1

        self._create_widgets()
        self._setup_event_listeners()
        self._animate_pulse()

    def _create_widgets(self):
        self.container = tb.Frame(self)
        self.container.pack(pady=10)

        self.bubbles = {}
        phases_list = ['RED', 'GREEN', 'REFACTOR']

        for i, phase in enumerate(phases_list):
            frame = tb.Frame(self.container)
            frame.pack(side=LEFT, padx=20)

            bubble = tb.Label(frame, text=self.PHASES[phase]['icon'], font=('Segoe UI', 32))
            bubble.pack()
            self.bubbles[phase] = bubble

            tb.Label(frame, text=self.PHASES[phase]['label'], font=('Segoe UI', 9, 'bold'), foreground="#888888").pack()

            if i < len(phases_list) - 1:
                tb.Label(self.container, text="→", font=('Segoe UI', 24), foreground="#444444").pack(side=LEFT)

    def _setup_event_listeners(self):
        self.event_system.subscribe(Events.PHASE_CHANGED, self.set_phase)

    def set_phase(self, phase_name):
        phase_name = phase_name.upper()
        if phase_name not in self.PHASES: return

        self.current_phase = phase_name
        self._update_display()

    def _update_display(self):
        for phase, bubble in self.bubbles.items():
            if phase == self.current_phase:
                bubble.configure(foreground=self.PHASES[phase]['color'])
            else:
                bubble.configure(foreground="#444444")

    def _animate_pulse(self):
        if self.current_phase in self.bubbles:
            bubble = self.bubbles[self.current_phase]
            self.pulse_val += self.pulse_dir
            if self.pulse_val <= 0.4: self.pulse_dir = 0.05
            elif self.pulse_val >= 1.0: self.pulse_dir = -0.05

            color = self.PHASES[self.current_phase]['color']
            # Simple brightness adjust (very crude for demo)
            if self.pulse_val < 0.7:
                 bubble.configure(foreground="#888888") # Dim
            else:
                 bubble.configure(foreground=color) # Bright

        self.after(200, self._animate_pulse)
