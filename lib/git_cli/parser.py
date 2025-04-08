# parser.py
import shlex
from typing import Tuple, Dict


def parse_command_line(line: str) -> Tuple[str, Dict[str, str]]:
    tokens = shlex.split(line)
    if not tokens:
        return "", {}

    name, *args = tokens
    kwargs = {}
    for i, arg in enumerate(args):
        if arg.startswith("--") and "=" in arg:
            key, value = arg[2:].split("=", 1)
            kwargs[key] = value
        elif arg.startswith("--"):
            kwargs[arg[2:]] = True
        else:
            if i == 0:
                kwargs["arg"] = arg
            kwargs[f"arg{i}"] = arg

    return name, kwargs
