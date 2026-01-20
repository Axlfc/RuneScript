from typing import Optional, Union, List, Dict, Any
from pathlib import Path
from lib.git_cli.commands.base import GitCommand
from lib.git_cli.executor import GitExecutor
from lib.git_cli.ui.icons import get_icon
from lib.git_cli.utils.logger import get_logger


logger = get_logger(__name__)


class CommitCommand(GitCommand):
    """Commit changes to the repository."""

    def execute(self, message: str, **kwargs: Any) -> bool:
        """
        Commit changes to the repository.

        Args:
            message: Commit message
            **kwargs: Additional arguments

        Returns:
            True if the command executed successfully, False otherwise
        """
        if not message or not message.strip():
            logger.error("No commit message provided.")
            return False

        # First check if there are changes to commit
        stdout, stderr, return_code = GitExecutor.run_git(
            "status", "--porcelain", repo_dir=self.repo_dir
        )

        if not stdout.strip():
            logger.error("No changes to commit.")
            return False

        # Add all changes
        stdout, stderr, return_code = GitExecutor.run_git(
            "add", "-A", repo_dir=self.repo_dir
        )

        if return_code != 0:
            logger.error(f"Failed to stage changes: {stderr}")
            return False

        # Commit changes
        stdout, stderr, return_code = GitExecutor.run_git(
            "commit", "-m", message, repo_dir=self.repo_dir
        )

        if return_code == 0:
            logger.info(f"{get_icon('commit')} Commit successful")
            return True
        else:
            logger.error(f"Failed to commit changes: {stderr}")
            return False


class PushCommand(GitCommand):
    """Push changes to remote repository."""

    def execute(self, **kwargs: Any) -> bool:
        """
        Push changes to remote repository.

        Args:
            **kwargs: Additional arguments

        Returns:
            True if the command executed successfully, False otherwise
        """
        stdout, stderr, return_code = GitExecutor.run_git(
            "push", repo_dir=self.repo_dir
        )

        if return_code == 0:
            logger.info(f"{get_icon('push')} Push successful")
            return True
        else:
            logger.error(f"Failed to push changes: {stderr}")
            return False


class PullCommand(GitCommand):
    """Pull changes from remote repository."""

    def execute(self, **kwargs: Any) -> bool:
        """
        Pull changes from remote repository.

        Args:
            **kwargs: Additional arguments

        Returns:
            True if the command executed successfully, False otherwise
        """
        stdout, stderr, return_code = GitExecutor.run_git(
            "pull", repo_dir=self.repo_dir
        )

        if return_code == 0:
            logger.info(f"{get_icon('pull')} Pull successful")
            return True
        else:
            logger.error(f"Failed to pull changes: {stderr}")
            return False


class RebaseCommand(GitCommand):
    """Rebase current branch onto another branch."""

    def execute(self, branch: str, **kwargs: Any) -> bool:
        """
        Rebase current branch onto another branch.

        Args:
            branch: Target branch for rebase
            **kwargs: Additional arguments

        Returns:
            True if the command executed successfully, False otherwise
        """
        stdout, stderr, return_code = GitExecutor.run_git(
            "rebase", branch, repo_dir=self.repo_dir
        )

        if return_code == 0:
            logger.info(f"{get_icon('rebase')} Rebase onto {branch} successful")
            return True
        else:
            logger.error(f"Failed to rebase onto {branch}: {stderr}")
            return False


class StashCommand(GitCommand):
    """Stash changes in the working directory."""

    def execute(self, **kwargs: Any) -> bool:
        """
        Stash changes in the working directory.

        Args:
            **kwargs: Additional arguments

        Returns:
            True if the command executed successfully, False otherwise
        """
        stdout, stderr, return_code = GitExecutor.run_git(
            "stash", repo_dir=self.repo_dir
        )

        if return_code == 0:
            logger.info(f"{get_icon('stash')} Stash successful")
            return True
        else:
            logger.error(f"Failed to stash changes: {stderr}")
            return False


class UnstashCommand(GitCommand):
    """Apply stashed changes to the working directory."""

    def execute(self, **kwargs: Any) -> bool:
        """
        Apply stashed changes to the working directory.

        Args:
            **kwargs: Additional arguments

        Returns:
            True if the command executed successfully, False otherwise
        """
        stdout, stderr, return_code = GitExecutor.run_git(
            "stash", "pop", repo_dir=self.repo_dir
        )

        if return_code == 0:
            logger.info(f"{get_icon('unstash')} Unstash successful")
            return True
        else:
            logger.error(f"Failed to unstash changes: {stderr}")
            return False
