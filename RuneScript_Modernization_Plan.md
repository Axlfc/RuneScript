# Plan de Modernización Visual - RuneScript IDE

Este documento presenta un plan detallado para modernizar la interfaz de usuario (UI) y la experiencia de usuario (UX) del IDE RuneScript, migrando de Tkinter estándar a CustomTkinter para lograr una estética más moderna, limpia y profesional.

## 1. Análisis del Estado Actual

- **Framework Actual:** La UI está construida con **Tkinter** y utiliza la librería **ttkbootstrap** para la gestión de temas.
- **Sistema de Temas:** La configuración del tema se gestiona a través del archivo `data/user_config.json` (ej. `"theme": "cosmo"`) y se aplica en `src/views/tk_utils.py` usando `style.theme_use()`.
- **Fortalezas:** Ya existe una base funcional para la gestión de temas y una estructura de aplicación que separa vistas, controladores y modelos.
- **Puntos Débiles Visuales:**
    - **Inconsistencia:** Hay una mezcla de componentes estilizados por ttkbootstrap (como la `Treeview`) y componentes de Tkinter con estilos manuales o hardcodeados (ej. `script_text` en `app_layers.py` con `bg="#1f1f1f"`).
    - **Estética General:** A pesar de ttkbootstrap, muchos componentes retienen un aspecto anticuado que no compite con IDEs modernos.
    - **Falta de Refinamiento:** Ausencia de elementos de diseño modernos como espaciado consistente, iconografía moderna, bordes redondeados y efectos sutiles (hover, focus).

## 2. Evaluación de Alternativas

Se evaluaron tres frameworks principales basándose en los requisitos clave (migración gradual, compatibilidad de temas, DX, rendimiento y estética).

### CustomTkinter
- **Conclusión:** La opción **recomendada**.
- **Pros:** Permite una migración gradual y coexistencia con Tkinter, tiene una curva de aprendizaje mínima, y su sistema de temas basado en JSON es fácilmente adaptable desde la configuración actual. Ofrece un excelente equilibrio entre mejora visual y bajo riesgo.

### Flet
- **Conclusión:** Descartado.
- **Pros:** Estética moderna superior gracias al motor de Flutter.
- **Contras:** Requiere una reescritura completa de la UI, lo que viola el requisito de una migración "paso a paso".

### PySide6 (Qt for Python)
- **Conclusión:** Descartado para este enfoque.
- **Pros:** El framework más potente y capaz, ideal para crear interfaces de nivel profesional.
- **Contras:** También requiere una reescritura total y presenta una curva de aprendizaje mucho más pronunciada, contradiciendo el deseo de un proceso "tranquilo y paso a paso".

## 3. Recomendación Final

La recomendación inequívoca es adoptar **CustomTkinter**. Es la única opción que cumple con los requisitos críticos del proyecto: permite una **migración incremental y de bajo riesgo**, facilita la **adaptación del sistema de temas existente** y requiere un **esfuerzo de aprendizaje mínimo**. Proporciona el camino más rápido y seguro para lograr un impacto visual significativo sin la necesidad de reescribir la aplicación desde cero.

## 4. Roadmap de Implementación

Este roadmap está diseñado para ser incremental, priorizando el impacto visual y manteniendo la aplicación funcional en todo momento.

### Fase 1: Preparación y Setup
1.  **Instalar CustomTkinter:** Añadir `customtkinter` al archivo `requirements.txt` y ejecutar `pip install -r requirements.txt`.
2.  **Crear Archivo de Tema:** Crear un nuevo archivo de tema JSON para CustomTkinter, por ejemplo, `data/themes/runescript_dark.json`. Este archivo contendrá la paleta de colores inspirada en VS Code. Se puede empezar con una estructura básica (ver sección de código de ejemplo).
3.  **Integración Inicial:** Modificar `src/views/tk_utils.py` para:
    - Importar `customtkinter`.
    - Configurar el modo de apariencia inicial (`customtkinter.set_appearance_mode("dark")`).
    - **Opcional:** Cargar el tema personalizado desde el archivo JSON con `customtkinter.set_default_color_theme("path/to/your/theme.json")`.
4.  **Entorno de Pruebas:** No se necesita un entorno paralelo. La migración se hará componente por componente en una rama de desarrollo (ej. `feature/ui-modernization`).

### Fase 2: Componentes Core (Migración Gradual)

El objetivo es reemplazar los widgets de Tkinter (`tk.*`, `ttk.*`) por sus equivalentes de CustomTkinter (`ctk.*`). Se prioriza por impacto visual.

1.  **Ventana Principal y Frames:**
    - Reemplazar `root = style.master` (`tk.Tk`) por `root = customtkinter.CTk()`.
    - Reemplazar todos los `tk.Frame` por `customtkinter.CTkFrame`. Esto establecerá inmediatamente el color de fondo correcto del tema y mejorará el espaciado.
    - **Componentes:** `toolbar`, `frm`, `script_frm`, `content_frm`, etc.

2.  **Botones y Entradas de Texto:**
    - Reemplazar `tk.Button` por `customtkinter.CTkButton`. Esto modernizará instantáneamente todos los botones.
    - Reemplazar `tk.Entry` por `customtkinter.CTkEntry`.
    - **Componentes:** Todos los botones de la barra de herramientas y otras ventanas de diálogo.

3.  **Editor de Texto Principal (`script_text`):**
    - `scrolledtext.ScrolledText` es un widget complejo. CustomTkinter tiene `CTkTextbox`.
    - **Acción:** Reemplazar `scrolledtext.ScrolledText` en `tk_utils.py` por `customtkinter.CTkTextbox`.
    - **Beneficio Inmediato:** Se eliminarán los colores hardcodeados (`bg="#1f1f1f"`) y el textbox adoptará automáticamente los colores del tema, las fuentes y los bordes redondeados.

4.  **Paneles Laterales (File Explorer):**
    - El `ttk.Treeview` es el componente más complejo de reemplazar, ya que CustomTkinter no tiene un widget de árbol nativo.
    - **Estrategia Mixta:** Inicialmente, **mantener el `ttk.Treeview`** pero estilizar su contenedor (`CTkFrame`) y las barras de scroll (`CTkScrollbar`). Se puede investigar librerías de terceros compatibles o, a largo plazo, construir un widget de árbol con frames y botones de CustomTkinter.

5.  **Menús:**
    - El `tk.Menu` es parte de la ventana nativa. Se puede mantener el menú de la barra superior, pero cualquier menú contextual o de "hamburguesa" dentro de la UI debería ser recreado con botones o frames de CustomTkinter.

### Fase 3: Sistema de Temas
1.  **Adaptar `parameters.py`:**
    - Modificar `load_theme_setting()` para que, en lugar de un nombre de tema de ttkbootstrap, lea una configuración que pueda ser `"light"`, `"dark"`, o `"system"`.
    - Añadir una nueva función para obtener la ruta al archivo de tema personalizado JSON si se desea.
2.  **Implementar Switch de Tema:**
    - Crear una función en `menu_functions.py` que llame a `customtkinter.set_appearance_mode(new_mode)`.
    - Añadir una opción en el menú de la UI (ej. "Apariencia > Claro/Oscuro") que ejecute esta función.
3.  **Consolidar Colores:**
    - Auditar el código para encontrar y eliminar cualquier color hardcodeado que quede. Todos los colores deben provenir del tema.

### Fase 4: Testing y Refinamiento
1.  **Plan de Testing:**
    - **Pruebas de Regresión Funcional:** Verificar que toda la funcionalidad existente (ejecutar scripts, git, AI) sigue operativa después de reemplazar cada componente.
    - **Pruebas Visuales:** Comprobar la consistencia visual en Windows y Linux. Validar que los temas claro y oscuro se aplican correctamente en todos los componentes.
    - **Pruebas de Rendimiento:** Asegurarse de que la fluidez del editor y la respuesta de la aplicación no se han degradado.
2.  **Checkpoints de Validación:** Revisar el progreso visual después de migrar cada grupo de componentes clave (frames, botones, editor).
3.  **Rollback Strategy:** Gracias a Git y la estrategia de migración gradual, el riesgo es bajo. Si un componente migrado causa un problema crítico, se puede revertir el cambio de ese componente específico desde el historial de commits sin afectar al resto de la migración.

## 5. Design Guidelines
- **Tipografía:**
    - **Recomendación:** `JetBrains Mono` o `Fira Code`. Son modernas, legibles y soportan ligaduras de programación.
    - **Implementación:** Configurar la fuente por defecto en el widget `CTkFont` y aplicarla globalmente.
- **Iconografía:**
    - **Recomendación:** Usar un pack de iconos SVG/PNG como **Feather Icons** o **Material Design Icons**.
    - **Implementación:** Cargar los iconos con `PIL` (`ImageTk`) y asignarlos a los `CTkButton` y `CTkLabel`. CustomTkinter tiene un buen soporte para imágenes.
- **Espaciado (Padding/Margin):**
    - Utilizar las opciones `padx` y `pady` de manera consistente en los métodos `.grid()` o `.pack()`. Se recomienda un espaciado base de `8` o `10` píxeles y usar múltiplos (ej. `padx=10`, `pady=(10, 0)`).
- **Paleta de Colores (Ejemplo Tema Oscuro - `runescript_dark.json`):**
    ```json
    {
      "CTk": {
        "fg_color": ["#2B2B2B", "#3C3F41"]
      },
      "CTkFrame": {
        "fg_color": ["#2B2B2B", "#3C3F41"],
        "border_color": ["#4E5254", "#4E5254"]
      },
      "CTkButton": {
        "fg_color": ["#4E5254", "#4E5254"],
        "hover_color": ["#5A5E60", "#5A5E60"],
        "text_color": ["#FFFFFF", "#FFFFFF"]
      },
      "CTkEntry": {
        "fg_color": ["#3C3F41", "#3C3F41"],
        "border_color": ["#4E5254", "#4E5254"],
        "text_color": ["#FFFFFF", "#FFFFFF"]
      },
      "CTkTextbox": {
        "fg_color": ["#313335", "#313335"],
        "text_color": ["#D3D3D3", "#D3D3D3"]
      }
    }
    ```

## 6. Código de Ejemplo

### Ejemplo 1: Migración de la Ventana Principal y un Botón

**Código Actual (simplificado de `tk_utils.py`):**
```python
# import tkinter as tk
# from ttkbootstrap import Style

# style = Style(theme="cosmo")
# root = style.master
#
# frm = tk.Frame(root)
# frm.pack(pady=10)
#
# my_button = tk.Button(frm, text="Ejecutar")
# my_button.pack()
```

**Código Migrado a CustomTkinter:**
```python
import customtkinter

# 1. Set appearance y (opcional) tema
customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("path/to/runescript_dark.json")

# 2. Reemplazar Tk por CTk
root = customtkinter.CTk()

# 3. Reemplazar Frame por CTkFrame
frm = customtkinter.CTkFrame(root, corner_radius=10) # Añade bordes redondeados
frm.pack(pady=20, padx=20, fill="both", expand=True)

# 4. Reemplazar Button por CTkButton
my_button = customtkinter.CTkButton(frm, text="Ejecutar")
my_button.pack(pady=10)
```

### Ejemplo 2: Adaptación del Sistema de Temas

**Código Actual (`parameters.py`):**
```python
# def load_theme_setting():
#     theme = read_config_parameter("options.theme_appearance.theme")
#     if theme is None:
#         theme = "cosmo" # Tema de ttkbootstrap
#     return theme
```

**Código Adaptado (`parameters.py`):**
```python
def load_appearance_mode():
    # El config ahora guarda "light", "dark", o "system"
    mode = read_config_parameter("options.theme_appearance.mode")
    if mode not in ["light", "dark", "system"]:
        mode = "dark" # Default mode
    return mode

# En tk_utils.py o donde se inicializa la app
# import customtkinter
# from src.controllers.parameters import load_appearance_mode

# mode = load_appearance_mode()
# customtkinter.set_appearance_mode(mode)
```

## 7. Recursos y Referencias
- **Documentación Oficial de CustomTkinter:** [https://customtkinter.tomschimansky.com/](https://customtkinter.tomschimansky.com/)
- **Repositorio de GitHub de CustomTkinter:** [https://github.com/TomSchimansky/CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) (muy útil para ver ejemplos y issues)
- **Iconos Feather Icons:** [https://feathericons.com/](https://feathericons.com/)
- **Iconos Material Design:** [https://fonts.google.com/icons](https://fonts.google.com/icons)
- **Tipografía JetBrains Mono:** [https://www.jetbrains.com/lp/mono/](https://www.jetbrains.com/lp/mono/)
