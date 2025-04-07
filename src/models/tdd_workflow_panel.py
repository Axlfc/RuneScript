from tkinter import ttk
import tkinter as tk
from typing import Optional

from src.views.tk_utils import PHASE_UI_LABELS


class TDDWorkflowPanel(ttk.Frame):
    """Panel specifically for managing the Red-Green-Refactor workflow"""

    def __init__(self, parent, on_run_tests, on_refactor, on_write_test, on_rerun_last=None):
        super().__init__(parent)
        self.current_phase = tk.StringVar(value="Write Test")
        self.create_widgets(on_run_tests, on_refactor, on_write_test, on_rerun_last)

    def create_widgets(self, on_run_tests, on_refactor, on_write_test, on_rerun_last):
        # Phase indicators
        phase_frame = ttk.LabelFrame(self, text="TDD Cycle")
        phase_frame.pack(fill=tk.X, padx=5, pady=5)

        phases = ["Write Test", "Run Test", "Write Code", "Run Test Again", "Refactor"]
        self.phase_indicators = {}

        for i, phase in enumerate(phases):
            col = i * 2
            indicator = ttk.Label(phase_frame, text=phase, padding=5)
            indicator.grid(row=0, column=col, padx=5)
            self.phase_indicators[phase] = indicator

            if i < len(phases) - 1:
                ttk.Label(phase_frame, text="→").grid(row=0, column=col + 1, padx=2)

        # Action buttons
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, padx=5, pady=5)

        self.test_btn = ttk.Button(
            action_frame,
            text="1. Write Test (Red)",
            style="Red.TButton",
            command=on_write_test
        )
        self.test_btn.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)

        self.run_tests_btn = ttk.Button(
            action_frame,
            text="2. Run Tests",
            command=on_run_tests
        )
        self.run_tests_btn.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)

        self.refactor_btn = ttk.Button(
            action_frame,
            text="3. Refactor (Green → Clean)",
            style="Green.TButton",
            command=on_refactor
        )
        self.refactor_btn.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)

        # 🔁 Re-run last test button (optional)
        if on_rerun_last:
            self.rerun_btn = ttk.Button(
                action_frame,
                text="🔁 Re-run Last Test",
                command=on_rerun_last,
                state=tk.DISABLED  # Start disabled
            )
            self.rerun_btn.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
            self.last_result_label = ttk.Label(action_frame, text="")  # Empty until first test
            self.last_result_label.pack(side=tk.LEFT, padx=5)

        self.last_result_label = ttk.Label(
            action_frame,
            text="🔁 Last: None",
            foreground="gray"
        )
        self.last_result_label.pack(side=tk.LEFT, padx=5)

    def update_last_test_summary(self, status: Optional[str]):
        """Update the label showing last test result"""
        if hasattr(self, 'last_result_label'):
            if status == "passed":
                self.last_result_label.config(text="✔️ Last: Passed", foreground="green")
            elif status == "failed":
                self.last_result_label.config(text="❌ Last: Failed", foreground="red")
            else:
                self.last_result_label.config(text="")

    def update_phase(self, phase_name: str, test_status: Optional[str] = None):
        """
        Updates the current phase indicator and button states.

        Args:
            phase_name (str): The UI-label of the phase (e.g., "Write Test", "Refactor")
            test_status (Optional[str]): Test result status ("passed", "failed", None)
        """
        assert phase_name in self.phase_indicators, f"[TDDWorkflowPanel] Unknown UI phase label: '{phase_name}'"

        for phase, indicator in self.phase_indicators.items():
            indicator.configure(background="", foreground="")

        self.phase_indicators[phase_name].configure(background="#4a6cd4", foreground="white")

        if phase_name == "Write Test":
            self.test_btn.configure(state=tk.NORMAL)
            self.run_tests_btn.configure(state=tk.DISABLED)
            self.refactor_btn.configure(state=tk.DISABLED)
        elif phase_name in ["Run Test", "Write Code", "Run Test Again"]:
            self.test_btn.configure(state=tk.DISABLED)
            self.run_tests_btn.configure(state=tk.NORMAL)
            self.refactor_btn.configure(state=tk.DISABLED)
        elif phase_name == "Refactor":
            self.test_btn.configure(state=tk.DISABLED)
            self.run_tests_btn.configure(state=tk.NORMAL)
            self.refactor_btn.configure(state=tk.NORMAL)

        if test_status == "failed":
            self.run_tests_btn.configure(style="Red.TButton")
        elif test_status == "passed":
            self.run_tests_btn.configure(style="Green.TButton")
        elif test_status is None:
            self.run_tests_btn.configure(style="TButton")

    def set_rerun_enabled(self, enabled: bool, result_label: Optional[str] = None):
        if hasattr(self, 'rerun_btn'):
            if result_label:
                self.rerun_btn.config(state=tk.NORMAL if enabled else tk.DISABLED)
                self.rerun_btn.config(text=f"🔁 Last: {result_label}")

    def update_last_result_label(self, passed: Optional[bool]):
        """Show summary icon next to rerun button"""
        if not hasattr(self, "last_result_label"):
            return
        if passed is True:
            self.last_result_label.config(text="✔️ Last: Passed", foreground="green")
        elif passed is False:
            self.last_result_label.config(text="❌ Last: Failed", foreground="red")
        else:
            self.last_result_label.config(text="🔁 Last: None", foreground="gray")
