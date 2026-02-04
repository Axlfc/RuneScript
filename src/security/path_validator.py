import os
import re
from pathlib import Path
from .exceptions import PathValidationError

class ParanoidPathValidator:
    """DEFCON 1 path validation with extreme prejudice."""

    FORBIDDEN_PATHS = {
        '/etc', '/sys', '/proc', '/dev', '/root', '/boot', '/var/log',
        '/System', '/Library', '/Windows', 'C:\\Windows',
        '~/.ssh', '~/.aws', '~/.gnupg', '~/.kube'
    }

    FORBIDDEN_PATTERNS = [
        r'\.\.',           # Parent directory
        r'~',              # Home expansion
        r'\$',             # Variable expansion
        r'%',              # Windows variables
        r'\x00',           # Null bytes
        r'[^\x20-\x7E]',   # Non-printable (basic ASCII only)
    ]

    ALLOWED_EXTENSIONS = {
        '.py', '.html', '.css', '.js', '.md', '.txt', '.json',
        '.png', '.jpg', '.jpeg', '.webp', '.svg', '.gif',
        '.gitignore', '.nia_config.json', 'requirements.txt', 'package.json'
    }

    def __init__(self, base_dir=None):
        if base_dir:
            self.base_dir = os.path.realpath(os.path.abspath(base_dir))
        else:
            self.base_dir = os.path.realpath(os.getcwd())

    def validate(self, path, base_dir=None):
        """
        Validate path and return absolute, canonical path if safe.
        """
        if base_dir:
            current_base = os.path.realpath(os.path.abspath(base_dir))
        else:
            current_base = self.base_dir

        if not isinstance(path, str):
            raise PathValidationError(f"Path must be string, got {type(path)}")

        if len(path) > 4096:
            raise PathValidationError(f"Path too long: {len(path)} bytes")

        # Basic sequence check
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, path):
                raise PathValidationError(f"Forbidden pattern '{pattern}' in path: {path}")

        try:
            # Resolve potential traversal and symlinks
            # We join with base_dir, then get abspath, then realpath
            requested_path = os.path.join(current_base, path)
            abs_path = os.path.abspath(requested_path)
            real_path = os.path.realpath(abs_path)
        except Exception as e:
            raise PathValidationError(f"Path normalization failed for '{path}': {e}")

        # Escape check: real_path must start with current_base
        # Adding trailing slash to avoid "project-ext" starting with "project"
        norm_base = os.path.join(current_base, '')
        if not real_path.startswith(norm_base):
            raise PathValidationError(
                f"Path escapes base directory: {path} -> {real_path} (Base: {current_base})"
            )

        # Forbidden system paths check
        for forbidden in self.FORBIDDEN_PATHS:
            try:
                forbidden_abs = os.path.abspath(os.path.expanduser(forbidden))
                if real_path.startswith(forbidden_abs):
                    raise PathValidationError(f"Access denied to system path: {forbidden}")
            except:
                continue

        # Check for existing symlink (could be a link to a sensitive file created earlier)
        if os.path.islink(real_path):
             # For some use cases we might allow it, but for DEFCON 1, let's be strict
             raise PathValidationError(f"Path is a symlink: {real_path}")

        # Extension and Filename check
        filename = os.path.basename(real_path)
        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        if ext:
            if ext not in self.ALLOWED_EXTENSIONS and filename not in self.ALLOWED_EXTENSIONS:
                if filename.upper() not in ['LICENSE', 'README', 'CONTRIBUTING']:
                    raise PathValidationError(f"Forbidden file extension: {ext}")
        else:
            # No extension
            if filename not in self.ALLOWED_EXTENSIONS:
                if filename.upper() not in ['LICENSE', 'README', 'CONTRIBUTING', '.GITKEEP']:
                    raise PathValidationError(f"Forbidden file without extension: {filename}")

        return real_path

    def is_safe_to_read(self, path, base_dir=None):
        try:
            self.validate(path, base_dir)
            return True
        except PathValidationError:
            return False

    def is_safe_to_write(self, path, base_dir=None):
        # Could add more strict checks for writing if needed
        return self.is_safe_to_read(path, base_dir)
