# git_cli/commands/meta_commands.py
from lib.git_cli.commands.base import GitCommand, CommandResult
import subprocess

from lib.git_cli.executor import GitExecutor
from lib.git_cli.utils.logger import get_logger

logger = get_logger(__name__)


class RevParseCommand(GitCommand):
    """Get information about Git repository (rev-parse)."""
    name = "rev-parse"

    def execute(self, **kwargs) -> CommandResult:
        args = [kwargs[f"arg{i}"] for i in range(len(kwargs)) if f"arg{i}" in kwargs]

        # If no arguments provided, show usage
        if not args:
            return {
                "stdout": "Usage: rev-parse [options] <args>",
                "stderr": "",
                "success": True
            }

        stdout, stderr, returncode = GitExecutor.run_git(
            "rev-parse", *args, repo_dir=self.repo_dir, errors="replace"
        )

        # Log for debugging purposes
        logger.debug(f"Running rev-parse with args: {args}")

        return {
            "stdout": stdout.strip(),
            "stderr": stderr.strip(),
            "success": returncode == 0
        }


class ShowCommand(GitCommand):
    """Show Git object information."""
    name = "show"

    def execute(self, **kwargs) -> CommandResult:
        args = [kwargs[f"arg{i}"] for i in range(len(kwargs)) if f"arg{i}" in kwargs]

        # If no arguments provided, show usage
        if not args:
            return {
                "stdout": "Usage: show [options] <object>",
                "stderr": "",
                "success": True
            }

        stdout, stderr, returncode = GitExecutor.run_git(
            "show", *args, repo_dir=self.repo_dir, errors="replace"
        )

        # Log for debugging purposes
        logger.debug(f"Running show with args: {args}")

        return {
            "stdout": stdout.strip(),
            "stderr": stderr.strip(),
            "success": returncode == 0
        }
