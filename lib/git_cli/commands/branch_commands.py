from typing import Optional, Union, List, Dict, Any
from pathlib import Path
from lib.git_cli.commands.base import GitCommand
from lib.git_cli.executor import GitExecutor
from lib.git_cli.core.validation import GitValidator
from lib.git_cli.ui.icons import get_icon
from lib.git_cli.utils.logger import get_logger

logger = get_logger(__name__)


class BranchListCommand(GitCommand):
    """List branches in the repository."""

    def execute(self, **kwargs: Any) -> bool:
        """
        List branches in the repository.

        Args:
            **kwargs: Additional arguments

        Returns:
            True if the command executed successfully, False otherwise
        """
        stdout, stderr, return_code = GitExecutor.run_git(
            "branch", repo_dir=self.repo_dir
        )

        if return_code == 0:
            logger.info(f"{get_icon('branch')} Branches:\n{stdout}")
            return True
        else:
            logger.error(f"Failed to list branches: {stderr}")
            return False


class CheckoutCommand(GitCommand):
    """Switch to another branch."""

    def execute(self, branch: str, **kwargs: Any) -> bool:
        """
        Switch to another branch.

        Args:
            branch: Branch to check out
            **kwargs: Additional arguments

        Returns:
            True if the command executed successfully, False otherwise
        """
        if not GitValidator.is_valid_branch_name(branch):
            logger.error(f"Invalid branch name: {branch}")
            return False

        stdout, stderr, return_code = GitExecutor.run_git(
            "checkout", branch, repo_dir=self.repo_dir
        )

        if return_code == 0:
            logger.info(f"{get_icon('checkout')} Checkout to {branch} successful")
            return True
        else:
            logger.error(f"Failed to checkout branch {branch}: {stderr}")
            return False


class MergeCommand(GitCommand):
    """Merge another branch into the current branch."""

    def execute(self, branch: str, **kwargs: Any) -> bool:
        """
        Merge another branch into the current branch.

        Args:
            branch: Branch to merge
            **kwargs: Additional arguments

        Returns:
            True if the command executed successfully, False otherwise
        """
        if not GitValidator.is_valid_branch_name(branch):
            logger.error(f"Invalid branch name: {branch}")
            return False

        stdout, stderr, return_code = GitExecutor.run_git(
            "merge", branch, repo_dir=self.repo_dir
        )

        if return_code == 0:
            logger.info(f"{get_icon('merge')} Merge of {branch} successful")
            return True
        else:
            logger.error(f"Failed to merge branch {branch}: {stderr}")
            return False


class TagCommand(GitCommand):
    """Create a tag at the current commit."""

    def execute(self, tag_name: str, **kwargs: Any) -> bool:
        """
        Create a tag at the current commit.

        Args:
            tag_name: Name of the tag to create
            **kwargs: Additional arguments

        Returns:
            True if the command executed successfully, False otherwise
        """
        stdout, stderr, return_code = GitExecutor.run_git(
            "tag", tag_name, repo_dir=self.repo_dir
        )

        if return_code == 0:
            logger.info(f"{get_icon('tag')} Tag '{tag_name}' created successfully")
            return True
        else:
            logger.error(f"Failed to create tag {tag_name}: {stderr}")
            return False