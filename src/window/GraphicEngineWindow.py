import tkinter as tk
from tkinter import (
    END, Label, Entry, Button, scrolledtext, IntVar, Menu, StringVar,
    messagebox, Checkbutton, Frame, filedialog, BOTH, LEFT, X, RAISED,
    BooleanVar, BOTTOM, Text, Radiobutton, simpledialog
)
from tkinter import ttk
import threading
import subprocess
import psutil
import sys
import json
import time
from queue import Queue
import os
import genesis as gs  # Asegúrate de tener Genesis instalado y accesible

class GraphicEngineWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("RuneScript Physics Engine - Genesis v1.0")
        self.root.geometry("1200x800")

        # Initialize state variables
        self.is_processing = False
        self.ai_messages = Queue()
        self.current_scene_path = None

        # UI Variables
        self.last_command = StringVar()
        self.physics_state = StringVar(value="Idle")
        self.memory_usage = StringVar()
        self.ai_enabled = BooleanVar(value=True)

        # Initialize Genesis
        self.init_genesis()

        # Create the main UI layout
        self.create_menu()
        self.create_main_layout()

        # Start background tasks
        self.start_monitoring()

    def init_genesis(self):
        """Inicializa Genesis y crea una escena básica."""
        gs.init(backend=gs.cpu)  # Puedes cambiar a gs.cuda si tienes una GPU compatible

        # Crear la escena con el visor visible
        self.scene = gs.Scene(show_viewer=True)

        # Añadir un plano y un brazo Franka
        self.plane = self.scene.add_entity(gs.morphs.Plane())
        self.franka = self.scene.add_entity(
            gs.morphs.MJCF(file='xml/franka_emika_panda/panda.xml')
        )

        # Construir la escena
        self.scene.build()

        # Iniciar la simulación en un hilo separado
        self.simulation_thread = threading.Thread(target=self.run_simulation, daemon=True)
        self.simulation_thread.start()

    def run_simulation(self):
        """Ejecuta la simulación de Genesis."""
        try:
            for i in range(1000):
                self.scene.step()
                time.sleep(0.01)  # Controla la velocidad de simulación
        except Exception as e:
            self.log_message(f"Error in simulation: {e}")

    def create_menu(self):
        """Crea la barra de menú principal."""
        self.menu_bar = Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # Menú Archivo
        file_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Scene", command=self.new_scene)
        file_menu.add_command(label="Open Scene", command=self.open_scene)
        file_menu.add_command(label="Save Scene", command=self.save_scene)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)

        # Menú Editar
        edit_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.undo)
        edit_menu.add_command(label="Redo", command=self.redo)

        # Menú AI
        ai_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="AI", menu=ai_menu)
        ai_menu.add_checkbutton(label="Enable AI Assistant",
                                variable=self.ai_enabled)

    def create_main_layout(self):
        """Crea el layout principal de la ventana."""
        # Crear contenedor principal
        main_container = Frame(self.root)
        main_container.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # Crear panel izquierdo
        left_panel = Frame(main_container, relief=RAISED, borderwidth=1)
        left_panel.pack(side=LEFT, fill=BOTH, expand=False, padx=5)

        # Panel de jerarquía de la escena
        self.create_hierarchy_panel(left_panel)

        # Crear panel derecho
        right_panel = Frame(main_container)
        right_panel.pack(side=LEFT, fill=BOTH, expand=True, padx=5)

        # Crear viewport (Placeholder para integrar Genesis si es posible)
        self.create_viewport(right_panel)

        # Crear panel inferior
        bottom_panel = Frame(right_panel)
        bottom_panel.pack(side=BOTTOM, fill=X, expand=False, pady=5)

        # Panel de interacción con AI
        self.create_ai_panel(bottom_panel)

        # Crear barra de estado
        self.status_bar = Label(self.root, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=BOTTOM, fill=X)

    def create_hierarchy_panel(self, parent):
        """Crea el panel de jerarquía de la escena."""
        Label(parent, text="Scene Hierarchy",
              font=("Helvetica", 10, "bold")).pack(pady=5)

        # Usar Treeview para una mejor visualización de la jerarquía
        self.hierarchy_tree = ttk.Treeview(parent)
        self.hierarchy_tree.pack(fill=BOTH, expand=True, pady=5, padx=5)

        # Definir columnas
        self.hierarchy_tree["columns"] = ("Type")
        self.hierarchy_tree.column("#0", width=150, minwidth=150)
        self.hierarchy_tree.column("Type", width=100, minwidth=100)

        self.hierarchy_tree.heading("#0", text="Name", anchor=tk.W)
        self.hierarchy_tree.heading("Type", text="Type", anchor=tk.W)

        # Añadir elementos de ejemplo en la jerarquía
        scene_node = self.hierarchy_tree.insert("", "end", text="Scene", values=("Root"), open=True)
        camera_node = self.hierarchy_tree.insert(scene_node, "end", text="Camera", values=("Camera"))
        lights_node = self.hierarchy_tree.insert(scene_node, "end", text="Lights", values=("Group"), open=True)
        self.hierarchy_tree.insert(lights_node, "end", text="Main Light", values=("Light"))
        self.hierarchy_tree.insert(lights_node, "end", text="Ambient", values=("Light"))
        objects_node = self.hierarchy_tree.insert(scene_node, "end", text="Objects", values=("Group"), open=True)

        # Vincular clic derecho para el menú contextual
        self.hierarchy_tree.bind("<Button-3>", self.show_hierarchy_context_menu)

    def show_hierarchy_context_menu(self, event):
        """Muestra un menú contextual para el Treeview."""
        selected_item = self.hierarchy_tree.identify_row(event.y)
        if selected_item:
            self.hierarchy_tree.selection_set(selected_item)
            menu = Menu(self.root, tearoff=0)
            menu.add_command(label="Add Object", command=lambda: self.add_object_prompt(selected_item))
            menu.add_command(label="Delete Object", command=lambda: self.delete_object(selected_item))
            menu.add_command(label="Rename Object", command=lambda: self.rename_object(selected_item))
            menu.post(event.x_root, event.y_root)

    def add_object_prompt(self, parent_item):
        """Solicita al usuario añadir un nuevo objeto bajo el elemento seleccionado."""
        object_type = simpledialog.askstring("Add Object", "Enter object type (Sphere/Cube):")
        if object_type:
            object_type = object_type.capitalize()
            if object_type in ["Sphere", "Cube", "Plane", "Wall", "Zone", "Sensor"]:
                self.add_object(object_type)
            else:
                messagebox.showerror("Invalid Object", f"Unsupported object type: {object_type}")

    def delete_object(self, item):
        """Elimina el objeto seleccionado de la jerarquía."""
        object_name = self.hierarchy_tree.item(item, "text")
        confirm = messagebox.askyesno("Delete Object", f"Are you sure you want to delete '{object_name}'?")
        if confirm:
            self.hierarchy_tree.delete(item)
            self.log_message(f"Deleted object: {object_name}")
            # Aquí agregarías la lógica real para eliminar el objeto en Genesis

    def rename_object(self, item):
        """Renombra el objeto seleccionado en la jerarquía."""
        object_name = self.hierarchy_tree.item(item, "text")
        new_name = simpledialog.askstring("Rename Object", "Enter new name:", initialvalue=object_name)
        if new_name:
            self.hierarchy_tree.item(item, text=new_name)
            self.log_message(f"Renamed '{object_name}' to '{new_name}'")
            # Aquí agregarías la lógica real para renombrar el objeto en Genesis

    def create_viewport(self, parent):
        """Crea el viewport 3D."""
        viewport_frame = Frame(parent, relief=RAISED, borderwidth=1)
        viewport_frame.pack(fill=BOTH, expand=True, pady=5)

        Label(viewport_frame, text="Physics Viewport",
              font=("Helvetica", 12, "bold")).pack(pady=5)

        # Canvas para renderizado OpenGL o cualquier otra librería de renderizado
        # Aquí solo se usa un Canvas de Tkinter como placeholder
        self.viewport = tk.Canvas(viewport_frame, bg='black')
        self.viewport.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # Placeholder text
        self.viewport_text = self.viewport.create_text(
            300, 200, text="3D Viewport Placeholder",
            fill="white", font=("Helvetica", 14)
        )

        # Aquí deberías integrar el renderizado de Genesis en el canvas.
        # Esto puede requerir una implementación personalizada con OpenGL o una biblioteca compatible.

    def create_ai_panel(self, parent):
        """Crea el panel de interacción con AI."""
        ai_frame = Frame(parent, relief=RAISED, borderwidth=1)
        ai_frame.pack(fill=X, expand=False, pady=5)

        # Área de texto para salida
        self.output_text = scrolledtext.ScrolledText(
            ai_frame, height=10, width=50, state='disabled', wrap='word'
        )
        self.output_text.pack(fill=X, expand=True, padx=5, pady=5)

        # Crear marco para entrada
        input_frame = Frame(ai_frame)
        input_frame.pack(fill=X, padx=5, pady=5)

        # Campo de entrada de prompt
        self.prompt_input = Entry(input_frame)
        self.prompt_input.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))
        self.prompt_input.bind('<Return>', self.process_prompt)

        # Botón de enviar
        self.send_button = Button(
            input_frame, text="Send", command=self.process_prompt
        )
        self.send_button.pack(side=LEFT)

    def process_prompt(self, event=None):
        """Procesa el prompt del usuario."""
        if self.is_processing:
            messagebox.showwarning("Processing", "Please wait until the current command is processed.")
            return

        prompt = self.prompt_input.get().strip()
        if not prompt:
            messagebox.showwarning("Input Error", "Please enter a command.")
            return

        self.prompt_input.delete(0, END)
        self.is_processing = True
        self.update_ui_state()

        # Log del prompt del usuario
        self.log_message(f"User: {prompt}")

        # Iniciar procesamiento en un hilo separado
        threading.Thread(
            target=self.run_ai_processing,
            args=(prompt,),
            daemon=True
        ).start()

    def run_ai_processing(self, prompt):
        """Ejecuta el procesamiento de AI en un hilo separado."""
        try:
            if self.ai_enabled.get():
                ai_response = process_prompt_with_ai(prompt)
                if ai_response:
                    # Log de la respuesta
                    self.log_message(f"AI: {ai_response}")
                    # Opcional: ejecutar comandos de la respuesta de AI
                    self.execute_ai_commands(ai_response)
                else:
                    self.log_message("AI: No response received.")
            else:
                self.log_message("AI: Assistant is disabled.")
        except Exception as e:
            self.log_message(f"Error: {str(e)}")
        finally:
            self.is_processing = False
            self.root.after(0, self.update_ui_state)

    def execute_ai_commands(self, response):
        """Ejecuta los comandos contenidos en la respuesta de AI."""
        # Implementar un parser simple de comandos
        # Por ejemplo, si AI responde con "create_sphere r=2; create_cube s=1", separar por ';'
        commands = response.split(';')  # Asumiendo que múltiples comandos están separados por ';'
        for cmd in commands:
            cmd = cmd.strip()
            if cmd:
                self.process_command(cmd)

    def process_command(self, command):
        """Procesa un único comando."""
        # Parser simple de comandos
        parts = command.split()
        if not parts:
            return
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        if cmd == "create_sphere":
            radius = 1.0  # Radio por defecto
            for arg in args:
                if arg.startswith("r="):
                    try:
                        radius = float(arg.split("=")[1])
                    except ValueError:
                        self.log_message("AI: Invalid radius value.")
                        return
            self.add_object("Sphere", radius=radius)
        elif cmd == "create_cube":
            size = 1.0  # Tamaño por defecto
            for arg in args:
                if arg.startswith("s="):
                    try:
                        size = float(arg.split("=")[1])
                    except ValueError:
                        self.log_message("AI: Invalid size value.")
                        return
            self.add_object("Cube", size=size)
        else:
            self.log_message(f"AI: Unknown command '{cmd}'.")

    def add_object(self, object_type, **kwargs):
        """
        Añade un objeto a la escena basado en el tipo y parámetros.
        Este es un placeholder para la integración real con Genesis.
        """
        # Integrar la lógica real para agregar objetos a Genesis
        # Por ejemplo:
        # if object_type == "Sphere":
        #     self.scene.add_entity(gs.morphs.Sphere(radius=kwargs.get('radius', 1.0)))
        # elif object_type == "Cube":
        #     self.scene.add_entity(gs.morphs.Box(size=kwargs.get('size', 1.0)))
        # ...

        # Simular la adición de objetos
        if object_type == "Sphere":
            radius = kwargs.get('radius', 1.0)
            self.log_message(f"AI: Creating a sphere with radius {radius}.")
            # Aquí agregarías la lógica real para crear una esfera en Genesis
            # Ejemplo:
            # sphere = self.scene.add_entity(gs.morphs.Sphere(radius=radius))
        elif object_type == "Cube":
            size = kwargs.get('size', 1.0)
            self.log_message(f"AI: Creating a cube with size {size}.")
            # Aquí agregarías la lógica real para crear un cubo en Genesis
            # Ejemplo:
            # cube = self.scene.add_entity(gs.morphs.Box(size=size))
        else:
            self.log_message(f"AI: Unsupported object type '{object_type}'.")

        # Actualizar la jerarquía
        self.update_hierarchy(object_type)

    def update_hierarchy(self, object_type):
        """Actualiza la visualización de la jerarquía de la escena."""
        # Añade el nuevo objeto al Treeview
        objects_node = self.find_node("Objects")
        if objects_node:
            new_object_text = f"New {object_type}"
            self.hierarchy_tree.insert(objects_node, "end", text=new_object_text, values=(object_type,))
            self.log_message(f"Added '{new_object_text}' to 'Objects' node.")
        else:
            self.log_message("AI: 'Objects' node not found in hierarchy.")

    def find_node(self, node_name, parent=''):
        """Encuentra un nodo en el Treeview por su nombre de forma recursiva."""
        children = self.hierarchy_tree.get_children(parent)
        for child in children:
            if self.hierarchy_tree.item(child, "text") == node_name:
                return child
            # Buscar recursivamente en los nodos hijos
            result = self.find_node(node_name, child)
            if result:
                return result
        return None

    def log_message(self, message):
        """Registra un mensaje en el área de texto de salida."""
        def _log():
            self.output_text.config(state='normal')
            self.output_text.insert(END, message + "\n")
            self.output_text.see(END)
            self.output_text.config(state='disabled')

        self.root.after(0, _log)

    def update_ui_state(self):
        """Actualiza el estado de la UI basado en el estado de procesamiento."""
        state = 'disabled' if self.is_processing else 'normal'
        self.prompt_input.config(state=state)
        self.send_button.config(state=state)

    def start_monitoring(self):
        """Inicia la monitorización en segundo plano."""
        self._running = True
        threading.Thread(target=self.monitor_resources, daemon=True).start()

    def monitor_resources(self):
        """Monitorea los recursos del sistema y actualiza la barra de estado."""
        while self._running:
            try:
                mem = psutil.virtual_memory()
                usage = f"Memory Usage: {mem.percent}%"
                self.memory_usage.set(usage)
                # Actualizar la barra de estado en la interfaz
                last_cmd = self.last_command.get() if self.last_command.get() else "N/A"
                physics_state = self.physics_state.get()
                mem_usage = self.memory_usage.get()
                self.update_memory_stack(last_cmd, physics_state, mem_usage)
                time.sleep(1)
            except Exception as e:
                self.log_message(f"Error monitoring resources: {e}")

    def update_memory_stack(self, last_command, physics_state, memory_usage):
        """Actualiza la barra de estado con la información proporcionada."""
        status_text = f"Last Command: {last_command} | Physics State: {physics_state} | {memory_usage}"
        self.root.after(0, lambda: self.status_bar.config(text=status_text))

    def play_scene(self):
        """Inicia la reproducción de la escena."""
        self.physics_state.set("Playing")
        self.log_message("Scene playback started.")
        # Aquí agregarías la lógica real para iniciar la simulación en Genesis

    def pause_scene(self):
        """Pausa la reproducción de la escena."""
        self.physics_state.set("Paused")
        self.log_message("Scene playback paused.")
        # Aquí agregarías la lógica real para pausar la simulación en Genesis

    def stop_scene(self):
        """Detiene la reproducción de la escena."""
        self.physics_state.set("Stopped")
        self.log_message("Scene playback stopped.")
        # Aquí agregarías la lógica real para detener la simulación en Genesis

    def new_scene(self):
        """Crea una nueva escena."""
        if messagebox.askyesno("New Scene",
                               "Are you sure you want to create a new scene? Unsaved changes will be lost."):
            self.current_scene_path = None
            self.log_message("Created a new scene.")
            self.hierarchy_tree.delete(*self.hierarchy_tree.get_children())
            # Re-insertar los nodos raíz
            scene_node = self.hierarchy_tree.insert("", "end", text="Scene", values=("Root"), open=True)
            camera_node = self.hierarchy_tree.insert(scene_node, "end", text="Camera", values=("Camera"))
            lights_node = self.hierarchy_tree.insert(scene_node, "end", text="Lights", values=("Group"), open=True)
            self.hierarchy_tree.insert(lights_node, "end", text="Main Light", values=("Light"))
            self.hierarchy_tree.insert(lights_node, "end", text="Ambient", values=("Light"))
            objects_node = self.hierarchy_tree.insert(scene_node, "end", text="Objects", values=("Group"), open=True)
            # Resetear el estado de física
            self.physics_state.set("Idle")
            self.update_memory_stack("New Scene", self.physics_state.get(), self.memory_usage.get())

    def open_scene(self):
        """Abre una escena existente."""
        file_path = filedialog.askopenfilename(
            title="Open Scene",
            filetypes=[("Scene Files", "*.scene"), ("All Files", "*.*")]
        )
        if file_path:
            self.current_scene_path = file_path
            self.log_message(f"Opened scene: {file_path}")
            # Aquí agregarías la lógica real para cargar la escena en Genesis
            # Por ejemplo:
            # self.scene.load(file_path)
            # Actualizar la jerarquía según el contenido de la escena
            # ...

    def save_scene(self):
        """Guarda la escena actual."""
        if not self.current_scene_path:
            file_path = filedialog.asksaveasfilename(
                title="Save Scene",
                defaultextension=".scene",
                filetypes=[("Scene Files", "*.scene"), ("All Files", "*.*")]
            )
            if file_path:
                self.current_scene_path = file_path
            else:
                return  # Cancelado

        if self.current_scene_path:
            self.log_message(f"Saved scene to: {self.current_scene_path}")
            # Aquí agregarías la lógica real para guardar la escena en Genesis
            # Por ejemplo:
            # self.scene.save(self.current_scene_path)
            # ...

    def undo(self):
        """Deshace la última acción."""
        self.log_message("Undo last action.")
        # Implementa la lógica de deshacer aquí
        # Por ejemplo:
        # self.scene.undo()

    def redo(self):
        """Rehace la última acción deshecha."""
        self.log_message("Redo last action.")
        # Implementa la lógica de rehacer aquí
        # Por ejemplo:
        # self.scene.redo()

    def on_closing(self):
        """Maneja el cierre de la ventana."""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self._running = False
            self.root.quit()

    def run(self):
        """Ejecuta el bucle principal de la aplicación."""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

def process_prompt_with_ai(combined_input):
    """
    Interactúa con el asistente AI ejecutando ai_assistant.py con la entrada proporcionada.
    """
    ai_script_path = "src/models/ai_assistant.py"
    python_executable = 'python'  # Ajusta esta ruta si es necesario

    # Verificar si el script de IA existe
    if not os.path.isfile(ai_script_path):
        print(f"AI Assistant script not found at: {ai_script_path}")
        return "AI Assistant script not found."

    command = [python_executable, ai_script_path, combined_input]

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )

        ai_response, error = process.communicate()

        if error:
            print(f"AI Assistant Error: {error}")
            return f"AI Assistant Error: {error}"

        return ai_response.strip()
    except Exception as e:
        print(f"Error processing prompt with AI: {e}")
        return f"Error processing prompt with AI: {e}"

def main():
    root = tk.Tk()
    app = GraphicEngineWindow(root)
    app.run()

if __name__ == "__main__":
    main()
