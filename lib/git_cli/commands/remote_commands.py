from typing import Optional, Union, List, Dict, Any
from pathlib import Path
from lib.git_cli.commands.base import GitCommand
from lib.git_cli.executor import GitExecutor
from lib.git_cli.core.validation import GitValidator
from lib.git_cli.ui.icons import get_icon
from lib.git_cli.utils.logger import get_logger


logger = get_logger(__name__)


class RemoteListCommand(GitCommand):
    """List remote repositories."""

    def execute(self, **kwargs: Any) -> bool:
        """
        List remote repositories.

        Args:
            **kwargs: Additional arguments

        Returns:
            True if the command executed successfully, False otherwise
        """
        stdout, stderr, return_code = GitExecutor.run_git(
            "remote", "-v", repo_dir=self.repo_dir
        )

        if return_code == 0:
            logger.info(f"{get_icon('remote')} Remotes:\n{stdout}")
            return True
        else:
            logger.error(f"Failed to list remote repositories: {stderr}")
            return False


class CloneCommand(GitCommand):
    """Clone a repository."""

    def execute(self, url: str, **kwargs: Any) -> bool:
        """
        Clone a repository.

        Args:
            url: Repository URL
            **kwargs: Additional arguments

        Returns:
            True if the command executed successfully, False otherwise
        """
        if not GitValidator.is_valid_repo_url(url):
            logger.error(f"Invalid repository URL: {url}")
            return False

        stdout, stderr, return_code = GitExecutor.run_git(
            "clone", url, self.repo_dir, check=True
        )

        if return_code == 0:
            logger.info(f"{get_icon('clone')} Clone of {url} successful")
            return True
        else:
            logger.error(f"Failed to clone repository {url}: {stderr}")
            return False


class FetchCommand(GitCommand):
    """Fetch changes from remote repository."""

    def execute(self, **kwargs: Any) -> bool:
        """
        Fetch changes from remote repository.

        Args:
            **kwargs: Additional arguments

        Returns:
            True if the command executed successfully, False otherwise
        """
        stdout, stderr, return_code = GitExecutor.run_git(
            "fetch", repo_dir=self.repo_dir
        )

        if return_code == 0:
            logger.info(f"{get_icon('fetch')} Fetch successful")
            return True
        else:
            logger.error(f"Failed to fetch changes: {stderr}")
            return False
