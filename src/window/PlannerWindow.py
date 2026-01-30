import tkinter as tk
from tkinter import ttk, messagebox
import time
import json
import threading
import os
from src.utils.thread_manager import thread_manager

from src.window.Notificador import Notificador

CONFIG_FILE = "planner_config.json"


def cargar_datos():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"rutina": [], "compras": [], "comidas": [], "cronometros": [], "habitos": []}


def guardar_datos(data):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo guardar el archivo: {e}")


class PlannerWindow(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.title("Productivity Planner")
        self.geometry("1000x650")
        self.configure(fg_color='#1e1e1e')
        self.data = cargar_datos()

        self._estilos()
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(expand=1, fill='both')
        self._tabs()

    def _estilos(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook", background="#2d2d2d")
        style.configure("TFrame", background="#2d2d2d")
        style.configure("TLabel", background="#2d2d2d", foreground="white")
        style.configure("TButton", padding=6)

    def _tabs(self):
        self.frames = {}
        sections = {
            "Rutina Diaria": self._rutina_ui,
            "Alarmas y Acciones": self._cronometros_ui,
            "Plan de Comidas": self._comidas_ui,
            "Lista de Compras": self._compras_ui,
            "HÃ¡bitos y Rituales": self._habitos_ui
        }
        for nombre, metodo in sections.items():
            frame = ttk.Frame(self.tabs)
            self.tabs.add(frame, text=nombre)
            self.frames[nombre] = frame
            metodo(frame)

    def _rutina_ui(self, frame):
        ttk.Label(frame, text="Rutina Diaria Personalizada").pack(pady=10)
        self.rutina_text = tk.Text(frame, height=25, fg_color="#111", text_color="white")
        self.rutina_text.pack(expand=True, fill='both', padx=20)
        if self.data.get("rutina"):
            self.rutina_text.insert('1.0', "\n".join(self.data["rutina"]))
        ttk.Button(frame, text="Guardar Rutina", command=self._guardar_rutina).pack(pady=10)

    def _guardar_rutina(self):
        texto = self.rutina_text.get('1.0', 'end').strip()
        self.data["rutina"] = texto.split("\n")
        guardar_datos(self.data)
        messagebox.showinfo("Guardado", "Rutina guardada correctamente.")

    def _cronometros_ui(self, frame):
        ttk.Label(frame, text="Crear CronÃ³metro con AcciÃ³n").pack(pady=10)
        frm = ttk.Frame(frame)
        frm.pack(pady=10)

        self.entrada_nombre = ttk.Entry(frm)
        self.entrada_duracion = ttk.Entry(frm)
        self.tipo_cronometro = ttk.Combobox(frm, values=["Normal", "Pomodoro"])
        self.tipo_cronometro.set("Normal")
        self.entrada_comando = ttk.Entry(frm)

        etiquetas = ["Nombre:", "DuraciÃ³n (min):", "Tipo:", "Comando opcional:"]
        entradas = [self.entrada_nombre, self.entrada_duracion, self.tipo_cronometro, self.entrada_comando]
        for i, (et, ent) in enumerate(zip(etiquetas, entradas)):
            ttk.Label(frm, text=et).grid(row=i, column=0)
            ent.grid(row=i, column=1)

        ttk.Button(frm, text="Iniciar", command=self._iniciar_cronometro).grid(row=4, column=1, pady=10)
        ttk.Button(frm, text="Ver CronÃ³metros Guardados", command=self._mostrar_guardados).grid(row=5, column=1)

    def _iniciar_cronometro(self):
        nombre, tipo, comando = self.entrada_nombre.get().strip(), self.tipo_cronometro.get(), self.entrada_comando.get().strip()
        try:
            duracion = int(self.entrada_duracion.get()) * 60
            if not nombre: raise ValueError
        except:
            messagebox.showerror("Error", "Nombre y duraciÃ³n vÃ¡lidos requeridos.")
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
        messagebox.showinfo("CronÃ³metros", texto or "No hay cronÃ³metros guardados.")

    def _simple_crono(self, stop_event, nombre, duracion, comando):
        for _ in range(duracion):
            if stop_event.is_set(): return
            time.sleep(1)

        Notificador.enviar_titulo_mensaje("Alarma", f"Fin del cronÃ³metro: {nombre}")
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
        ttk.Label(frame, text="PlanificaciÃ³n de Comidas (Markdown)").pack(pady=10)
        self.comidas_text = tk.Text(frame, height=25, fg_color="#111", text_color="white")
        self.comidas_text.pack(expand=True, fill='both', padx=20)
        if self.data.get("comidas"):
            self.comidas_text.insert('1.0', "\n".join(self.data["comidas"]))
        ttk.Button(frame, text="Guardar Comidas", command=self._guardar_comidas).pack(pady=10)

    def _guardar_comidas(self):
        self.data["comidas"] = self.comidas_text.get('1.0', 'end').strip().split("\n")
        guardar_datos(self.data)
        messagebox.showinfo("Guardado", "Plan de comidas guardado.")

    def _compras_ui(self, frame):
        ttk.Label(frame, text="Lista de la Compra").pack(pady=10)
        self.compras_text = tk.Text(frame, height=25, fg_color="#111", text_color="white")
        self.compras_text.pack(expand=True, fill='both', padx=20)
        if self.data.get("compras"):
            self.compras_text.insert('1.0', "\n".join(self.data["compras"]))
        ttk.Button(frame, text="Guardar Lista", command=self._guardar_compras).pack(pady=10)

    def _guardar_compras(self):
        self.data["compras"] = self.compras_text.get('1.0', 'end').strip().split("\n")
        guardar_datos(self.data)
        messagebox.showinfo("Guardado", "Lista de compras guardada.")

    def _habitos_ui(self, frame):
        ttk.Label(frame, text="Seguimiento de HÃ¡bitos y Rituales").pack(pady=10)
        frm = ttk.Frame(frame)
        frm.pack(pady=10)
        self.habito_entry = ttk.Entry(frm, width=30)
        self.habito_entry.grid(row=0, column=0, padx=5)
        ttk.Button(frm, text="AÃ±adir", command=self._agregar_habito).grid(row=0, column=1)
        self._refrescar_habitos(frame)

    def _agregar_habito(self):
        nuevo = self.habito_entry.get().strip()
        if nuevo:
            self.data.setdefault("habitos", []).append({"nombre": nuevo, "realizado": False})
            guardar_datos(self.data)
            self.habito_entry.delete(0, 'end')
            self._refrescar_habitos(self.frames["HÃ¡bitos y Rituales"])

    def _refrescar_habitos(self, frame):
        for widget in frame.winfo_children():
            if isinstance(widget, ttk.Checkbutton):
                widget.destroy()
        for i, h in enumerate(self.data.get("habitos", [])):
            var = tk.BooleanVar(value=h["realizado"])
            cb = ttk.Checkbutton(frame, text=h["nombre"], variable=var,
                                 command=lambda i=i, var=var: self._actualizar_habito(i, var))
            cb.pack(anchor='w')

    def _actualizar_habito(self, i, var):
        self.data["habitos"][i]["realizado"] = var.get()
        guardar_datos(self.data)

