from tkinter import ttk, scrolledtext
import tkinter as tk


class TestResultPanel(ttk.Frame):
    """Panel for displaying test results and status"""

    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()

    def create_widgets(self):
        # Test results display area with clear pass/fail visualization
        result_frame = ttk.LabelFrame(self, text="Test Results")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Test status indicator (Red/Green visual)
        self.status_frame = ttk.Frame(result_frame)
        self.status_frame.pack(fill=tk.X, padx=5, pady=5)

        self.status_indicator = ttk.Label(
            self.status_frame,
            text="No Tests Run",
            font=("Arial", 12, "bold"),
            background="#f0f0f0",
            padding=10,
            anchor="center"
        )
        self.status_indicator.pack(fill=tk.X)

        # Test output with detailed information
        self.output_frame = ttk.Frame(result_frame)
        self.output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.test_output = scrolledtext.ScrolledText(
            self.output_frame,
            wrap=tk.WORD,
            height=10
        )
        self.test_output.pack(fill=tk.BOTH, expand=True)

    def update_test_results(self, passed, stdout: str, stderr: str):
        """Updates the test results display with visually distinct stdout and stderr sections."""
        # Update the status indicator color and message
        if passed:
            self.status_indicator.configure(
                text="✅ Tests PASSED",
                background="#4CAF50",
                foreground="white"
            )
        else:
            self.status_indicator.configure(
                text="❌ Tests FAILED",
                background="#F44336",
                foreground="white"
            )

        self.test_output.configure(state=tk.NORMAL)
        self.test_output.delete("1.0", tk.END)

        # Add stdout section
        self.test_output.insert(tk.END, "=== Standard Output ===\n", "stdout_header")
        self.test_output.insert(tk.END, stdout.strip() + "\n\n", "stdout")

        # Add stderr section (only if there is any)
        if stderr.strip():
            self.test_output.insert(tk.END, "=== Error Output ===\n", "stderr_header")
            self.test_output.insert(tk.END, stderr.strip() + "\n", "stderr")

        # TODO: hook click-to-jump feature using pytest --json-report
        # Requires test line parsing and file opening
        # Placeholder for future implementation

        self.test_output.configure(state=tk.DISABLED)

        # Optional: tag formatting
        self.test_output.tag_configure("stdout_header", font=("Arial", 10, "bold"))
        self.test_output.tag_configure("stderr_header", font=("Arial", 10, "bold"))
        self.test_output.tag_configure("stdout", foreground="black")
        self.test_output.tag_configure("stderr", foreground="red")

    def clear_results(self):
        """Clears the test results"""
        self.status_indicator.configure(
            text="No Tests Run",
            background="#f0f0f0",
            foreground="black"
        )
        self.test_output.delete("1.0", tk.END)
