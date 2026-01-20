# git_cli/commands/setup_commands.py
from typing import Any
from lib.git_cli.commands.base import GitCommand
from lib.git_cli.executor import GitExecutor
from lib.git_cli.utils.logger import get_logger

from lib.git_cli.ui.icons import get_icon

logger = get_logger(__name__)


class InitCommand(GitCommand):
    """Initialize a new Git repository."""

    def execute(self, **kwargs: Any) -> bool:
        if self.repository.is_git_repository:
            logger.error(f"{self.repo_dir} is already a Git repository.")
            return False

        stdout, stderr, return_code = GitExecutor.run_git(
            "init", repo_dir=self.repo_dir
        )

        if return_code == 0:
            logger.info(f"{get_icon('init')} Git repository initialized at {self.repo_dir}")
            return True
        else:
            logger.error(f"Failed to initialize Git repository: {stderr}")
            return False


class DeinitCommand(GitCommand):
    """Remove Git metadata from the current directory."""

    def execute(self, **kwargs: Any) -> bool:
        import shutil

        git_dir = self.repo_dir / ".git"
        if not git_dir.exists():
            logger.error("No .git directory found to deinitialize.")
            return False

        try:
            shutil.rmtree(git_dir)
            logger.info(f"{get_icon('deinit')} Git metadata removed from {self.repo_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove .git directory: {e}")
            return False
