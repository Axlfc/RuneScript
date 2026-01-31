from tkinter import *
from src.config.fonts import AppFonts
from tkinter import filedialog, ttk
import tkinter as tk
import customtkinter as ctk
import sys
import io
import json
import markdown
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime
import re
from src.ui.themed_window import ThemedWindow


class IPythonNotebookTerminal(ThemedWindow):
    def __init__(self, parent=None):
        if parent is None:
            try:
                from src.views.tk_utils import root
                parent = root
            except ImportError:
                pass
        super().__init__(parent)
        self.window = self # self is the window
        self.title("IPython Notebook Terminal")
        self.geometry("1024x800")

        # Variables de estado
        self.cells = []  # Lista de celdas (código y markdown)
        self.current_cell = None
        self.namespace = {}  # Espacio de nombres para variables
        self.history = []
        self.history_pointer = 0

        self.setup_ui()
        self.setup_bindings()

    def setup_ui(self):
        """Configura la interfaz de usuario"""
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Barra de herramientas
        self.toolbar = ctk.CTkFrame(self.main_container)
        self.toolbar.pack(fill=tk.X, padx=5, pady=5)

        # Botones de la barra de herramientas
        ctk.CTkButton(self.toolbar, text="Nueva celda código", width=140, command=self.add_code_cell).pack(side=tk.LEFT, padx=5, pady=5)
        ctk.CTkButton(self.toolbar, text="Nueva celda Markdown", width=140, command=self.add_markdown_cell).pack(side=tk.LEFT, padx=5, pady=5)
        ctk.CTkButton(self.toolbar, text="Ejecutar celda", width=120, command=self.execute_current_cell).pack(side=tk.LEFT, padx=5, pady=5)
        ctk.CTkButton(self.toolbar, text="Guardar", width=80, command=self.save_notebook).pack(side=tk.LEFT, padx=5, pady=5)
        ctk.CTkButton(self.toolbar, text="Abrir", width=80, command=self.load_notebook).pack(side=tk.LEFT, padx=5, pady=5)

        # Canvas y scrollbar para el contenido
        self.scroll_container = ctk.CTkFrame(self.main_container)
        self.scroll_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(self.scroll_container, highlightthickness=0)
        self.scrollbar = ctk.CTkScrollbar(self.scroll_container, orientation="vertical", command=self.canvas.yview)
        self.scrollable_frame = ctk.CTkFrame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw",
                                  width=self.window.winfo_width() - 20)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        self.scrollbar.pack(side=RIGHT, fill=Y)

        # Configurar fuentes
        self.code_font = AppFonts.CODE_SMALL
        self.markdown_font = AppFonts.MARKDOWN

    def create_cell(self, cell_type="code"):
        """Crea una nueva celda del tipo especificado"""
        cell_frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=6)
        cell_frame.pack(fill=tk.X, padx=10, pady=10)

        # Barra de herramientas de la celda
        cell_toolbar = ctk.CTkFrame(cell_frame, height=30)
        cell_toolbar.pack(fill=tk.X)

        # Etiqueta que muestra el tipo de celda
        ctk.CTkLabel(cell_toolbar, text=f"[{cell_type}]", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=10)

        # Botones de la celda
        ctk.CTkButton(cell_toolbar, text="Eliminar", width=80, height=24, fg_color="transparent", border_width=1,
                   command=lambda: self.delete_cell(cell_frame)).pack(side=tk.RIGHT, padx=5, pady=3)
        ctk.CTkButton(cell_toolbar, text="Ejecutar", width=80, height=24,
                   command=lambda: self.execute_cell(cell_frame)).pack(side=tk.RIGHT, padx=5, pady=3)

        # Área de entrada
        input_text = ctk.CTkTextbox(cell_frame, height=100,
                          font=self.code_font if cell_type == "code" else self.markdown_font)
        input_text.pack(fill=tk.X, padx=10, pady=5)

        # Área de salida
        output_text = ctk.CTkTextbox(cell_frame, height=100,
                           font=self.code_font, state='disabled')
        output_text.pack(fill=tk.X, padx=10, pady=5)

        # Guardar información de la celda
        cell_info = {
            'frame': cell_frame,
            'type': cell_type,
            'input': input_text,
            'output': output_text,
            'toolbar': cell_toolbar
        }

        self.cells.append(cell_info)
        self.current_cell = cell_info
        input_text.focus_set()

        return cell_info

    def execute_cell(self, cell_frame):
        """Ejecuta el código de una celda"""
        cell = next((c for c in self.cells if c['frame'] == cell_frame), None)
        if not cell:
            return

        input_content = cell['input'].get("1.0", END).strip()
        output_text = cell['output']

        # Habilitar la salida para escritura
        output_text.configure(state='normal')
        output_text.delete("1.0", END)

        if cell['type'] == "code":
            # Ejecutar código Python
            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()

            try:
                with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                    try:
                        # Intentar evaluar como expresión
                        result = eval(input_content, self.namespace)
                        if result is not None:
                            print(repr(result))
                    except SyntaxError:
                        # Si falla, ejecutar como statement
                        exec(input_content, self.namespace)
                    except Exception as e:
                        print(f"Error: {str(e)}", file=stderr_buffer)

                output = stdout_buffer.getvalue()
                errors = stderr_buffer.getvalue()

                if output:
                    output_text.insert(END, output)
                if errors:
                    output_text.insert(END, errors, "error")

            except Exception as e:
                output_text.insert(END, f"Error: {str(e)}\n", "error")

        else:  # Markdown
            # Renderizar Markdown
            try:
                html = markdown.markdown(input_content)
                output_text.insert(END, html)
            except Exception as e:
                output_text.insert(END, f"Error rendering markdown: {str(e)}\n", "error")

        output_text.configure(state='disabled')

    def execute_current_cell(self):
        """Ejecuta la celda actual"""
        if self.current_cell:
            self.execute_cell(self.current_cell['frame'])

    def delete_cell(self, cell_frame):
        """Elimina una celda"""
        cell = next((c for c in self.cells if c['frame'] == cell_frame), None)
        if cell:
            self.cells.remove(cell)
            cell_frame.destroy()
            if cell == self.current_cell:
                self.current_cell = self.cells[-1] if self.cells else None

    def add_code_cell(self):
        """Agrega una nueva celda de código"""
        self.create_cell("code")

    def add_markdown_cell(self):
        """Agrega una nueva celda de Markdown"""
        self.create_cell("markdown")

    def save_notebook(self):
        """Guarda el notebook en formato .ipynb"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".ipynb",
            filetypes=[("Jupyter Notebook", "*.ipynb"), ("All Files", "*.*")]
        )

        if not filename:
            return

        notebook = {
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                },
                "language_info": {
                    "name": "python",
                    "version": sys.version.split()[0]
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4,
            "cells": []
        }

        for cell in self.cells:
            cell_content = {
                "cell_type": cell['type'],
                "metadata": {},
                "source": cell['input'].get("1.0", END).strip().split('\n')
            }

            if cell['type'] == "code":
                cell_content["outputs"] = [{
                    "output_type": "stream",
                    "text": cell['output'].get("1.0", END).strip().split('\n')
                }]
                cell_content["execution_count"] = None

            notebook["cells"].append(cell_content)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(notebook, f, indent=2)

    def load_notebook(self):
        """Carga un notebook desde un archivo .ipynb"""
        filename = filedialog.askopenfilename(
            filetypes=[("Jupyter Notebook", "*.ipynb"), ("All Files", "*.*")]
        )

        if not filename:
            return

        # Limpiar celdas existentes
        for cell in self.cells:
            cell['frame'].destroy()
        self.cells.clear()

        with open(filename, 'r', encoding='utf-8') as f:
            notebook = json.load(f)

        for cell_data in notebook["cells"]:
            cell_type = cell_data["cell_type"]
            cell = self.create_cell(cell_type)

            # Cargar contenido
            source = '\n'.join(cell_data["source"])
            cell['input'].delete("1.0", END)
            cell['input'].insert("1.0", source)

            # Si es una celda de código, ejecutarla
            if cell_type == "code":
                self.execute_cell(cell['frame'])

    def setup_bindings(self):
        """Configura los atajos de teclado"""
        self.window.bind("<Control-Return>", lambda e: self.execute_current_cell())
        self.window.bind("<Control-b>", lambda e: self.add_code_cell())
        self.window.bind("<Control-m>", lambda e: self.add_markdown_cell())
        self.window.bind("<Control-s>", lambda e: self.save_notebook())
        self.window.bind("<Control-o>", lambda e: self.load_notebook())
