# git_cli/commands/dispatcher.py
from typing import Type, Dict, Any, Union
from pathlib import Path
from lib.git_cli.commands.base import GitCommand, CommandResult
import shlex

# Import all command classes (kept the same as original)
from .meta_commands import RevParseCommand, ShowCommand
from .branch_commands import BranchListCommand, CheckoutCommand, MergeCommand, TagCommand
from .commit_commands import CommitCommand, PushCommand, PullCommand, RebaseCommand, StashCommand, UnstashCommand
from .config_commands import ConfigGetCommand, ConfigSetCommand
from .remote_commands import RemoteListCommand, CloneCommand, FetchCommand
from .setup_commands import InitCommand, DeinitCommand
from .workspace_commands import (
    StatusCommand, LogCommand, DiffCommand, BlameCommand,
    ResetCommand, CleanCommand, PristineCommand
)

# Command registry mapping string names to command classes
COMMAND_REGISTRY: Dict[str, Type[GitCommand]] = {
    cmd().name: cmd for cmd in [
        BranchListCommand, CheckoutCommand, MergeCommand, TagCommand,
        CommitCommand, PushCommand, PullCommand, RebaseCommand, StashCommand, UnstashCommand,
        ConfigGetCommand, ConfigSetCommand,
        RemoteListCommand, CloneCommand, FetchCommand,
        InitCommand, DeinitCommand,
        StatusCommand, LogCommand, DiffCommand, BlameCommand,
        ResetCommand, CleanCommand, PristineCommand,
        RevParseCommand, ShowCommand,

    ]
}


# Refactored Dispatcher
class CommandDispatcher:
    def __init__(self, repo_dir: Path):
        self.repo_dir = repo_dir

    def dispatch(self, name: str, **kwargs: Any) -> CommandResult:
        """
        Dispatch a command by name with given arguments.

        Args:
            name: The command name to execute
            **kwargs: Command-specific arguments

        Returns:
            CommandResult with stdout, stderr, and success status
        """
        name = name.lower()
        if name not in COMMAND_REGISTRY:
            # Return structured error for unknown commands
            return {
                "stdout": "",
                "stderr": f"Unknown command: '{name}'",
                "success": False
            }

        command_class = COMMAND_REGISTRY[name]
        command = command_class(repo_dir=self.repo_dir)

        # Execute and return the structured result
        return command.execute(**kwargs)

    def dispatch_line(self, line: str) -> CommandResult:
        tokens = shlex.split(line)
        if not tokens:
            return {
                "stdout": "",
                "stderr": "Empty command",
                "success": False
            }

        name, *args = tokens

        # Handle command arguments
        kwargs = {}
        for i, arg in enumerate(args):
            if arg.startswith("--") and "=" in arg:
                # Handle --key=value style arguments
                key, value = arg[2:].split("=", 1)
                kwargs[key] = value
            elif arg.startswith("--"):
                # Handle --flag style arguments
                kwargs[arg[2:]] = True
            else:
                # Positional arguments
                if i == 0:
                    kwargs["arg"] = arg  # First argument is just "arg"
                kwargs[f"arg{i}"] = arg

        # Execute the command and return its result
        return self.dispatch(name, **kwargs)