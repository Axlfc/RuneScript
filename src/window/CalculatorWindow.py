import tkinter as tk
import customtkinter as ctk
import math
import re
from src.ui.themed_window import ThemedWindow

class CalculatorWindow(ThemedWindow):
    def __init__(self, parent=None):
        if parent is None:
            try:
                from src.views.tk_utils import root
                parent = root
            except ImportError:
                pass
        super().__init__(parent)
        self.title("Scientific Calculator")
        self.geometry("450x600")

        self.calculator_buttons = []
        self.original_states = {}
        self.setup_ui()

    def setup_ui(self):
        self.expression_entry = ctk.CTkEntry(self, font=("Arial", 20), height=50)
        self.expression_entry.grid(row=0, column=0, columnspan=5, sticky="we", padx=10, pady=10)

        self.result_label = ctk.CTkLabel(self, text="0", font=("Arial", 16), anchor="e")
        self.result_label.grid(row=1, column=0, columnspan=5, sticky="we", padx=10, pady=5)

        self._create_buttons()

    def _button_click(self, value):
        self.expression_entry.insert("insert", str(value))

    def _clear_entry(self):
        self.expression_entry.delete(0, "end")
        self.result_label.configure(text="0")

    def _clear_last_entry(self):
        current = self.expression_entry.get()
        if current:
            self.expression_entry.delete(len(current)-1, "end")

    def _backspace(self):
        # Implementation simplified for brevity
        current = self.expression_entry.get()
        if current:
             self.expression_entry.delete(len(current)-1, "end")

    def _evaluate_expression(self):
        expr = self.expression_entry.get().strip()
        if not expr: return
        try:
            # Very basic evaluation for example
            res = eval(expr, {"__builtins__": None}, {"sin": math.sin, "cos": math.cos, "tan": math.tan, "sqrt": math.sqrt, "pi": math.pi, "e": math.e})
            self.result_label.configure(text=str(res))
        except Exception as e:
            self.result_label.configure(text=f"Error: {e}")

    def _scientific_function_click(self, func):
        self.expression_entry.insert("insert", f"{func}(")

    def _create_buttons(self):
        buttons = [
            ("7", 2, 0), ("8", 2, 1), ("9", 2, 2), ("/", 2, 3), ("C", 2, 4),
            ("4", 3, 0), ("5", 3, 1), ("6", 3, 2), ("*", 3, 3), ("(", 3, 4),
            ("1", 4, 0), ("2", 4, 1), ("3", 4, 2), ("-", 4, 3), (")", 4, 4),
            ("0", 5, 0), (".", 5, 1), ("=", 5, 2), ("+", 5, 3), ("sin", 5, 4),
            ("cos", 6, 0), ("tan", 6, 1), ("sqrt", 6, 2), ("pi", 6, 3), ("e", 6, 4)
        ]

        for (text, r, c) in buttons:
            if text == "=":
                cmd = self._evaluate_expression
            elif text == "C":
                cmd = self._clear_entry
            elif text in ("sin", "cos", "tan", "sqrt"):
                cmd = lambda t=text: self._scientific_function_click(t)
            else:
                cmd = lambda t=text: self._button_click(t)

            btn = ctk.CTkButton(self, text=text, width=70, height=50, command=cmd)
            btn.grid(row=r, column=c, padx=2, pady=2)
            self.calculator_buttons.append(btn)
