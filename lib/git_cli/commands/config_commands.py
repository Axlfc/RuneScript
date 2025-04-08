from typing import Any
from lib.git_cli.commands.base import GitCommand
from lib.git_cli.executor import GitExecutor
from lib.git_cli.core.validation import GitValidator
from lib.git_cli.utils.logger import get_logger

from lib.git_cli.ui.icons import get_icon

logger = get_logger(__name__)


class ConfigSetCommand(GitCommand):
    """Set Git configuration key."""

    def execute(self, key: str, value: str, **kwargs: Any) -> bool:
        if not key or not value:
            logger.error("Both key and value are required to set config.")
            return False

        stdout, stderr, return_code = GitExecutor.run_git(
            "config", key, value, repo_dir=self.repo_dir
        )

        if return_code == 0:
            logger.info(f"{get_icon('config')} Config {key} set to {value}")
            return True
        else:
            logger.error(f"Failed to set config {key}: {stderr}")
            return False


class ConfigGetCommand(GitCommand):
    """Get Git configuration value for a key."""

    def execute(self, key: str, **kwargs: Any) -> bool:
        if not key:
            logger.error("Key is required to get config.")
            return False

        stdout, stderr, return_code = GitExecutor.run_git(
            "config", "--get", key, repo_dir=self.repo_dir
        )

        if return_code == 0:
            logger.info(f"{get_icon('config')} {key} = {stdout.strip()}")
            return True
        else:
            logger.error(f"Failed to get config {key}: {stderr}")
            return False