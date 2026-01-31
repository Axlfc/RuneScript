import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import time
import json
import threading
import os
from src.utils.thread_manager import thread_manager
from src.ui.themed_window import ThemedWindow
from src.window.Notificador import Notificador

CONFIG_FILE = "planner_config.json"


def cargar_datos():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return {"rutina": [], "compras": [], "comidas": [], "cronometros": [], "habitos": []}


def guardar_datos(data):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo guardar el archivo: {e}")


class PlannerWindow(ThemedWindow):
    def __init__(self, parent=None):
        if parent is None:
            try:
                from src.views.tk_utils import root
                parent = root
            except ImportError:
                pass
        super().__init__(parent)
        self.title("Productivity Planner")
        self.geometry("1000x650")
        self.data = cargar_datos()

        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(expand=1, fill='both', padx=10, pady=10)

        self._setup_tabs()

    def _setup_tabs(self):
        sections = {
            "Rutina Diaria": self._rutina_ui,
            "Alarmas y Acciones": self._cronometros_ui,
            "Plan de Comidas": self._comidas_ui,
            "Lista de Compras": self._compras_ui,
            "Hábitos y Rituales": self._habitos_ui
        }
        for nombre, metodo in sections.items():
            self.tabs.add(nombre)
            metodo(self.tabs.tab(nombre))

    def _rutina_ui(self, frame):
        ctk.CTkLabel(frame, text="Rutina Diaria Personalizada").pack(pady=10)
        self.rutina_text = ctk.CTkTextbox(frame, height=400)
        self.rutina_text.pack(expand=True, fill='both', padx=20)
        if self.data.get("rutina"):
            self.rutina_text.insert('1.0', "\n".join(self.data["rutina"]))
        ctk.CTkButton(frame, text="Guardar Rutina", command=self._guardar_rutina).pack(pady=10)

    def _guardar_rutina(self):
        texto = self.rutina_text.get('1.0', 'end').strip()
        self.data["rutina"] = texto.split("\n")
        guardar_datos(self.data)
        messagebox.showinfo("Guardado", "Rutina guardada correctamente.")

    def _cronometros_ui(self, frame):
        ctk.CTkLabel(frame, text="Crear Cronómetro con Acción").pack(pady=10)
        frm = ctk.CTkFrame(frame)
        frm.pack(pady=10, padx=20, fill="x")

        self.entrada_nombre = ctk.CTkEntry(frm, placeholder_text="Nombre")
        self.entrada_duracion = ctk.CTkEntry(frm, placeholder_text="Duración (min)")
        self.tipo_cronometro = ctk.CTkComboBox(frm, values=["Normal", "Pomodoro"])
        self.tipo_cronometro.set("Normal")
        self.entrada_comando = ctk.CTkEntry(frm, placeholder_text="Comando opcional")

        etiquetas = ["Nombre:", "Duración (min):", "Tipo:", "Comando opcional:"]
        entradas = [self.entrada_nombre, self.entrada_duracion, self.tipo_cronometro, self.entrada_comando]
        for i, (et, ent) in enumerate(zip(etiquetas, entradas)):
            ctk.CTkLabel(frm, text=et).grid(row=i, column=0, padx=10, pady=5, sticky="e")
            ent.grid(row=i, column=1, padx=10, pady=5, sticky="we")

        frm.columnconfigure(1, weight=1)

        ctk.CTkButton(frm, text="Iniciar", command=self._iniciar_cronometro).grid(row=4, column=1, pady=10)
        ctk.CTkButton(frm, text="Ver Cronómetros Guardados", command=self._mostrar_guardados).grid(row=5, column=1, pady=5)

    def _iniciar_cronometro(self):
        nombre, tipo, comando = self.entrada_nombre.get().strip(), self.tipo_cronometro.get(), self.entrada_comando.get().strip()
        try:
            duracion = int(self.entrada_duracion.get()) * 60
            if not nombre: raise ValueError
        except:
            messagebox.showerror("Error", "Nombre y duración válidos requeridos.")
            return
        self.data.setdefault("cronometros", []).append({"nombre": nombre, "tipo": tipo, "duracion": duracion, "comando": comando})
        guardar_datos(self.data)

        task_id = f"crono_{nombre}"
        if tipo == "Pomodoro":
            thread_manager.run_in_thread(self._pomodoro_crono, task_id, nombre, duracion, comando)
        else:
            thread_manager.run_in_thread(self._simple_crono, task_id, nombre, duracion, comando)

    def _mostrar_guardados(self):
        c = self.data.get("cronometros", [])
        texto = "\n".join([f"{x['nombre']} - {x['tipo']} - {x['duracion']//60} min" for x in c])
        messagebox.showinfo("Cronómetros", texto or "No hay cronómetros guardados.")

    def _simple_crono(self, stop_event, nombre, duracion, comando):
        for _ in range(duracion):
            if stop_event.is_set(): return
            time.sleep(1)

        Notificador.enviar_titulo_mensaje("Alarma", f"Fin del cronómetro: {nombre}")
        if comando:
            try:
                import subprocess
                subprocess.run(comando, shell=True)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Error ejecutando: {e}"))

    def _pomodoro_crono(self, stop_event, nombre, duracion, comando):
        try:
            for i in range(4):
                if stop_event.is_set(): return
                Notificador.enviar_titulo_mensaje("Pomodoro", f"Inicio trabajo {i+1}")
                for _ in range(duracion):
                    if stop_event.is_set(): return
                    time.sleep(1)

                if stop_event.is_set(): return
                Notificador.enviar_titulo_mensaje("Descanso", "5 minutos de pausa")
                for _ in range(300):
                    if stop_event.is_set(): return
                    time.sleep(1)

            if stop_event.is_set(): return
            Notificador.enviar_titulo_mensaje("Pomodoro", f"Finalizado: {nombre}")
            if comando:
                import subprocess
                subprocess.run(comando, shell=True)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Error durante Pomodoro: {e}"))

    def _comidas_ui(self, frame):
        ctk.CTkLabel(frame, text="Planificación de Comidas (Markdown)").pack(pady=10)
        self.comidas_text = ctk.CTkTextbox(frame, height=400)
        self.comidas_text.pack(expand=True, fill='both', padx=20)
        if self.data.get("comidas"):
            self.comidas_text.insert('1.0', "\n".join(self.data["comidas"]))
        ctk.CTkButton(frame, text="Guardar Comidas", command=self._guardar_comidas).pack(pady=10)

    def _guardar_comidas(self):
        self.data["comidas"] = self.comidas_text.get('1.0', 'end').strip().split("\n")
        guardar_datos(self.data)
        messagebox.showinfo("Guardado", "Plan de comidas guardado.")

    def _compras_ui(self, frame):
        ctk.CTkLabel(frame, text="Lista de la Compra").pack(pady=10)
        self.compras_text = ctk.CTkTextbox(frame, height=400)
        self.compras_text.pack(expand=True, fill='both', padx=20)
        if self.data.get("compras"):
            self.compras_text.insert('1.0', "\n".join(self.data["compras"]))
        ctk.CTkButton(frame, text="Guardar Lista", command=self._guardar_compras).pack(pady=10)

    def _guardar_compras(self):
        self.data["compras"] = self.compras_text.get('1.0', 'end').strip().split("\n")
        guardar_datos(self.data)
        messagebox.showinfo("Guardado", "Lista de compras guardada.")

    def _habitos_ui(self, frame):
        ctk.CTkLabel(frame, text="Seguimiento de Hábitos y Rituales").pack(pady=10)
        frm = ctk.CTkFrame(frame)
        frm.pack(pady=10, padx=20, fill="x")
        self.habito_entry = ctk.CTkEntry(frm, width=300)
        self.habito_entry.pack(side="left", padx=10, pady=10)
        ctk.CTkButton(frm, text="Añadir", command=self._agregar_habito).pack(side="left", padx=10)

        self.habitos_list_frame = ctk.CTkScrollableFrame(frame)
        self.habitos_list_frame.pack(expand=True, fill="both", padx=20, pady=10)
        self._refrescar_habitos()

    def _agregar_habito(self):
        nuevo = self.habito_entry.get().strip()
        if nuevo:
            self.data.setdefault("habitos", []).append({"nombre": nuevo, "realizado": False})
            guardar_datos(self.data)
            self.habito_entry.delete(0, 'end')
            self._refrescar_habitos()

    def _refrescar_habitos(self):
        for widget in self.habitos_list_frame.winfo_children():
            widget.destroy()
        for i, h in enumerate(self.data.get("habitos", [])):
            var = tk.BooleanVar(value=h["realizado"])
            cb = ctk.CTkCheckBox(self.habitos_list_frame, text=h["nombre"], variable=var,
                                 command=lambda i=i, var=var: self._actualizar_habito(i, var))
            cb.pack(anchor='w', pady=2, padx=10)

    def _actualizar_habito(self, i, var):
        self.data["habitos"][i]["realizado"] = var.get()
        guardar_datos(self.data)
