import tkinter as tk
from tkinter import ttk

class TDDWorkflowPanel(ttk.Frame):
    """
    An intelligent, guided TDD workbench to seamlessly guide the user
    through the Red-Green-Refactor cycle with AI assistance.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()

    def create_widgets(self):
        """Creates and lays out the new three-section TDD Workbench UI."""
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- Section 1: Goal & Status Header ---
        header_frame = ttk.Frame(self, padding=(10, 5))
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)

        goal_label = ttk.Label(header_frame, text="Your Goal:")
        goal_label.grid(row=0, column=0, padx=(0, 5), sticky="w")

        self.user_intent_input = ttk.Entry(header_frame, font=("TkDefaultFont", 10))
        self.user_intent_input.grid(row=0, column=1, sticky="ew")

        # State Indicator Frame
        self.state_indicator_frame = ttk.Frame(header_frame, relief="sunken", borderwidth=1, width=150)
        self.state_indicator_frame.grid(row=0, column=2, padx=(10, 0), sticky="e")
        self.state_indicator_label = ttk.Label(self.state_indicator_frame, text="AWAITING GOAL", font=("TkDefaultFont", 10, "bold"), padding=(10, 5))
        self.state_indicator_label.pack(expand=True, fill="both")

        self.primary_action_button = ttk.Button(header_frame, text="Generate Failing Test")
        self.primary_action_button.grid(row=0, column=3, padx=(5, 0), sticky="e")


        # --- Section 2: Code Panes (Split View) ---
        code_panes = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        code_panes.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Left Pane: Test Code
        test_code_frame = ttk.LabelFrame(code_panes, text="Test Code (Read-Only)")
        self.test_code_text = tk.Text(test_code_frame, wrap="word", state="disabled", bg="#f0f0f0")
        self.test_code_text.pack(expand=True, fill="both", padx=5, pady=5)
        code_panes.add(test_code_frame, weight=1)

        # Right Pane: Implementation Code
        impl_code_frame = ttk.LabelFrame(code_panes, text="Implementation Code")
        self.impl_code_text = tk.Text(impl_code_frame, wrap="word")
        self.impl_code_text.pack(expand=True, fill="both", padx=5, pady=5)
        code_panes.add(impl_code_frame, weight=1)


        # --- Section 3: Output & Suggestions Footer ---
        footer_frame = ttk.LabelFrame(self, text="Output")
        footer_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=(0, 5))
        footer_frame.grid_columnconfigure(0, weight=1)

        self.output_console_text = tk.Text(footer_frame, wrap="word", height=8, state="disabled", bg="#f0f0f0")
        self.output_console_text.pack(expand=True, fill="both", padx=5, pady=5)
        footer_frame.grid_columnconfigure(0, weight=1) # Ensure footer expands

        # --- nIA Suggestions Frame (initially hidden) ---
        self.nia_suggestions_frame = ttk.LabelFrame(self, text="nIA's Refactoring Suggestions")
        self.nia_suggestions_frame.grid_rowconfigure(0, weight=1)
        self.nia_suggestions_frame.grid_columnconfigure(0, weight=1)

        self.suggestion_text = tk.Text(self.nia_suggestions_frame, wrap="none", height=10, state="disabled")
        self.suggestion_text.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        self.accept_button = ttk.Button(self.nia_suggestions_frame, text="Accept")
        self.accept_button.grid(row=1, column=0, padx=5, pady=5, sticky="e")

        self.decline_button = ttk.Button(self.nia_suggestions_frame, text="Decline")
        self.decline_button.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        self.set_state("AWAITING_GOAL")

    def set_state(self, state: str, test_output: str = ""):
        """Updates the UI to reflect the current TDD state."""
        state_map = {
            "AWAITING_GOAL": {"text": "AWAITING GOAL", "color": "#e0e0e0", "button_text": "Generate Failing Test"},
            "RED": {"text": "🔴 RED", "color": "#ffdddd", "button_text": "Implement Solution"},
            "GREEN": {"text": "🟢 GREEN", "color": "#ddffdd", "button_text": "Suggest Refactoring"},
            "REFACTORING": {"text": "🔵 REFACTORING", "color": "#ddddff", "button_text": "Apply Suggestion"},
        }

        config = state_map.get(state, state_map["AWAITING_GOAL"])

        self.state_indicator_frame.config(style=f"{state}.TFrame")
        self.state_indicator_label.config(text=config["text"])
        self.primary_action_button.config(text=config["button_text"])

        # Show/hide suggestions panel
        if state == "REFACTORING":
            self.nia_suggestions_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
        else:
            self.nia_suggestions_frame.grid_remove()

        # Update style for the frame background color
        style = ttk.Style()
        style.configure(f"{state}.TFrame", background=config["color"])

        # Update output console
        self.output_console_text.config(state="normal")
        self.output_console_text.delete("1.0", tk.END)
        self.output_console_text.insert("1.0", test_output)
        self.output_console_text.config(state="disabled")

    def display_refactor_suggestions(self, diff: str):
        """Displays the diff in the suggestions text widget."""
        self.suggestion_text.config(state="normal")
        self.suggestion_text.delete("1.0", tk.END)
        self.suggestion_text.insert("1.0", diff)
        self.suggestion_text.config(state="disabled")
