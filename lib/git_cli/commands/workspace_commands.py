from typing import Optional, Union, List, Dict, Any, Tuple
from pathlib import Path
from lib.git_cli.commands.base import GitCommand, CommandResult
from lib.git_cli.executor import GitExecutor
from lib.git_cli.core.validation import GitValidator
from lib.git_cli.ui.icons import get_icon
from lib.git_cli.utils.logger import get_logger

logger = get_logger(__name__)


class StatusCommand(GitCommand):
    """Show repository status."""

    def execute(self, **kwargs: Any) -> CommandResult:
        """
        Show repository status.

        Args:
            **kwargs: Additional arguments

        Returns:
            CommandResult with status output and success indicator
        """
        status, stderr, return_code = GitExecutor.run_git(
            "status", repo_dir=self.repo_dir
        )

        logger.debug(f"Status command executed with return code: {return_code}")

        # Format the output with icon
        output = f"{get_icon('status')} Status:\n{status}"

        return {
            "stdout": output,
            "stderr": stderr,
            "success": return_code == 0
        }


class LogCommand(GitCommand):
    """Show commit history."""

    def execute(self, **kwargs: Any) -> CommandResult:
        """
        Show commit history.

        Args:
            **kwargs: Additional arguments

        Returns:
            CommandResult with log output and success indicator
        """
        log_format = "%Cred%h %Cblue%an%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr)%Creset"

        stdout, stderr, return_code = GitExecutor.run_git(
            "log",
            "--graph",
            "--pretty=format:" + log_format,
            "--abbrev-commit",
            "--date=relative",
            repo_dir=self.repo_dir
        )

        logger.debug(f"Log command executed with return code: {return_code}")

        # Add "Log:" header to make output consistent
        output = stdout or "No commit history found"

        return {
            "stdout": output,
            "stderr": stderr,
            "success": return_code == 0
        }


class DiffCommand(GitCommand):
    """Show changes between working directory and last commit."""

    def execute(self, **kwargs: Any) -> CommandResult:
        """
        Show changes between working directory and last commit.

        Args:
            **kwargs: Additional arguments

        Returns:
            CommandResult with diff output and success indicator
        """
        # Enable color output
        GitExecutor.run_git(
            "config", "--local", "color.ui", "auto", repo_dir=self.repo_dir
        )

        stdout, stderr, return_code = GitExecutor.run_git(
            "diff", "--color", repo_dir=self.repo_dir
        )

        logger.debug(f"Diff command executed with return code: {return_code}")

        # Format output with icon
        output = f"{get_icon('diff')} Diff:\n{stdout}" if stdout else "No changes detected"

        return {
            "stdout": output,
            "stderr": stderr,
            "success": return_code == 0
        }


class BlameCommand(GitCommand):
    """Show who last modified each line of a file."""

    def execute(self, file: str = None, **kwargs: Any) -> CommandResult:
        """
        Show who last modified each line of a file.

        Args:
            file: File to blame
            **kwargs: Additional arguments

        Returns:
            CommandResult with blame output and success indicator
        """
        # Extract file from positional arguments if not explicitly provided
        if file is None:
            file = kwargs.get("arg", kwargs.get("arg0"))

        if not file:
            return {
                "stdout": "",
                "stderr": "File path is required for blame command",
                "success": False
            }

        if not GitValidator.is_valid_file_path(Path(self.repo_dir) / file):
            return {
                "stdout": "",
                "stderr": f"File not found: {file}",
                "success": False
            }

        stdout, stderr, return_code = GitExecutor.run_git(
            "blame", file, repo_dir=self.repo_dir
        )

        logger.debug(f"Blame command executed with return code: {return_code}")

        # Format output with icon
        output = f"{get_icon('blame')} Blame for {file}:\n{stdout}"

        return {
            "stdout": output,
            "stderr": stderr,
            "success": return_code == 0
        }


class ResetCommand(GitCommand):
    """Reset working directory to last commit."""

    def execute(self, hard: bool = False, **kwargs: Any) -> CommandResult:
        """
        Reset working directory to last commit.

        Args:
            hard: Whether to perform a hard reset
            **kwargs: Additional arguments

        Returns:
            CommandResult with reset output and success indicator
        """
        # Check for --hard flag in kwargs
        hard = hard or kwargs.get("hard", False)

        if hard:
            stdout, stderr, return_code = GitExecutor.run_git(
                "reset", "--hard", repo_dir=self.repo_dir
            )
            output = f"{get_icon('hard')} Hard reset successful" if return_code == 0 else ""
        else:
            stdout, stderr, return_code = GitExecutor.run_git(
                "reset", repo_dir=self.repo_dir
            )
            output = "Reset successful" if return_code == 0 else ""

        logger.debug(f"Reset command executed with return code: {return_code}")

        return {
            "stdout": output,
            "stderr": stderr,
            "success": return_code == 0
        }


class CleanCommand(GitCommand):
    """Clean working directory."""

    def execute(self, delete_ignored: bool = False, **kwargs: Any) -> CommandResult:
        """
        Clean working directory.

        Args:
            delete_ignored: Whether to delete ignored files
            **kwargs: Additional arguments

        Returns:
            CommandResult with clean output and success indicator
        """
        # Check for --force or -f flag in kwargs
        delete_ignored = delete_ignored or kwargs.get("delete_ignored", False) or kwargs.get("x", False)

        args = ["-fd"]
        if delete_ignored:
            args = ["-fdx"]

        stdout, stderr, return_code = GitExecutor.run_git(
            "clean", *args, repo_dir=self.repo_dir
        )

        logger.debug(f"Clean command executed with return code: {return_code}")

        output = f"{get_icon('pristine')} Clean successful" if return_code == 0 else ""

        return {
            "stdout": output,
            "stderr": stderr,
            "success": return_code == 0
        }


class PristineCommand(GitCommand):
    """Reset to pristine state (combination of hard reset and clean)."""

    def execute(self, delete_ignored: bool = False, **kwargs: Any) -> CommandResult:
        """
        Reset to pristine state.

        Args:
            delete_ignored: Whether to delete ignored files
            **kwargs: Additional arguments

        Returns:
            CommandResult with pristine output and success indicator
        """
        # First perform hard reset
        reset_cmd = ResetCommand(self.repo_dir)
        reset_result = reset_cmd.execute(hard=True)

        if not reset_result["success"]:
            return reset_result  # Return early with reset error

        # Then clean
        clean_cmd = CleanCommand(self.repo_dir)
        clean_result = clean_cmd.execute(delete_ignored=delete_ignored)

        # Combine outputs
        return {
            "stdout": f"{reset_result['stdout']}\n{clean_result['stdout']}".strip(),
            "stderr": f"{reset_result['stderr']}\n{clean_result['stderr']}".strip(),
            "success": clean_result["success"]
        }