"""Anthropic configuration shared by the UI and project AI subprocesses."""

import os
from pathlib import Path

from dotenv import dotenv_values, load_dotenv, set_key


ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
DEFAULT_MODEL = "claude-sonnet-4-6"


def load_anthropic_settings():
    # Process environment takes precedence, including in child processes.
    load_dotenv(dotenv_path=ENV_PATH, override=False)
    return (
        os.getenv("ANTHROPIC_API_KEY", "").strip(),
        os.getenv("ANTHROPIC_WORKSPACE_ID", "").strip(),
        os.getenv("ANTHROPIC_MODEL", "").strip() or DEFAULT_MODEL,
    )


def save_anthropic_settings(api_key, workspace_id, model):
    """Save locally; a blank key keeps the existing key, never revealing it."""
    api_key, workspace_id, model = (value.strip() for value in (api_key, workspace_id, model))
    if any(any(char in value for char in "\r\n\0") for value in (api_key, workspace_id, model)):
        raise ValueError("Settings must be single-line values.")
    if api_key == "ANTHROPIC_API_KEY":
        raise ValueError("Enter the actual Anthropic API key, not its variable name.")
    if not api_key and not (os.getenv("ANTHROPIC_API_KEY") or dotenv_values(ENV_PATH).get("ANTHROPIC_API_KEY")):
        raise ValueError("Enter an Anthropic API key or configure ANTHROPIC_API_KEY in the environment.")
    if not model:
        raise ValueError("Enter an Anthropic model ID.")

    if not ENV_PATH.exists():
        fd = os.open(ENV_PATH, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(fd)
    changes = {"ANTHROPIC_WORKSPACE_ID": workspace_id, "ANTHROPIC_MODEL": model}
    if api_key:
        changes["ANTHROPIC_API_KEY"] = api_key
    for name, value in changes.items():
        set_key(str(ENV_PATH), name, value)
        os.environ[name] = value


def create_anthropic_client():
    import anthropic

    api_key, workspace_id, _ = load_anthropic_settings()
    if not api_key:
        raise ValueError("Anthropic API key missing. Configure it in AI Server Settings or ANTHROPIC_API_KEY.")
    headers = {"anthropic-workspace-id": workspace_id} if workspace_id else None
    return anthropic.Anthropic(api_key=api_key, default_headers=headers)
