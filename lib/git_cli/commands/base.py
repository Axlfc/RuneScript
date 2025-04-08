from abc import ABC, abstractmethod
from typing import Optional, List, Any, Dict, Union, TypedDict
from pathlib import Path
from lib.git_cli.executor import GitExecutor
from lib.git_cli.core.repository import Repository
from lib.git_cli.utils.logger import get_logger

logger = get_logger(__name__)


class CommandResult(TypedDict):
    """Structure for command execution results."""
    stdout: str
    stderr: str
    success: bool


class GitCommand(ABC):
    """Base abstract class for all Git commands."""

    def __init__(self, repo_dir: Optional[Union[str, Path]] = None):
        """
        Initialize a Git command.

        Args:
            repo_dir: Git repository directory
        """
        self.repo_dir = Path(repo_dir) if repo_dir else Path.cwd()
        self.repository = Repository(self.repo_dir)

    @abstractmethod
    def execute(self, **kwargs: Any) -> CommandResult:
        """
        Execute the Git command.

        Args:
            **kwargs: Command-specific arguments

        Returns:
            CommandResult containing stdout, stderr, and success status
        """
        pass

    @property
    def name(self) -> str:
        """Name of the command."""
        return self.__class__.__name__.lower().replace('command', '')

    @property
    def description(self) -> str:
        """Description of the command."""
        return self.__doc__ or f"Execute {self.name} command"