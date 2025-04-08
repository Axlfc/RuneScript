# registry.py
from typing import Dict, Type
from lib.git_cli.commands.base import GitCommand

from lib.git_cli.commands.meta_commands import RevParseCommand, ShowCommand
from lib.git_cli.commands.branch_commands import BranchListCommand, CheckoutCommand, MergeCommand, TagCommand
from lib.git_cli.commands.commit_commands import CommitCommand, PushCommand, PullCommand, RebaseCommand, StashCommand, UnstashCommand
from lib.git_cli.commands.config_commands import ConfigGetCommand, ConfigSetCommand
from lib.git_cli.commands.remote_commands import RemoteListCommand, CloneCommand, FetchCommand
from lib.git_cli.commands.setup_commands import InitCommand, DeinitCommand
from lib.git_cli.commands.workspace_commands import (
    StatusCommand, LogCommand, DiffCommand, BlameCommand,
    ResetCommand, CleanCommand, PristineCommand
)

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
