from tkinter import ttk
import tkinter as tk


class TDDWorkflowPanel(ttk.Frame):
    """Panel specifically for managing the Red-Green-Refactor workflow"""

    def __init__(self, parent, on_run_tests, on_refactor, on_write_test):
        super().__init__(parent)
        self.current_phase = tk.StringVar(value="Write Test")
        self.create_widgets(on_run_tests, on_refactor, on_write_test)

    def create_widgets(self, on_run_tests, on_refactor, on_write_test):
        # Create phase indicator
        phase_frame = ttk.LabelFrame(self, text="TDD Cycle")
        phase_frame.pack(fill=tk.X, padx=5, pady=5)

        # Phase indicator
        phases = ["Write Test", "Run Test", "Write Code", "Run Test Again", "Refactor"]
        self.phase_indicators = {}

        for i, phase in enumerate(phases):
            col = i * 2  # Even columns for phases
            indicator = ttk.Label(phase_frame, text=phase, padding=5)
            indicator.grid(row=0, column=col, padx=5)
            self.phase_indicators[phase] = indicator

            if i < len(phases) - 1:
                arrow = ttk.Label(phase_frame, text="→")
                arrow.grid(row=0, column=col + 1, padx=2)  # Odd columns for arrows

        # Action buttons frame
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, padx=5, pady=5)

        # TDD workflow buttons with clear visual indicators
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

    def create_widgets(self, on_run_tests, on_refactor, on_write_test):
        # Create phase indicator
        phase_frame = ttk.LabelFrame(self, text="TDD Cycle")
        phase_frame.pack(fill=tk.X, padx=5, pady=5)

        # Phase indicator with interleaved arrows
        phases = ["Write Test", "Run Test", "Write Code", "Run Test Again", "Refactor"]
        self.phase_indicators = {}

        for i, phase in enumerate(phases):
            col = i * 2  # Even columns for phases
            indicator = ttk.Label(phase_frame, text=phase, padding=5)
            indicator.grid(row=0, column=col, padx=5)
            self.phase_indicators[phase] = indicator

            if i < len(phases) - 1:
                ttk.Label(phase_frame, text="→").grid(row=0, column=col + 1, padx=2)

        # Action buttons frame
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

    def update_phase(self, phase_name, test_status=None):
        """Updates the current phase indicator and button states"""
        # Reset all indicators
        for phase, indicator in self.phase_indicators.items():
            indicator.configure(background="", foreground="")

        # Highlight current phase
        if phase_name in self.phase_indicators:
            self.phase_indicators[phase_name].configure(background="#4a6cd4", foreground="white")

        # Update button states based on phase
        if phase_name == "Write Test":
            self.test_btn.configure(state=tk.NORMAL)
            self.run_tests_btn.configure(state=tk.DISABLED)
            self.refactor_btn.configure(state=tk.DISABLED)
        elif phase_name == "Run Test":
            self.test_btn.configure(state=tk.DISABLED)
            self.run_tests_btn.configure(state=tk.NORMAL)
            self.refactor_btn.configure(state=tk.DISABLED)
        elif phase_name == "Write Code":
            self.test_btn.configure(state=tk.DISABLED)
            self.run_tests_btn.configure(state=tk.NORMAL)
            self.refactor_btn.configure(state=tk.DISABLED)
        elif phase_name == "Run Test Again":
            self.test_btn.configure(state=tk.DISABLED)
            self.run_tests_btn.configure(state=tk.NORMAL)
            self.refactor_btn.configure(state=tk.DISABLED)
        elif phase_name == "Refactor":
            self.test_btn.configure(state=tk.DISABLED)
            self.run_tests_btn.configure(state=tk.NORMAL)
            self.refactor_btn.configure(state=tk.NORMAL)

        # Update button appearance based on test status
        if test_status == "failed":
            # Tests have failed - we're in the "red" phase
            self.run_tests_btn.configure(style="Red.TButton")
        elif test_status == "passed":
            # Tests have passed - we're in the "green" phase
            self.run_tests_btn.configure(style="Green.TButton")
        elif test_status is None:
            # Reset to default style
            self.run_tests_btn.configure(style="TButton")