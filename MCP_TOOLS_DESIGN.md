# Especificación y Diseño Técnico de Nuevas Herramientas MCP para RuneScript

Este documento detalla la arquitectura, esquemas Pydantic, políticas de seguridad y contratos de interfaz para las nuevas herramientas MCP requeridas para otorgar autonomía real a agentes externos (como Hermes Agent) sobre RuneScript.

---

## 1. Políticas de Seguridad e Invariantes del Sistema

### 1.1 Políticas del Sistema de Archivos (FS Security Policies)
1. **Path Traversal Guard**: Todo `path` recibido se resuelve mediante `os.path.realpath()` o `Path.resolve()`. Si la ruta resuelta no comienza con `RUNESCRIPT_PATH`, se aborta inmediatamente con `PermissionError` y código de error `E_PATH_OUT_OF_BOUNDS`.
2. **Tratamiento de Symlinks**: Se **rechazan** enlaces simbólicos que apunten fuera de `RUNESCRIPT_PATH`. Enlaces internos solo se leen, nunca se siguen para escrituras destructivas.
3. **Límite de Escritura**: Máximo **5 MB** por archivo único.
4. **Respaldos Automáticos (Pre-Write Backups)**: Antes de modificar o aplicar un diff sobre un archivo existente, el handler creará una copia temporal en `.nia/backups/<timestamp>_<hash>_<filename>.bak`.

### 1.2 Políticas de Git y Control de Versiones (Git Security Policies)
1. **Protección de Ramas Críticas**: Bloqueo absoluto de commits directos en `main`, `ancient`, `redgreenrefactor` y `master`.
2. **Nomenclatura Obligatoria**: Solo se permite crear y trabajar en ramas con prefijo `jules/*` o `agent/*`.
3. **Política de Push**: `git_push` requiere flag explícito `--force=False` y verificación de rama protegida.
4. **Gestión de Secretos**: Los tokens de API para GitHub (`GITHUB_TOKEN` o `GH_TOKEN`) **NUNCA** se almacenan en el repositorio ni en archivos de configuración planos. Deben inyectarse mediante variables de entorno en tiempo de ejecución.

---

## 2. Especificación de Herramientas

---

### GRUPO 1: Sistema de Archivos (Filesystem - P1)

#### 1. `fs_read_file`
- **Descripción**: Lee el contenido de un archivo dentro del repositorio hasta un número máximo de bytes.
- **Pydantic Model**:
  ```python
  class FsReadFileInput(BaseModel):
      path: str = Field(..., description="Ruta relativa o absoluta dentro del repositorio.")
      max_bytes: int = Field(default=1048576, ge=1, le=10485760, description="Límite máximo de bytes a leer (default 1MB).")
  ```
- **Output Schema**: `{"path": str, "content": str, "bytes_read": int, "truncated": bool}`
- **Handler Pseudocódigo**:
  ```python
  async def handle_fs_read_file(wrapper, path: str, max_bytes: int):
      resolved = validate_and_resolve_path(path)
      with open(resolved, "r", encoding="utf-8") as f:
          data = f.read(max_bytes + 1)
      truncated = len(data) > max_bytes
      return {"path": path, "content": data[:max_bytes], "bytes_read": min(len(data), max_bytes), "truncated": truncated}
  ```
- **Manejo de Errores**: Retorna `E_PATH_OUT_OF_BOUNDS` si sale de `RUNESCRIPT_PATH`, o `E_FILE_NOT_FOUND` si el archivo no existe.
- **Requisitos de Permisos**: Solo lectura.
- **Test Mínimo**: Leer `README.md` y verificar que retorna el contenido y `truncated=False`.
- **Dependencias**: Ninguna.

---

#### 2. `fs_write_file`
- **Descripción**: Escribe o sobrescribe un archivo dentro del repositorio con respaldos automáticos.
- **Pydantic Model**:
  ```python
  class FsWriteFileInput(BaseModel):
      path: str = Field(..., description="Ruta dentro del repositorio.")
      content: str = Field(..., description="Contenido textual a escribir.")
      create_dirs: bool = Field(default=False, description="Crea directorios padres si no existen.")
  ```
- **Output Schema**: `{"path": str, "bytes_written": int, "backup_created": Optional[str]}`
- **Handler Pseudocódigo**:
  ```python
  async def handle_fs_write_file(wrapper, path: str, content: str, create_dirs: bool):
      resolved = validate_and_resolve_path(path)
      if len(content.encode('utf-8')) > 5_242_880:
          raise ValueError("File exceeds 5MB size limit")
      backup_path = create_pre_write_backup(resolved) if os.path.exists(resolved) else None
      if create_dirs:
          os.makedirs(os.path.dirname(resolved), exist_ok=True)
      with open(resolved, "w", encoding="utf-8") as f:
          f.write(content)
      return {"path": path, "bytes_written": len(content), "backup_created": backup_path}
  ```
- **Manejo de Errores**: `E_PATH_OUT_OF_BOUNDS`, `E_SIZE_EXCEEDED`, `E_DIRECTORY_MISSING`.
- **Requisitos de Permisos**: Permiso de escritura en la ruta resuelta.
- **Test Mínimo**: Escribir en un archivo temporal en `tests/tmp_test.txt`, verificar creación de backup y contenido.
- **Dependencias**: Ninguna.

---

#### 3. `fs_list_directory`
- **Descripción**: Enumera archivos y subdirectorios dentro de una ruta.
- **Pydantic Model**:
  ```python
  class FsListDirectoryInput(BaseModel):
      path: str = Field(default=".", description="Directorio a listar.")
      recursive: bool = Field(default=False, description="Listado recursivo de subdirectorios.")
  ```
- **Output Schema**: `{"path": str, "entries": List[Dict[str, Any]]}`
- **Handler Pseudocódigo**:
  ```python
  async def handle_fs_list_directory(wrapper, path: str, recursive: bool):
      resolved = validate_and_resolve_path(path)
      entries = []
      if recursive:
          for root, dirs, files in os.walk(resolved):
              for f in files:
                  rel = os.path.relpath(os.path.join(root, f), resolved)
                  entries.append({"name": rel, "type": "file"})
      else:
          for item in os.listdir(resolved):
              is_dir = os.path.isdir(os.path.join(resolved, item))
              entries.append({"name": item, "type": "directory" if is_dir else "file"})
      return {"path": path, "entries": entries}
  ```
- **Manejo de Errores**: `E_NOT_A_DIRECTORY`, `E_PATH_OUT_OF_BOUNDS`.
- **Test Mínimo**: Listar directorio raíz `.` y verificar presencia de `src` y `README.md`.
- **Dependencias**: Ninguna.

---

#### 4. `fs_apply_diff`
- **Descripción**: Aplica un diff en formato Git Merge Diff (`<<<<<<< SEARCH`, `=======`, `>>>>>>> REPLACE`) sobre un archivo existente.
- **Pydantic Model**:
  ```python
  class FsApplyDiffInput(BaseModel):
      path: str = Field(..., description="Ruta del archivo a modificar.")
      diff: str = Field(..., description="Diff con bloques SEARCH/REPLACE.")
  ```
- **Output Schema**: `{"path": str, "applied_blocks": int, "backup_created": str}`
- **Handler Pseudocódigo**:
  ```python
  async def handle_fs_apply_diff(wrapper, path: str, diff: str):
      resolved = validate_and_resolve_path(path)
      backup_path = create_pre_write_backup(resolved)
      original = open(resolved, "r", encoding="utf-8").read()
      new_content, blocks = parse_and_apply_merge_diff(original, diff)
      open(resolved, "w", encoding="utf-8").write(new_content)
      return {"path": path, "applied_blocks": blocks, "backup_created": backup_path}
  ```
- **Manejo de Errores**: `E_SEARCH_BLOCK_NOT_FOUND` si el bloque `SEARCH` no coincide exactamente.
- **Requisitos de Permisos**: Permiso de modificación sobre el archivo.
- **Test Mínimo**: Crear un archivo de prueba, aplicar un diff de reemplazo de texto y verificar el contenido final.
- **Dependencias**: `fs_read_file`, `fs_write_file`.

---

#### 5. `fs_file_exists`
- **Descripción**: Verifica si un archivo o directorio existe dentro del repositorio.
- **Pydantic Model**:
  ```python
  class FsFileExistsInput(BaseModel):
      path: str = Field(..., description="Ruta a verificar.")
  ```
- **Output Schema**: `{"path": str, "exists": bool, "is_file": bool, "is_directory": bool}`
- **Test Mínimo**: Verificar `README.md` (`exists=True`, `is_file=True`).

---

### GRUPO 2: Control de Versiones (Git - P1)

#### 1. `git_status`
- **Descripción**: Obtiene el estado actual del árbol de trabajo de Git.
- **Pydantic Model**:
  ```python
  class GitStatusInput(BaseModel):
      pass
  ```
- **Output Schema**: `{"branch": str, "clean": bool, "staged": List[str], "unstaged": List[str], "untracked": List[str]}`

#### 2. `git_diff`
- **Descripción**: Muestra las diferencias no commiteadas o en staging.
- **Pydantic Model**:
  ```python
  class GitDiffInput(BaseModel):
      path: Optional[str] = Field(default=None, description="Filtra diff por archivo específico.")
      staged: bool = Field(default=False, description="Si es True, muestra diff de cambios en staging.")
  ```

#### 3. `git_branch_create`
- **Descripción**: Crea una nueva rama de trabajo asegurando nomenclatura permitida.
- **Pydantic Model**:
  ```python
  class GitBranchCreateInput(BaseModel):
      name: str = Field(..., description="Nombre de la rama. Debe empezar con jules/ o agent/.")
      base: str = Field(default="redgreenrefactor", description="Rama base.")
  ```
- **Regla de Seguridad**: Rechaza nombres de rama que no comiencen con `jules/` o `agent/`.

#### 4. `git_checkout`
- **Pydantic Model**:
  ```python
  class GitCheckoutInput(BaseModel):
      branch: str = Field(..., description="Nombre de la rama a seleccionar.")
  ```

#### 5. `git_add`
- **Pydantic Model**:
  ```python
  class GitAddInput(BaseModel):
      paths: List[str] = Field(..., description="Lista de archivos a añadir a staging.")
  ```

#### 6. `git_commit`
- **Pydantic Model**:
  ```python
  class GitCommitInput(BaseModel):
      message: str = Field(..., min_length=5, max_length=200, description="Mensaje del commit.")
  ```
- **Regla de Seguridad**: Impide commits directos si la rama actual es `redgreenrefactor`, `main` o `ancient`.

#### 7. `git_push`
- **Pydantic Model**:
  ```python
  class GitPushInput(BaseModel):
      branch: str = Field(..., description="Nombre de la rama a enviar.")
      remote: str = Field(default="origin", description="Nombre del remoto.")
  ```

#### 8. `git_open_pr`
- **Pydantic Model**:
  ```python
  class GitOpenPrInput(BaseModel):
      title: str = Field(..., description="Título del Pull Request.")
      body: str = Field(..., description="Descripción detallada del PR.")
      head: str = Field(..., description="Rama origen.")
      base: str = Field(default="redgreenrefactor", description="Rama destino.")
  ```
- **Uso de Token**: Utiliza `GITHUB_TOKEN` desde las variables de entorno del proceso para comunicarse con la API REST v3 de GitHub.

---

### GRUPO 3: Ejecución de Pruebas (Tests - P1)

#### 1. `run_tests`
- **Descripción**: Ejecuta la suite de pruebas automatizadas en un entorno aislado y devuelve el resultado parseado.
- **Pydantic Model**:
  ```python
  class RunTestsInput(BaseModel):
      path: Optional[str] = Field(default=None, description="Ruta del archivo o directorio de tests.")
      framework: Literal["pytest", "unittest"] = Field(default="pytest", description="Framework de testing.")
      timeout: int = Field(default=300, ge=10, le=600, description="Timeout en segundos.")
  ```
- **Output Schema**:
  ```json
  {
    "exit_code": 0,
    "passed": 7,
    "failed": 0,
    "errors": 0,
    "duration_seconds": 1.24,
    "stdout": "...",
    "stderr": "..."
  }
  ```

---

### GRUPO 4: Arquitectura de Sandbox y Aislamiento (P0)

#### Evaluación de Opciones de Sandboxing:

| Criterio | Opción 1: Docker Containers | Opción 2: bubblewrap / nsjail | Opción 3: subprocess + rlimit + seccomp |
| :--- | :--- | :--- | :--- |
| **Aislamiento FS/Red** | 🟢 Total (Container Image) | 🟢 Alto (Linux Namespaces) | 🟡 Medio (Restricción por proceso) |
| **Compatibilidad OS** | 🟢 Multiplataforma (Linux/Win/Mac) | 🔴 Solo Linux | 🟡 Parcial (Linux/POSIX) |
| **Complejidad** | 🟡 Requiere Docker Daemon | 🔴 Complejidad alta de setup | 🟢 Baja (Librerías estándar) |
| **Latencia de Arranque** | 🟡 ~500ms - 1s | 🟢 ~10ms | 🟢 <5ms |

#### **Recomendación Final de Sandbox**:
**Opción 1: Docker Containers (Efímeros por ejecución)**
- **Justificación**: Proporciona aislamiento completo e inexpugnable de sistema de archivos, red y procesos, siendo 100% multiplataforma. Para entornos de desarrollo local Linux donde Docker no esté disponible, se utilizará Opción 3 como *fallback* controlado con límites de recursos `rlimit`.

---

### GRUPO 5: Meta y Mantenimiento del Servidor (Meta - P2)

#### 1. `mcp_health`
- **Descripción**: Devuelve el estado de salud del servidor MCP, versión instalada, ruta de RuneScript activa y estado del sandbox.
- **Pydantic Model**: `class McpHealthInput(BaseModel): pass`
- **Output Schema**:
  ```json
  {
    "status": "healthy",
    "mcp_version": "1.30.0",
    "runescript_path": "/app",
    "sandbox_mode": "docker",
    "uptime_seconds": 1420
  }
  ```

#### 2. `mcp_reload`
- **Descripción**: Solicita la recarga limpia de los handlers y del wrapper del servidor MCP tras aplicar cambios en el código.
- **Pydantic Model**: `class McpReloadInput(BaseModel): pass`
