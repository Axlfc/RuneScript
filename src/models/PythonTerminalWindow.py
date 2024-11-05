# PythonTerminalWindow.py
import sys
import io
import re
from tkinter import Toplevel, Frame, Text, END, INSERT
from tkinter import scrolledtext
from contextlib import redirect_stdout, redirect_stderr

from src.views.tk_utils import my_font


class PythonTerminalWindow:
    def __init__(self):
        """Initialize the Python Terminal window."""
        self.terminal_window = Toplevel()
        self.terminal_window.title("Python Terminal")
        self.terminal_window.geometry("800x600")

        # Main frame to organize widgets
        main_frame = Frame(self.terminal_window, bg='black')
        main_frame.pack(fill="both", expand=True)

        # Create output text widget with scroll
        self.output_text = scrolledtext.ScrolledText(main_frame, height=20, width=80, bg='black', fg='white',
                                                     insertbackground='white', font=('Consolas', 10))
        self.output_text.pack(fill="both", expand=True)

        # Create input text widget
        self.input_text = Text(main_frame, height=4, width=80, bg='black', fg='white',
                               insertbackground='white', font=my_font)
        self.input_text.pack(fill="x", expand=False)

        # Show the Python welcome message
        python_version = sys.version.split()[0]
        welcome_message = f"Python {python_version} on Tkinter\nType 'exit()' to exit\nShift+Enter for new line, Enter to execute\n>>> "
        self.output_text.insert(END, welcome_message)

        # Variables to maintain state
        self.command_history = []
        self.history_pointer = [0]
        self.namespace = {}
        self.current_block = []
        self.indent_level = 0

        # Configure key bindings
        self.input_text.bind("<Return>", self.handle_return)
        self.input_text.bind("<Shift-Return>", self.handle_shift_return)
        self.input_text.bind("<Tab>", self.handle_tab)
        self.input_text.bind("<Up>", self.navigate_history)
        self.input_text.bind("<Down>", self.navigate_history)

        # Configure tags for text formatting
        self.output_text.tag_config("error", foreground="red")

        # Set initial focus to input
        self.input_text.focus_set()

        # Configure window close behavior
        self.terminal_window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def check_complete_block(self, code):
        """Check if a block of code is complete."""
        if not code.strip():
            return True

        try:
            compile(code, '<string>', 'exec')
            return True
        except SyntaxError as e:
            if 'unexpected EOF' in str(e) or 'EOF in multi-line' in str(e):
                return False
            return True
        except Exception:
            return True

    def get_indent_level(self, line):
        """Calculate the indentation level of a line."""
        spaces = len(line) - len(line.lstrip())
        return spaces // 4

    def execute_python_code(self, code_to_execute):
        """Execute Python code and capture its output."""
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        try:
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                try:
                    # First, try to evaluate as an expression
                    result = eval(code_to_execute, self.namespace)
                    if result is not None:
                        print(repr(result))
                except SyntaxError:
                    # If it fails, execute as a statement
                    exec(code_to_execute, self.namespace)
                except Exception as e:
                    raise e

            output = stdout_buffer.getvalue()
            errors = stderr_buffer.getvalue()

            if output:
                self.output_text.insert(END, output)
            if errors:
                self.output_text.insert(END, errors, "error")

        except Exception as e:
            self.output_text.insert(END, f"{str(e)}\n", "error")

        prompt = "... " if self.current_block else ">>> "
        self.output_text.insert(END, prompt)
        self.output_text.see(END)

    def handle_shift_return(self, event):
        """Handle Shift+Enter to add a new line without executing."""
        self.input_text.insert(INSERT, '\n')
        if self.indent_level > 0:
            self.input_text.insert(INSERT, "    " * self.indent_level)
        return "break"

    def handle_return(self, event):
        """Handle Enter key to execute code."""
        # Get the full content of the input widget
        command = self.input_text.get("1.0", END).strip()

        if not command:
            if self.current_block:
                # Execute the current block if it exists
                full_code = '\n'.join(self.current_block)
                self.execute_python_code(full_code)
                self.current_block.clear()
                self.indent_level = 0
            self.output_text.insert(END, ">>> ")
            self.output_text.see(END)
            return "break"

        if command == 'exit()':
            self.terminal_window.destroy()
            return "break"

        # Process command line by line
        lines = command.split('\n')
        for line in lines:
            self.output_text.insert(END, f"{line}\n")
            if line.strip():
                self.current_block.append(line)
                if line.rstrip().endswith(':'):
                    self.indent_level += 1
                elif self.get_indent_level(line) < self.indent_level and line.strip():
                    self.indent_level = self.get_indent_level(line)

        # Add to history
        if command:
            self.command_history.append(command)
            self.history_pointer[0] = len(self.command_history)

        # Check if the block is complete
        full_code = '\n'.join(self.current_block)
        if self.check_complete_block(full_code):
            self.execute_python_code(full_code)
            self.current_block.clear()
            self.indent_level = 0
        else:
            self.output_text.insert(END, "... ")
            self.output_text.see(END)

        # Clear the input widget
        self.input_text.delete("1.0", END)
        if self.indent_level > 0:
            self.input_text.insert("1.0", "    " * self.indent_level)

        return "break"

    def handle_tab(self, event):
        """Handle Tab key for indentation."""
        self.input_text.insert(INSERT, "    ")
        return "break"

    def navigate_history(self, event):
        """Navigate command history with arrow keys."""
        if not self.command_history:
            return

        if event.keysym == "Up":
            self.history_pointer[0] = max(0, self.history_pointer[0] - 1)
        elif event.keysym == "Down":
            self.history_pointer[0] = min(len(self.command_history), self.history_pointer[0] + 1)

        if self.history_pointer[0] < len(self.command_history):
            command = self.command_history[self.history_pointer[0]]
            self.input_text.delete("1.0", END)
            self.input_text.insert("1.0", command)

    def on_closing(self):
        """Handle window close event."""
        self.terminal_window.destroy()
