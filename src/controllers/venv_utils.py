# src/controllers/venv_utils.py
import os
import sys
import shutil

def find_venvs(project_root):
    """
    Busca carpetas de entornos virtuales en project_root.
    Reconoce cualquier directorio que tenga pyvenv.cfg o Scripts/python.exe / bin/python.
    Devuelve lista de rutas absolutas.
    """
    venvs = []
    for name in os.listdir(project_root):
        full = os.path.join(project_root, name)
        if not os.path.isdir(full):
            continue
        if os.path.isfile(os.path.join(full, "pyvenv.cfg")):
            venvs.append((name, full))
        elif os.path.isfile(os.path.join(full, "Scripts", "python.exe")):
            venvs.append((name, full))
        elif os.path.isfile(os.path.join(full, "bin", "python")):
            venvs.append((name, full))
    return venvs

def find_system_pythons():
    """
    Detecta intérpretes Python del sistema en PATH.
    Devuelve lista de rutas absolutas.
    """
    pythons = set()
    for exe in ("python", "python3"):
        path = shutil.which(exe)
        if path:
            pythons.add(path)
    return list(pythons)
