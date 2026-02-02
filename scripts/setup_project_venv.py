import os
import sys
import subprocess
import venv
from pathlib import Path

def setup_venv(project_path: Path):
    venv_dir = project_path / ".venv"
    if not venv_dir.exists():
        print(f"Creating venv in {venv_dir}...")
        venv.create(venv_dir, with_pip=True)

    # Determine the python executable inside the venv
    if os.name == 'nt': # Windows
        python_exe = venv_dir / "Scripts" / "python.exe"
    else: # Linux/Mac
        python_exe = venv_dir / "bin" / "python"

    if not python_exe.exists():
        print(f"❌ Could not find python executable at {python_exe}")
        sys.exit(1)

    return python_exe

def install_dependencies(python_exe, requirements):
    if not requirements:
        return

    print(f"Installing dependencies: {', '.join(requirements)}...")
    try:
        subprocess.run([str(python_exe), "-m", "pip", "install"] + requirements, check=True)
        print("✅ Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python setup_project_venv.py <project_path> [dependency1 dependency2 ...]")
        sys.exit(1)

    proj_path = Path(sys.argv[1])
    deps = sys.argv[2:]

    py_exe = setup_venv(proj_path)
    install_dependencies(py_exe, deps)

    # Print the path to the python executable so the caller can use it
    print(f"VENV_PYTHON:{py_exe}")
