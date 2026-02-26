# DOCUMENTO DE DISEÑO: nIA Autonomous Engine (RuneScript Blueprint)
**Versión:** 1.0 (Senior Architectural Spec)
**Objetivo:** Descripción detallada del comportamiento del sistema para implementación por agentes.

---

## 1. MODO: PARLAR (Descubrimiento y Alineación Estratégica)
*El diálogo no es una charla; es una fase de ingeniería de requerimientos.*

### Comportamiento Core:
- **Elicitación Proactiva:** nIA no acepta prompts pasivamente. Realiza una "Exploración de Contexto" antes de proponer la especificación. Analiza archivos existentes y estructura previa para asegurar continuidad.
- **Sanitización de Intención:** Antes de procesar, limpia el prompt de ambigüedades. Si detecta requerimientos contradictorios (ej: "app web sin HTML"), genera un aviso de inconsistencia.
- **Detección de Tech-Stack:** No asume tecnologías. Utiliza un `TechStackDetector` basado en heurística y patrones de prompt para asignar reglas de calidad específicas (ej: reglas de Python vs rules de Frontend).

### Implicaciones e Invariantes:
- **Invariante de Contexto:** nIA nunca opera en un vacío. Si no hay archivos, inicializa un repositorio Git de inmediato.
- **Implicación de Seguridad:** La fase de "Parlar" ya incluye una validación de seguridad para prevenir inyecciones de prompts maliciosos que intenten escapar del sandbox.

---

## 2. MODO: PLANEJAR (Estrategia y Auditoría de Planificación)
*La planificación es una simulación de la ejecución.*

### Comportamiento Core:
- **Generación de SPEC.md (La Única Verdad):** Traduce el prompt en una especificación técnica formal. Si no está en el `SPEC.md`, no existe para el agente.
- **Planificación Ponderada:** El `PlanGenerator` asigna una puntuación de complejidad al proyecto. Esta puntuación determina:
    - El número de tareas permitidas.
    - El nivel de detalle de cada tarea.
    - La tolerancia a fallos en el ciclo TDD.
- **Recursive Critique (El Revisor):** Implementa un bucle de "Self-Correction". Un proceso de IA revisa el plan generado contra el `SPEC.md`. Si el plan omite requerimientos o no es testeable, es rechazado con una crítica detallada y regenerado.

### Implicaciones e Invariantes:
- **Invariante de Testeabilidad:** Cada tarea del plan DEBE tener un criterio de validación técnica (ej: "Debe existir un test en `tests/`").
- **Implicación de Modularidad:** El plan se divide en fases (Setup, Core, Features, UI). nIA no permite saltar a "Features" sin completar el "Core".

---

## 3. MODO: AGENT (Ejecución Autónoma y Resiliencia Extrema)
*El agente es un artesano del código, no un generador de texto.*

### Comportamiento Core (Ciclo TDD-Quality):
1. **Fase RED (Test Failing):** nIA genera un test unitario/funcional basado en la tarea actual. El test *debe* fallar inicialmente. Si pasa prematuramente, nIA detecta una anomalía y revisa si el test es válido o si la funcionalidad ya existía.
2. **Fase GREEN (Implementación Real):** Escribe el código de implementación. Aquí entra la **Muralla de Calidad**:
    - **Rechazo de Placeholders:** Si el código contiene `...`, `TODO`, o `/* rest of code */`, el sistema lo rechaza y obliga a una re-generación total. nIA no "rellena huecos", construye componentes completos.
    - **Enforcement de Volumen:** Para evitar stubs, se exigen mínimos de líneas de código útiles por tecnología.
3. **Fase REFACTOR (Integridad):** Tras pasar el test, ejecuta TODA la suite de tests del proyecto para asegurar que no hay regresiones.

### Estrategias de Resiliencia (Self-Healing):
- **Smart Rollback (Git-Based):** En caso de fallo persistente, nIA utiliza Git para volver al último estado conocido como "estable". No borra el trabajo al azar; sabe qué archivos fueron añadidos y cuáles modificados. Se utiliza `git checkout --force` como fail-safe en sistemas con bloqueos de archivos (Windows).
- **Auto-Corrección Sintáctica y Lógica de Tests:** nIA valida el AST (Abstract Syntax Tree). Además, inyecta correcciones automáticas para errores comunes de LLMs:
    - Uso de `requests.get` en archivos locales (lo cambia por `open()`).
    - Rutas relativas incorrectas en tests (las normaliza a la raíz del proyecto).
    - Accesos inseguros en BeautifulSoup (fuerza el uso de `.get()` para evitar `KeyError`).
- **Multi-Model Fallback:** Si el modelo principal (Gemini) agota su quota o da errores 503, nIA conmuta el contexto completo a Claude-3 o GPT-4o para no detener el flujo de trabajo.

### Implicaciones e Invariantes:
- **Invariante de IterationState (Antideriva):** nIA mantiene un "Estado de Iteración" que bloquea el archivo de test una vez generado. Durante los reintentos de una misma tarea, el agente tiene prohibido modificar el test para "ajustarlo" a su fallo; debe ajustar la implementación al test.
- **Invariante de Verificación Física:** nIA no "cree" que ha escrito un archivo. Realiza un `os.path.exists()` y un checksum tras cada operación de escritura atómica.
- **Invariante de Seguridad (Sandboxing):** Las ejecuciones de tests ocurren en un entorno controlado con `ParanoidPathValidator`, bloqueando cualquier intento de acceso a archivos del sistema operativo o fuera del `/project_root`.
- **Invariante de Patching:** Cada tarea exitosa se consolida en un `patch` y se documenta en un `history_report.html` autogenerado.

---

## 4. CAPAS DE ESCALA (Invariantes de "Mega Máximo Senior")
*Para proyectos de alta complejidad (Platform Scale), nIA añade estas capas automáticas:*

### A. Invariante de Accesibilidad (A11y):
- nIA rechaza cualquier componente UI que no cumpla con estándares mínimos de accesibilidad (WCAG 2.1).
- **Check automático:** Uso de `aria-labels`, roles semánticos y contraste de color. Si el componente no es navegable por teclado, el test funcional *debe* fallar.

### B. Invariante de Rendimiento (Performance Budgets):
- Cada iteración del Modo Agent mide el impacto en el peso del proyecto.
- **Lógica:** Si un nuevo componente incrementa el bundle size por encima de un umbral predefinido (ej: 50kb para un giny/widget), nIA dispara una fase de refactorización obligatoria para optimizar imports o lógica.

### C. Invariante de Privacidad y Sanitización:
- Especialmente crítico para módulos tipo ERP o Chat.
- **Comportamiento:** nIA detecta patrones de "Sensitive Data" (PII, API Keys, contraseñas en duro) y bloquea la escritura del archivo si no se han usado variables de entorno o sistemas de sanitización definidos en el `SPEC.md`.

### D. Protocolo de Resolución de Dependencias:
- nIA no añade librerías ciegamente.
- **Lógica:** Antes de un `pip install` o `npm install`, verifica vulnerabilidades conocidas (CVE) y conflictos de versiones. Si hay un conflicto, nIA genera un "Dependency Conflict Report" en el Modo Parlar antes de proceder.

---

## 5. RESUMEN ARQUITECTÓNICO PARA IMPLEMENTACIÓN
Para que otro agente implemente esto, debe considerar a nIA como una **Máquina de Estados Finita** impulsada por **Contratos de Calidad**:
1. **Input:** Requerimiento natural.
2. **State 1 (Parlar):** Acuerdo de especificación.
3. **State 2 (Planejar):** Plan de ataque validado.
4. **State 3 (Agent):** Ciclo infinito RED-GREEN hasta completar el plan o agotar recursos.
5. **Output:** Proyecto verificado por tests, sin deuda técnica de placeholders, y con historial de Git limpio.
