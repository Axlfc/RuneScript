from tkinter import *
from tkinter import scrolledtext, filedialog, ttk
from tkinter.font import Font
import sys
import io
import json
import markdown
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime
import re


class IPythonNotebookTerminal:
    def __init__(self):
        self.window = Toplevel()
        self.window.title("IPython Notebook Terminal")
        self.window.geometry("1024x768")

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
        # Barra de herramientas
        self.toolbar = Frame(self.window)
        self.toolbar.pack(fill=X, padx=5, pady=5)

        # Botones de la barra de herramientas
        ttk.Button(self.toolbar, text="Nueva celda código", command=self.add_code_cell).pack(side=LEFT, padx=2)
        ttk.Button(self.toolbar, text="Nueva celda Markdown", command=self.add_markdown_cell).pack(side=LEFT, padx=2)
        ttk.Button(self.toolbar, text="Ejecutar celda", command=self.execute_current_cell).pack(side=LEFT, padx=2)
        ttk.Button(self.toolbar, text="Guardar", command=self.save_notebook).pack(side=LEFT, padx=2)
        ttk.Button(self.toolbar, text="Abrir", command=self.load_notebook).pack(side=LEFT, padx=2)

        # Panel principal con scroll
        self.main_frame = Frame(self.window)
        self.main_frame.pack(fill=BOTH, expand=True)

        # Canvas y scrollbar para el contenido
        self.canvas = Canvas(self.main_frame, bg='white')
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient=VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = Frame(self.canvas, bg='white')

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
        self.code_font = Font(family="Consolas", size=10)
        self.markdown_font = Font(family="Arial", size=10)

    def create_cell(self, cell_type="code"):
        """Crea una nueva celda del tipo especificado"""
        cell_frame = Frame(self.scrollable_frame, bg='white', pady=5)
        cell_frame.pack(fill=X, padx=10)

        # Barra de herramientas de la celda
        cell_toolbar = Frame(cell_frame, bg='#f0f0f0')
        cell_toolbar.pack(fill=X)

        # Etiqueta que muestra el tipo de celda
        Label(cell_toolbar, text=f"[{cell_type}]", bg='#f0f0f0').pack(side=LEFT)

        # Botones de la celda
        ttk.Button(cell_toolbar, text="Ejecutar",
                   command=lambda: self.execute_cell(cell_frame)).pack(side=RIGHT)
        ttk.Button(cell_toolbar, text="Eliminar",
                   command=lambda: self.delete_cell(cell_frame)).pack(side=RIGHT)

        # Área de entrada
        input_text = Text(cell_frame, height=4, width=80,
                          font=self.code_font if cell_type == "code" else self.markdown_font)
        input_text.pack(fill=X, padx=5, pady=5)

        # Área de salida
        output_text = Text(cell_frame, height=4, width=80,
                           font=self.code_font, state='disabled')
        output_text.pack(fill=X, padx=5, pady=5)

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
        output_text.config(state='normal')
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

        output_text.config(state='disabled')

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