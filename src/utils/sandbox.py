"""Execution sandbox for nIA."""
import subprocess
import tempfile
import shutil
from pathlib import Path

class SimpleSandbox:
    """
    Isolated execution environment for nIA tasks.
    """
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.sandbox_dir = Path(tempfile.mkdtemp(prefix="nia_sandbox_"))

    def run_command(self, cmd: list[str]) -> subprocess.CompletedProcess:
        """Run command in sandbox directory"""
        return subprocess.run(
            cmd,
            cwd=self.sandbox_dir,
            capture_output=True,
            text=True,
            timeout=300
        )

    def cleanup(self):
        """Clean up sandbox directory"""
        if self.sandbox_dir.exists():
            shutil.rmtree(self.sandbox_dir)
