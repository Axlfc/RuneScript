import subprocess
import shutil
import sys
import logging

logger = logging.getLogger(__name__)

def check_tool(command: str) -> bool:
    """Check if a tool is available in the system PATH."""
    return shutil.which(command) is not None

def get_python_executable() -> str:
    """Return the current Python executable."""
    return sys.executable

def check_node() -> bool:
    """Check if Node.js is available."""
    try:
        subprocess.run(["node", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_npm() -> bool:
    """Check if npm is available."""
    try:
        subprocess.run(["npm", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def detect_available_tools() -> dict:
    """Detect all relevant tools for project generation."""
    return {
        "python": True,  # Current executable is always available
        "python_path": get_python_executable(),
        "node": check_node(),
        "npm": check_npm(),
        "git": check_tool("git")
    }

if __name__ == "__main__":
    print(detect_available_tools())
