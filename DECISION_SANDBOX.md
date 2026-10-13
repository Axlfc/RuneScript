# Especificación de Arquitectura de Aislamiento y Sandboxing (DECISION_SANDBOX.md)

## 1. Objetivo y Perfiles de Aislamiento

El objetivo de esta especificación es implementar un mecanismo inexpugnable de aislamiento (*sandboxing*) para la ejecución autónoma de código mediante `execute_script`, `sandbox_execute` y la suite de pruebas `run_tests`.

Para equilibrar la seguridad estricta frente a código generado por IA no confiable y el rendimiento necesario para ejecutar la suite de pruebas del proyecto, se definen dos perfiles de aislamiento distintos:

### 1.1 Perfil 1: "untrusted" (`sandbox_execute` / `execute_script`)
Diseñado para la ejecución de código efímero generado por agentes o LLMs.
* **Sin Montaje de Repositorio**: No se monta `RUNESCRIPT_PATH` ni ningún volumen del host.
* **Código vía `stdin`**: El código se inyecta directamente por `stdin` (`cat script.py | docker run -i ... python3 -`).
* **Sistema de Archivos en RAM**: `--tmpfs /tmp:rw,noexec,nosuid,size=64m` (`/tmp` temporal en RAM de 64MB con ejecución de binarios prohibida `noexec`).
* **Raíz de Solo Lectura**: `--read-only`.
* **Red Deshabilitada**: `--network=none`.
* **Límites de Recursos**: `--memory=256m`, `--cpus=1`, `--pids-limit=64`.
* **Permisos**: `--user=10001:10001`, `--cap-drop=ALL`, `--security-opt=no-new-privileges`.

---

### 1.2 Perfil 2: "trusted-tests" (`run_tests`)
Diseñado para la ejecución de pruebas automáticas del repositorio con `pytest`.
* **Montaje del Repositorio**: Monta `RUNESCRIPT_PATH` en modo **estrictamente lectura (`:ro`)**.
* **Directorio Temporal con Ejecución**: `--tmpfs /tmp:rw,exec,nosuid,size=256m` (se permite `exec` en `/tmp` porque `pytest` y generadores de código de prueba pueden requerir compilación o ejecución de módulos temporales).
* **Variables de Entorno**: `PYTHONDONTWRITEBYTECODE=1` (evita la creación de archivos `.pyc`).
* **Configuración de Pytest**: `pytest --cache-dir=/tmp/.pytest_cache -p no:cacheprovider` (fuerza a `pytest` a escribir su caché exclusivamente en `/tmp` sin tocar el árbol fuente).
* **Red Deshabilitada**: `--network=none`.
* **Límites de Recursos**: `--memory=512m`, `--cpus=2`, `--pids-limit=128`.
* **Permisos**: `--user=10001:10001`, `--cap-drop=ALL`, `--security-opt=no-new-privileges`.

---

## 2. Gestión del Ciclo de Vida y Limpieza de Contenedores

Para evitar la acumulación de contenedores huérfanos o colgados:
1. **Auto-Eliminación**: Todos los comandos ejecutan con la flag `--rm`.
2. **Nomenclatura Determinista**: Nombres únicos generados mediante `runescript-sandbox-<uuid4>`.
3. **Etiquetado Métrico**: Todos los contenedores del sandbox llevan la etiqueta `--label runescript-sandbox=true`.
4. **Watchdog de Limpieza**: Un proceso de limpieza periódico (ejecutado en segundo plano) rastrea cada 5 minutos contenedores con la etiqueta `runescript-sandbox=true` que lleven más de 5 minutos activos y ejecuta `docker kill` y `docker rm -f`.
5. **Registro de Limpieza**: Cualquier contenedor huérfano eliminado por el watchdog genera un registro en `runescript_mcp.log` con nivel `WARNING`.

---

## 3. Manejo de Fallos de Docker e Imágenes Base

1. **Construcción de Imagen Base (`runescript-sandbox:3.11-slim`)**:
   - El repositorio incluye un `Dockerfile.sandbox` en `cognito-stack/mcp-servers/runescript/Dockerfile.sandbox`.
   - Al iniciar el servidor MCP, se verifica si la imagen local `runescript-sandbox:3.11-slim` existe. Si no existe, se construye automáticamente mediante `docker build` o se utiliza `python:3.11-slim` con instalación de dependencias en `/tmp`.
2. **Diferenciación de Errores (Fallo de Código vs. Fallo de Infraestructura)**:
   - **Fallo del código ejecutable**: Si el contenedor arranca y el intérprete Python devuelve un `exit_code != 0`, el error se formatea en el JSON de respuesta como una salida normal con `exit_code`, `stdout` y `stderr`.
   - **Fallo de la infraestructura Docker**: Si el Demonio de Docker no responde, la imagen no existe o falla la invocación del comando `docker`, el handler captura la excepción de sistema y devuelve un error de protocolo `E_DOCKER_INFRASTRUCTURE_ERROR` diferenciado.
3. **Mecanismo de Fallback (`rlimit`)**:
   - El modo de aislamiento degradado mediante `rlimit` **NO se activa silenciosamente**.
   - Requiere la presencia explícita de la variable de entorno `RUNESCRIPT_ALLOW_DEGRADED_SANDBOX=true`.
   - Si Docker no está disponible y la variable no está configurada, la llamada falla con error de seguridad.
4. **Advertencias de Degradación**:
   - La advertencia de que se está utilizando el sandbox degradado `rlimit` se emite en el log `runescript_mcp.log` una vez por sesión al inicializar el wrapper.

---

## 4. Concurrencia y Control de Carga

1. **Límite de Concurrencia**: Máximo de **4 contenedores concurrentes** por defecto. Configurable mediante la variable de entorno `RUNESCRIPT_SANDBOX_MAX_CONCURRENT`.
2. **Manejo de Sobrecarga**: Se implementa un semáforo asíncrono (`asyncio.Semaphore(MAX_CONCURRENT)`). Si se alcanza el número máximo de ejecuciones simultáneas, las nuevas peticiones se encolan respetando un timeout global de espera.
