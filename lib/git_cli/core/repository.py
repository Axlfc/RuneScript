# git_cli/core/repository.py
from pathlib import Path
from typing import Optional, Union, List, Dict, Any, Tuple

from lib.git_cli.executor import GitExecutor

from lib.git_cli.utils.logger import get_logger

logger = get_logger(__name__)


class Repository:
    """Represents a Git repository and provides methods to interact with it."""

    def __init__(self, path: Union[str, Path]):
        """
        Initialize a Repository object.

        Args:
            path: Path to the Git repository
        """
        self.path = Path(path).absolute()

    @property
    def exists(self) -> bool:
        """Check if the repository directory exists."""
        return self.path.exists() and self.path.is_dir()

    @property
    def is_git_repository(self) -> bool:
        """Check if the directory is a Git repository."""
        if not self.exists:
            return False

        stdout, stderr, return_code = GitExecutor.run_git(
            "rev-parse", "--is-inside-work-tree", repo_dir=self.path, check=False
        )
        return return_code == 0 and stdout.strip() == "true"

    def get_current_branch(self) -> Optional[str]:
        """Get the name of the current branch."""
        if not self.is_git_repository:
            return None

        stdout, stderr, return_code = GitExecutor.run_git(
            "symbolic-ref", "--short", "HEAD", repo_dir=self.path
        )
        if return_code == 0:
            return stdout.strip()
        return None

    def get_status(self) -> Tuple[str, bool]:
        """
        Get repository status information.

        Returns:
            Tuple containing (status_text, has_changes)
        """
        if not self.is_git_repository:
            return "", False

        stdout, stderr, return_code = GitExecutor.run_git(
            "status", "--porcelain", repo_dir=self.path
        )

        # Get more detailed status for display
        status_stdout, _, _ = GitExecutor.run_git("status", repo_dir=self.path)

        has_changes = len(stdout.strip()) > 0
        return status_stdout, has_changes

    def get_branches(self) -> List[str]:
        """Get list of branches in the repository."""
        if not self.is_git_repository:
            return []

        stdout, stderr, return_code = GitExecutor.run_git(
            "branch", "--list", "--format=%(refname:short)", repo_dir=self.path
        )
        if return_code == 0:
            return [branch for branch in stdout.strip().split('\n') if branch]
        return []

    def get_config(self, key: str) -> Optional[str]:
        """Get Git configuration value."""
        if not self.is_git_repository:
            return None

        stdout, stderr, return_code = GitExecutor.run_git(
            "config", "--get", key, repo_dir=self.path
        )
        if return_code == 0:
            return stdout.strip()
        return None

    def set_config(self, key: str, value: str) -> bool:
        """Set Git configuration value."""
        if not self.is_git_repository:
            return False

        _, stderr, return_code = GitExecutor.run_git(
            "config", key, value, repo_dir=self.path
        )
        return return_code == 0
