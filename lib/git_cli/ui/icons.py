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
        "init": "🆕",
        "deinit": "🗑️",
        "commit": "✅",
        "push": "📤",
        "pull": "📥",
        "stash": "📦",
        "unstash": "📂",
        "rebase": "♻️",
        "branch": "🌿",
        "checkout": "🚀",
        "merge": "🔀",
        "tag": "🏷️",
        "config": "⚙️",
        "remote": "🌐",
        "clone": "📁",
        "fetch": "📡",
        "status": "📋",
        "log": "🧾",
        "diff": "🧮",
        "blame": "👤",
        "reset": "🔄",
        "hard": "💣",
        "clean": "🧹",
        "pristine": "✨",
    }
    return icons.get(name.lower(), "❓")