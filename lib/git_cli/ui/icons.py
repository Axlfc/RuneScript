# git_cli/ui/icons.py

def get_icon(name: str) -> str:
    """
    Return a Unicode icon representation for a given git command category.

    Args:
        name: The command or category name

    Returns:
        A string containing the Unicode icon
    """
    icons = {
        "init": "ðŸ†•",
        "deinit": "ðŸ—‘ï¸",
        "commit": "âœ…",
        "push": "ðŸ“¤",
        "pull": "ðŸ“¥",
        "stash": "ðŸ“¦",
        "unstash": "ðŸ“‚",
        "rebase": "â™»ï¸",
        "branch": "ðŸŒ¿",
        "checkout": "ðŸš€",
        "merge": "ðŸ”€",
        "tag": "ðŸ·ï¸",
        "config": "âš™ï¸",
        "remote": "ðŸŒ",
        "clone": "ðŸ“",
        "fetch": "ðŸ“¡",
        "status": "ðŸ“‹",
        "log": "ðŸ§¾",
        "diff": "ðŸ§®",
        "blame": "ðŸ‘¤",
        "reset": "ðŸ”„",
        "hard": "ðŸ’£",
        "clean": "ðŸ§¹",
        "pristine": "âœ¨",
    }
    return icons.get(name.lower(), "â“")
