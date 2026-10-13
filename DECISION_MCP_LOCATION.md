# Decisiones de Arquitectura: Ubicación del MCP Server de RuneScript

## 1. Contexto

El servidor MCP (Model Context Protocol) permite a agentes externos (como Hermes Agent, Claude Desktop o Cursor) conectarse vía `stdio`, descubrir herramientas e invocar acciones para controlar y orquestar RuneScript.

A partir de la auditoría inicial de la rama `redgreenrefactor`, se detectó que la carpeta `cognito-stack/mcp-servers/runescript` existía originalmente en `origin/ancient` (commit `bbbbbc0`), pero estaba ausente en `redgreenrefactor`.

Este documento analiza tres opciones para la ubicación y distribución del MCP server, evalúa sus pros y contras según los criterios de ingeniería del proyecto, y emite una recomendación formal.

---

## 2. Análisis de Opciones

### Opción A: MCP integrado en la rama `redgreenrefactor` (`cognito-stack/mcp-servers/runescript`)

El servidor MCP se co-ubica dentro del repositorio de RuneScript en la rama `redgreenrefactor`.

* **Mantenibilidad**: **Alta**. Los cambios en las APIs internas del IDE (`src/models/ai_assistant.py`, etc.) se sincronizan en el mismo commit o PR que actualiza el wrapper del MCP.
* **Riesgo de Merge**: **Muy Bajo**. La carpeta `cognito-stack/mcp-servers/runescript` es puramente aditiva y no entra en conflicto con archivos existentes de `redgreenrefactor`.
* **Acoplamiento con el Core**: **Medio-Alto**. El servidor MCP importa directamente los módulos Python de RuneScript (`from src.models.ai_assistant import AIAssistant`).
* **Facilidad para Hermes**: **Alta**. Hermes solo necesita ejecutar la ruta relativa dentro del clon de RuneScript.
* **Futuro de Autonomía**: **Muy Alto**. Un agente autónomo que opera sobre el repositorio puede inspeccionar, probar y mejorar tanto el núcleo del IDE como el propio servidor MCP en una sola rama.

---

### Opción B: Mergear `redgreenrefactor` → `ancient` para unificar el MCP original

Forzar la fusión de `redgreenrefactor` hacia la rama base `ancient` donde vivía originalmente el commit `bbbbbc0`.

* **Mantenibilidad**: **Baja**. Dificultad para mantener la estabilidad del proyecto durante un rebase o merge masivo.
* **Riesgo de Merge**: **EXTREMO**. `redgreenrefactor` está fuertemente divergida de `ancient` (406 archivos modificados, +47,674 inserciones, -9,290 eliminaciones). Un merge directo provocaría cientos de conflictos sintácticos y de regresión en CustomTkinter y el motor nIA.
* **Acoplamiento con el Core**: **Alto**.
* **Facilidad para Hermes**: **Baja en el corto plazo**. Bloquea la integración de Hermes hasta que se resuelva la divergencia masiva de ramas.
* **Futuro de Autonomía**: **Incierto**. Elevado riesgo de romper dependencias en tiempo de ejecución.

---

### Opción C: MCP como proyecto satélite independiente (`runescript-mcp-server`)

El servidor MCP se empaqueta como un repositorio/paquete independiente (o subsistema desacoplado) que recibe la variable de entorno `RUNESCRIPT_PATH` apuntando a cualquier clon local de RuneScript.

* **Mantenibilidad**: **Media**. Exige mantener compatibilidad hacia atrás o versiones explícitas entre el servidor MCP y distintas versiones/ramas de RuneScript.
* **Riesgo de Merge**: **Cero**. Cero impacto en el repositorio principal de RuneScript.
* **Acoplamiento con el Core**: **Bajo**. El servidor MCP actúa como una capa de control externa (*Control Plane*) que interactúa con el objetivo mediante `sys.path` dinámico o subprocess/CLI.
* **Facilidad para Hermes**: **Muy Alta**. Hermes puede instalar `runescript-mcp-server` vía `pip` o `uvx` y apuntar a cualquier directorio de trabajo.
* **Futuro de Autonomía**: **Alto para producción / Aislamiento**. Proporciona una barrera clara de seguridad entre el agente de orquestación y el espacio de trabajo auditado.

---

## 3. Matriz Comparativa

| Criterio | Opción A (Monorepo en `redgreenrefactor`) | Opción B (Merge a `ancient`) | Opción C (Satélite con `RUNESCRIPT_PATH`) |
| :--- | :---: | :---: | :---: |
| **Mantenibilidad** | 🟢 Alta | 🔴 Muy Baja | 🟡 Media |
| **Riesgo de Merge** | 🟢 Muy Bajo | 🔴 Extremo (+47k líneas) | 🟢 Cero |
| **Acoplamiento** | 🟡 Medio | 🟡 Medio | 🟢 Bajo |
| **Conexión Hermes** | 🟢 Inmediata | 🔴 Bloqueada | 🟢 Inmediata |
| **Autonomía y TDD** | 🟢 Excelente | 🔴 Riesgo alto | 🟢 Excelente |

---

## 4. Recomendación Final

**Recomendación: Modelo Híbrido A/C (Co-ubicado en monorepo con arquitectura de Satélite)**

1. **Ubicación del código**: Adoptar la **Opción A** dentro del repositorio en `cognito-stack/mcp-servers/runescript` sobre la rama `redgreenrefactor`. Esto elimina el riesgo de merge masivo de la Opción B y mantiene el código sincronizado en un solo lugar.
2. **Diseño de ejecución**: Implementar la lógica interna con el desacoplamiento de la **Opción C**. El servidor MCP debe ser un proceso independiente que acepte `RUNESCRIPT_PATH` dinámicamente y no dependa de ser ejecutado desde un directorio en particular.

Esta decisión permite empezar a trabajar de inmediato en la FASE B y FASE C sin bloqueos de merge ni divergencias de repositorio.
