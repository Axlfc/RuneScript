# dispatcher.py
from pathlib import Path
from typing import Any, Dict
from lib.git_cli.registry import COMMAND_REGISTRY
from lib.git_cli.parser import parse_command_line
from lib.git_cli.commands.base import CommandResult


class CommandDispatcher:
    def __init__(self, repo_dir: Path):
        self.repo_dir = repo_dir

    def dispatch(self, name: str, **kwargs: Any) -> CommandResult:
        name = name.lower()
        if name not in COMMAND_REGISTRY:
            return {
                "stdout": "",
                "stderr": f"Unknown command: '{name}'",
                "success": False
            }

        command_class = COMMAND_REGISTRY[name]
        command = command_class(repo_dir=self.repo_dir)
        return command.execute(**kwargs)

    def dispatch_line(self, line: str) -> CommandResult:
        name, kwargs = parse_command_line(line)
        if not name:
            return {"stdout": "", "stderr": "Empty command", "success": False}
        return self.dispatch(name, **kwargs)

