from tkinter import *
from tkinter import scrolledtext
from tkinter.ttk import Combobox
from datetime import datetime
import subprocess
import platform
import os
import time

from src.views.tk_utils import my_font


class TranslatorWindow:
    def __init__(self):
        self.translator_win = Toplevel()
        self.translator_win.title("Real-time Translator")
        self.translator_win.geometry("600x400")

        # Initialize instance variables
        self.last_translation = {"input": None}
        self.languages = [
            "English", "Spanish", "Chinese (Mandarin)", "German", "French", "Arabic",
            "Portuguese", "Russian", "Japanese", "Hindi", "Korean", "Turkish",
            "Italian", "Dutch", "Swedish", "Polish", "Vietnamese", "Thai",
            "Indonesian", "Czech", "Catalan", "Hebrew", "Greek", "Danish",
            "Finnish", "Norwegian", "Hungarian", "Romanian", "Bulgarian",
            "Ukrainian", "Bengali", "Punjabi", "Urdu", "Malay", "Persian (Farsi)",
            "Swahili", "Serbian", "Croatian", "Slovak", "Lithuanian", "Latvian",
            "Estonian", "Basque", "Icelandic", "Malayalam", "Tamil", "Telugu",
            "Gujarati", "Marathi", "Sinhala"
        ]

        self.setup_ui()
        self.translator_win.mainloop()

    def setup_ui(self):
        # Output area
        self.output_text = scrolledtext.ScrolledText(self.translator_win, height=15, width=85)
        self.output_text.pack(padx=10, pady=10)

        # Language selection frame
        self.setup_language_frame()

        # Input frame
        self.setup_input_frame()

    def setup_language_frame(self):
        lang_frame = Frame(self.translator_win)
        lang_frame.pack(fill=X, padx=10, pady=5)

        # Language variables
        self.input_lang_var = StringVar(value='Spanish')
        self.output_lang_var = StringVar(value='English')

        # Create dropdowns
        self.input_lang_dropdown = self.create_dropdown(lang_frame, "From:", self.input_lang_var)
        self.output_lang_dropdown = self.create_dropdown(lang_frame, "To:", self.output_lang_var)

        # Swap button
        swap_button = Button(lang_frame, text="Swap Languages",
                             command=self.swap_languages)
        swap_button.pack(side=LEFT, padx=(10, 10))

    def setup_input_frame(self):
        input_frame = Frame(self.translator_win)
        input_frame.pack(fill=X, padx=10, pady=5)

        # Input field
        self.input_entry = Text(input_frame, width=70, height=4, wrap="word", font=my_font)
        self.input_entry.pack(side=LEFT, padx=(0, 10))

        # Translate button
        translate_button = Button(input_frame, text="Translate",
                                  command=self.translate_text)
        translate_button.pack(side=LEFT, padx=(10, 10))

        # Bind keys
        self.input_entry.bind('<Return>', self.handle_enter)
        self.input_entry.bind('<Shift-Return>', lambda event: self.input_entry.insert(END, "\n"))

    def create_dropdown(self, frame, label_text, variable):
        label = Label(frame, text=label_text)
        label.pack(side=LEFT, padx=(0, 5))
        dropdown = Combobox(frame, textvariable=variable, values=self.languages,
                            state="readonly", width=15)
        dropdown.pack(side=LEFT, padx=(0, 10))
        return dropdown

    def swap_languages(self):
        current_input_lang = self.input_lang_var.get()
        current_output_lang = self.output_lang_var.get()

        self.input_lang_var.set(current_output_lang)
        self.output_lang_var.set(current_input_lang)

        self.input_lang_dropdown.set(self.input_lang_var.get())
        self.output_lang_dropdown.set(self.output_lang_var.get())

    def handle_enter(self, event):
        if event.state == 0:
            self.translate_text()
            return 'break'

    def translate_text(self):
        text = self.input_entry.get("1.0", END).strip()

        if text == self.last_translation.get("input"):
            return

        self.last_translation["input"] = text
        self.input_entry.config(state="disabled")

        prompt = f"Translate the following text from {self.input_lang_var.get()} to {self.output_lang_var.get()}: {text}"
        ai_script_path = "src/models/ai_assistant.py"
        command = self.create_ai_command(ai_script_path, prompt)

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                bufsize=1,
            )

            translation = ""
            self.output_text.insert(END,
                                    f"\n[{datetime.now().strftime('%H:%M:%S')}] From {self.input_lang_var.get()} to {self.output_lang_var.get()}:\n")
            for line in process.stdout:
                translation += line
                self.stream_translation(line)

            process.wait()

        except Exception as e:
            self.output_text.insert(END, f"Error: {e}\n")

        finally:
            self.input_entry.config(state="normal")

    def stream_translation(self, translation):
        for char in translation:
            self.output_text.insert(END, char)
            self.output_text.see(END)
            self.output_text.update()
            time.sleep(0.01)

    def create_ai_command(self, ai_script_path, user_prompt, agent_name=None):
        if platform.system() == "Windows":
            python_executable = os.path.join("venv", "Scripts", "python")
        else:
            python_executable = os.path.join("venv", "bin", "python3")

        if agent_name:
            return [python_executable, ai_script_path, user_prompt, agent_name]
        else:
            return [python_executable, ai_script_path, user_prompt]


