# git_cli/core/executor.py
from pathlib import Path
import subprocess
from typing import List, Optional, Tuple, Union
import sys


class GitExecutor:
    """Handles execution of Git commands and manages subprocess communication."""

    @staticmethod
    def run_command(
            args: List[str],
            cwd: Optional[Union[str, Path]] = None,
            capture_output: bool = True,
            encoding: str = "utf-8",
            errors: str = "replace",
            check: bool = True
    ) -> Tuple[str, str, int]:
        """
        Execute a command and return stdout, stderr, and return code.

        Args:
            args: List of command arguments
            cwd: Working directory for command execution
            capture_output: Whether to capture command output
            encoding: Character encoding for command output
            check: Whether to check return code

        Returns:
            Tuple containing (stdout, stderr, return_code)
        """
        try:
            result = subprocess.run(
                args,
                cwd=cwd,
                capture_output=capture_output,
                text=True,
                encoding=encoding,
                errors="replace",  # <== THIS prevents crashes from bad byte sequences
                check=check
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.CalledProcessError as e:
            return "", e.stderr, e.returncode
        except Exception as e:
            return "", str(e), 1

    @staticmethod
    def run_git(
            command: str,
            *args: str,
            repo_dir: Optional[Union[str, Path]] = None,
            capture_output: bool = True,
            encoding: str = "utf-8",
            errors: str = "replace",
            check: bool = False
    ) -> Tuple[str, str, int]:
        """
        Execute a git command with the given arguments.

        Args:
            command: Git command to run
            *args: Arguments to pass to the git command
            repo_dir: Git repository directory
            capture_output: Whether to capture command output
            encoding: Character encoding for command output
            check: Whether to check return code

        Returns:
            Tuple containing (stdout, stderr, return_code)
        """
        git_args = ["git", command]
        git_args.extend(args)
        return GitExecutor.run_command(
            git_args,
            cwd=repo_dir,
            capture_output=capture_output,
            encoding=encoding,
            check=check
        )
