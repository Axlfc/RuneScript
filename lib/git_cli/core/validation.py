# git_cli/core/validation.py
import os
import re
from pathlib import Path
from typing import Union, Optional
from urllib.parse import urlparse


class GitValidator:
    """Validates Git-related inputs."""

    @staticmethod
    def is_valid_branch_name(branch: str) -> bool:
        """
        Check if a branch name is valid according to Git naming rules.

        Args:
            branch: Branch name to validate

        Returns:
            True if the branch name is valid, False otherwise
        """
        # Git branch names cannot:
        # - Have spaces in the name
        # - Begin with '.'
        # - Contain '..' anywhere
        # - End with '/'
        # - Contain any of: ~, ^, :, ?, *, [
        invalid_chars = ['~', '^', ':', '?', '*', '[', ' ', '\\']

        if not branch or branch.startswith('.') or '..' in branch or branch.endswith('/'):
            return False

        return not any(char in branch for char in invalid_chars)

    @staticmethod
    def is_valid_file_path(file_path: Union[str, Path]) -> bool:
        """
        Check if a file path exists and is a file.

        Args:
            file_path: Path to validate

        Returns:
            True if the path exists and is a file, False otherwise
        """
        return os.path.isfile(file_path)

    @staticmethod
    def is_valid_repo_url(url: str) -> bool:
        """
        Check if a repository URL is valid.

        Args:
            url: Repository URL to validate

        Returns:
            True if the URL is valid, False otherwise
        """
        # Support git://, http://, https://, ssh:// and SCP-like syntax
        if not url:
            return False

        # Check common Git URL formats
        git_protocols = ['git://', 'http://', 'https://', 'ssh://']
        if any(url.startswith(protocol) for protocol in git_protocols):
            parsed = urlparse(url)
            return bool(parsed.netloc)

        # Check SCP-like syntax (e.g., git@github.com:user/repo.git)
        if ':' in url and not url.startswith(':'):
            parts = url.split(':')
            if len(parts) == 2 and '@' in parts[0] and len(parts[1]) > 0:
                return True

        # For local paths
        return os.path.exists(url) and os.path.isdir(url)