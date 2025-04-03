import tkinter as tk
from tkinter import ttk
import math
import re


class CalculatorWindow(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.title("Advanced Scientific Calculator")
        self.geometry("500x600")

        # Initialize instance variables
        self.original_states = {}
        self.calculator_buttons = []

        self._create_widgets()
        self._setup_grid()
        self._create_buttons()
        self._setup_bindings()

    def _create_widgets(self):
        # Create expression entry
        self.expression_entry = tk.Entry(
            self,
            width=30,
            font=("Arial", 18),
            borderwidth=2,
            relief="solid",
            justify="right",
        )
        self.expression_entry.grid(
            row=0, column=0, columnspan=5, padx=10, pady=10, sticky="nsew"
        )

        # Create result label
        self.result_label = tk.Label(
            self,
            text="",
            font=("Arial", 20, "bold"),
            anchor="e",
            background="white",
            foreground="black",
            borderwidth=2,
            relief="solid",
        )
        self.result_label.grid(row=1, column=0, columnspan=5, padx=10, pady=5, sticky="nsew")

    def _setup_grid(self):
        for i in range(9):
            self.grid_rowconfigure(i, weight=1)
        for i in range(5):
            self.grid_columnconfigure(i, weight=1)

    def _setup_bindings(self):
        self.result_label.bind("<Button-1>", self._copy_result_to_clipboard)
        self.result_label.bind("<Double-Button-1>", self._copy_result_to_clipboard)
        self.bind("<Return>", lambda event: self._evaluate_expression())
        self.bind("<Escape>", lambda event: self._clear_entry())

    def _update_result_display(self, message):
        self.result_label.config(text=message)

    def _copy_result_to_clipboard(self, event):
        result = self.result_label.cget("text")
        self.clipboard_clear()
        self.clipboard_append(result)

    def _button_click(self, value):
        current = self.expression_entry.get()
        if current in ("Error", "Invalid Input"):
            self.expression_entry.delete(0, tk.END)
        if self.expression_entry.selection_present():
            selection_start = self.expression_entry.index(tk.SEL_FIRST)
            selection_end = self.expression_entry.index(tk.SEL_LAST)
            self.expression_entry.delete(selection_start, selection_end)
            self.expression_entry.insert(selection_start, value)
            self.expression_entry.icursor(selection_start + len(value))
        else:
            cursor_position = self.expression_entry.index(tk.INSERT)
            self.expression_entry.insert(cursor_position, value)
            self.expression_entry.icursor(cursor_position + len(value))

    def _clear_entry(self):
        self.expression_entry.delete(0, tk.END)
        self._update_result_display("")

    def _clear_last_entry(self):
        current = self.expression_entry.get()
        cursor_position = self.expression_entry.index(tk.INSERT)
        if self.expression_entry.selection_present():
            selection_start = self.expression_entry.index(tk.SEL_FIRST)
            selection_end = self.expression_entry.index(tk.SEL_LAST)
            self.expression_entry.delete(selection_start, selection_end)
            self.expression_entry.icursor(selection_start)
            return
        if cursor_position == 0:
            return
        pattern = r"(\d+\.\d+|\d+|[a-zA-Z_][a-zA-Z0-9_]*|\S)"
        tokens = list(re.finditer(pattern, current[:cursor_position]))
        if not tokens:
            return
        last_token = tokens[-1]
        start, end = last_token.start(), last_token.end()
        self.expression_entry.delete(start, cursor_position)
        self.expression_entry.icursor(start)

    def _backspace(self):
        if self.expression_entry.selection_present():
            selection_start = self.expression_entry.index(tk.SEL_FIRST)
            selection_end = self.expression_entry.index(tk.SEL_LAST)
            self.expression_entry.delete(selection_start, selection_end)
            self.expression_entry.icursor(selection_start)
        else:
            cursor_position = self.expression_entry.index(tk.INSERT)
            if cursor_position > 0:
                self.expression_entry.delete(cursor_position - 1, cursor_position)

    def _toggle_scientific_calculator_buttons(self):
        toggle_map = {
            "x²": ("x³", lambda value="**3": self._button_click(value)),
            "xʸ": ("x⁽¹/ʸ⁾", lambda value="**(1/y)": self._button_click(value)),
            "sin": ("asin", lambda: self._scientific_function_click("asin")),
            "cos": ("acos", lambda: self._scientific_function_click("acos")),
            "tan": ("atan", lambda: self._scientific_function_click("atan")),
            "√": ("¹/ₓ", lambda value="1/": self._button_click(value)),
            "10ˣ": ("eˣ", lambda value="math.e**": self._button_click(value)),
            "log": ("ln", lambda: self._scientific_function_click("ln")),
            "Exp": ("dms", lambda value="dms(": self._button_click(value)),
            "Mod": ("deg", lambda value="deg(": self._button_click(value)),
        }

        for btn in self.calculator_buttons:
            current_text = btn["text"]
            if current_text in toggle_map:
                if btn not in self.original_states:
                    self.original_states[btn] = current_text, btn["command"]
                new_text, new_command = toggle_map[current_text]
                btn.config(text=new_text, command=new_command)
            elif any(current_text == pair[0] for pair in toggle_map.values()):
                reverse_map = {v[0]: (k, v[1]) for k, v in toggle_map.items()}
                original_text, original_command = reverse_map[current_text]
                if btn in self.original_states:
                    original_text, original_command = self.original_states[btn]
                    btn.config(text=original_text, command=original_command)

    def _balance_parentheses(self, expr):
        open_count = expr.count("(")
        close_count = expr.count(")")
        return expr + ")" * (open_count - close_count)

    def _evaluate_expression(self):
        try:
            expression = self.expression_entry.get().strip()
            if not expression:
                self._update_result_display("Error: Empty expression")
                return

            expression = self._balance_parentheses(expression)
            replacements = {
                "sin": "sin",
                "cos": "cos",
                "tan": "tan",
                "asin": "asin",
                "acos": "acos",
                "atan": "atan",
                "log": "log",
                "ln": "ln",
                "sqrt": "sqrt",
                "abs": "abs",
                "π": "pi",
                "e": "e",
                "**": "**",
                "^": "**",
                "√": "sqrt",
            }

            for old, new in replacements.items():
                expression = expression.replace(old, new)

            expression = re.sub(r"(\([^()]*\)|\d+)!", r"factorial\1", expression)
            expression = re.sub(r"(\d+)([a-zA-Z\(])", r"\1*\2", expression)
            expression = re.sub(r"([a-zA-Z\)])(\d+)", r"\1*\2", expression)
            expression = re.sub(r"([^\s\w\.\(\)])", r" \1 ", expression)

            safe_dict = {
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "asin": math.asin,
                "acos": math.acos,
                "atan": math.atan,
                "sqrt": math.sqrt,
                "abs": abs,
                "log": math.log10,
                "ln": math.log,
                "factorial": math.factorial,
                "pi": math.pi,
                "e": math.e,
            }

            if re.search(r"[^\d\w\s\+\-\*\/\^\(\)\.\,\!]", expression):
                self._update_result_display("Error: Invalid characters in expression")
                return

            result = eval(expression, {"__builtins__": None}, safe_dict)

            if isinstance(result, (int, float)):
                formatted_result = f"{result:.8g}"
            elif isinstance(result, complex):
                formatted_result = (
                    f"{result.real:.8g} + {result.imag:.8g}j"
                    if result.imag != 0
                    else f"{result.real:.8g}"
                )
            else:
                formatted_result = str(result)

            self._update_result_display(formatted_result)

        except ZeroDivisionError:
            self._update_result_display("Error: Division by zero")
        except ValueError as ve:
            self._update_result_display(f"Error: {str(ve)}")
        except SyntaxError:
            self._update_result_display("Error: Invalid syntax")
        except Exception as e:
            self._update_result_display(f"Error: {str(e)}")

    def _scientific_function_click(self, func_name):
        value = f"{func_name}("
        if self.expression_entry.selection_present():
            selection_start = self.expression_entry.index(tk.SEL_FIRST)
            selection_end = self.expression_entry.index(tk.SEL_LAST)
            self.expression_entry.delete(selection_start, selection_end)
            self.expression_entry.insert(selection_start, value)
            self.expression_entry.icursor(selection_start + len(value))
        else:
            cursor_position = self.expression_entry.index(tk.INSERT)
            self.expression_entry.insert(cursor_position, value)
            self.expression_entry.icursor(cursor_position + len(value))

    def _create_buttons(self):
        button_texts = [
            ("x²", 1, 0),
            ("xʸ", 1, 1),
            ("sin", 1, 2),
            ("cos", 1, 3),
            ("tan", 1, 4),
            ("√", 2, 0),
            ("10ˣ", 2, 1),
            ("log", 2, 2),
            ("Exp", 2, 3),
            ("Mod", 2, 4),
            ("↑", 3, 0),
            ("CE", 3, 1),
            ("C", 3, 2),
            ("←", 3, 3),
            ("/", 3, 4),
            ("π", 4, 0),
            ("7", 4, 1),
            ("8", 4, 2),
            ("9", 4, 3),
            ("*", 4, 4),
            ("e", 5, 0),
            ("4", 5, 1),
            ("5", 5, 2),
            ("6", 5, 3),
            ("-", 5, 4),
            ("x!", 6, 0),
            ("1", 6, 1),
            ("2", 6, 2),
            ("3", 6, 3),
            ("+", 6, 4),
            ("(", 7, 0),
            (")", 7, 1),
            ("0", 7, 2),
            (".", 7, 3),
            ("=", 7, 4),
        ]

        for text, row, col in button_texts:
            if text == "=":
                btn = tk.Button(
                    self,
                    text=text,
                    width=8,
                    height=2,
                    command=self._evaluate_expression,
                )
            elif text == "C":
                btn = tk.Button(
                    self, text=text, width=8, height=2, command=self._clear_entry
                )
            elif text == "CE":
                btn = tk.Button(
                    self,
                    text=text,
                    width=8,
                    height=2,
                    command=self._clear_last_entry,
                )
            elif text == "10ˣ":
                btn = tk.Button(
                    self,
                    text=text,
                    width=8,
                    height=2,
                    command=lambda: self._button_click("10**"),
                )
            elif text in (
                    "sin",
                    "cos",
                    "tan",
                    "log",
                    "ln",
                    "abs",
                    "asin",
                    "acos",
                    "atan",
                    "√",
            ):
                btn = tk.Button(
                    self,
                    text=text,
                    width=8,
                    height=2,
                    command=lambda t=text: self._scientific_function_click(t),
                )
            elif text in ("π", "e", "j"):
                btn = tk.Button(
                    self,
                    text=text,
                    width=8,
                    height=2,
                    command=lambda t=text: self._button_click(t),
                )
            elif text == "x!":
                btn = tk.Button(
                    self,
                    text=text,
                    width=8,
                    height=2,
                    command=lambda: self._button_click("!"),
                )
            elif text == "←":
                btn = tk.Button(
                    self, text="←", width=8, height=2, command=self._backspace
                )
            elif text == "↑":
                btn = tk.Button(
                    self,
                    text="↑",
                    width=8,
                    height=2,
                    command=self._toggle_scientific_calculator_buttons,
                )
            else:
                btn = tk.Button(
                    self,
                    text=text,
                    width=8,
                    height=2,
                    command=lambda t=text: self._button_click(t),
                )

            self.calculator_buttons.append(btn)
            btn.grid(row=row + 1, column=col, padx=2, pady=2)