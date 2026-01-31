import sys
import io
import re
import customtkinter as ctk
from contextlib import redirect_stdout, redirect_stderr
from src.ui.themed_window import ThemedWindow

class PythonTerminalWindow(ThemedWindow):
    def __init__(self, parent=None):
        if parent is None:
            try:
                from src.views.tk_utils import root
                parent = root
            except ImportError:
                pass
        super().__init__(parent)
        self.title("Python Terminal")
        self.geometry("800x600")

        self.setup_ui()

        self.command_history = []
        self.history_pointer = [0]
        self.namespace = {}
        self.current_block = []
        self.indent_level = 0

    def setup_ui(self):
        self.output_text = ctk.CTkTextbox(self, font=('Consolas', 12))
        self.output_text.pack(fill="both", expand=True, padx=10, pady=5)

        self.input_text = ctk.CTkTextbox(self, height=100, font=('Consolas', 12))
        self.input_text.pack(fill="x", expand=False, padx=10, pady=5)

        python_version = sys.version.split()[0]
        welcome_message = f"Python {python_version} on RuneScript\nType 'exit()' to exit\nShift+Enter for new line, Enter to execute\n>>> "
        self.output_text.insert("end", welcome_message)

        self.input_text.bind("<Return>", self.handle_return)
        self.input_text.bind("<Shift-Return>", self.handle_shift_return)
        self.input_text.bind("<Tab>", self.handle_tab)
        self.input_text.bind("<Up>", self.navigate_history)
        self.input_text.bind("<Down>", self.navigate_history)

        self.input_text.focus_set()

    def execute_python_code(self, code_to_execute):
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        try:
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                try:
                    result = eval(code_to_execute, self.namespace)
                    if result is not None:
                        print(repr(result))
                except SyntaxError:
                    exec(code_to_execute, self.namespace)
                except Exception as e:
                    raise e

            output = stdout_buffer.getvalue()
            errors = stderr_buffer.getvalue()

            if output:
                self.output_text.insert("end", output)
            if errors:
                self.output_text.insert("end", errors)

        except Exception as e:
            self.output_text.insert("end", f"{str(e)}\n")

        prompt = "... " if self.current_block else ">>> "
        self.output_text.insert("end", prompt)
        self.output_text.see("end")

    def handle_return(self, event):
        command = self.input_text.get("1.0", "end").strip()
        if not command:
            if self.current_block:
                full_code = '\n'.join(self.current_block)
                self.execute_python_code(full_code)
                self.current_block.clear()
                self.indent_level = 0
            else:
                self.output_text.insert("end", "\n>>> ")
            self.output_text.see("end")
            self.input_text.delete("1.0", "end")
            return "break"

        if command == 'exit()':
            self.destroy()
            return "break"

        self.output_text.insert("end", f"\n{command}\n")
        self.current_block.append(command)

        self.command_history.append(command)
        self.history_pointer[0] = len(self.command_history)

        full_code = '\n'.join(self.current_block)
        # Simple check for block completion (can be improved)
        if not command.endswith(':'):
             self.execute_python_code(full_code)
             self.current_block.clear()
             self.indent_level = 0
        else:
             self.output_text.insert("end", "... ")
             self.indent_level += 1

        self.input_text.delete("1.0", "end")
        if self.indent_level > 0:
            self.input_text.insert("1.0", "    " * self.indent_level)
        return "break"

    def handle_shift_return(self, event):
        self.input_text.insert("insert", "\n")
        return "break"

    def handle_tab(self, event):
        self.input_text.insert("insert", "    ")
        return "break"

    def navigate_history(self, event):
        if not self.command_history: return
        if event.keysym == "Up":
            self.history_pointer[0] = max(0, self.history_pointer[0] - 1)
        elif event.keysym == "Down":
            self.history_pointer[0] = min(len(self.command_history), self.history_pointer[0] + 1)

        if self.history_pointer[0] < len(self.command_history):
            command = self.command_history[self.history_pointer[0]]
            self.input_text.delete("1.0", "end")
            self.input_text.insert("1.0", command)
        else:
            self.input_text.delete("1.0", "end")
