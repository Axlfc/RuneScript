# fallback_executor.py
import subprocess
from pathlib import Path
from lib.git_cli.commands.base import CommandResult


def execute_raw_git_command(command: str, repo_dir: Path) -> CommandResult:
    try:
        result = subprocess.check_output(
            f'git -C "{repo_dir}" {command}',
            stderr=subprocess.STDOUT,
            shell=True,
            text=True
        )
        return {
            "stdout": result,
            "stderr": "",
            "success": True
        }
    except subprocess.CalledProcessError as e:
        return {
            "stdout": "",
            "stderr": e.output,
            "success": False
        }
