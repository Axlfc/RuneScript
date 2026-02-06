import os
import shutil
import tempfile
import logging
from typing import Protocol, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class StorageProvider(Protocol):
    """Protocol for storage operations."""
    def read(self, path: str) -> str: ...
    def write(self, path: str, content: str) -> None: ...
    def write_atomic(self, path: str, content: str) -> None: ...
    def exists(self, path: str) -> bool: ...
    def delete(self, path: str) -> None: ...

class FileSystemStorage:
    """File system based storage implementation."""
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir.resolve()

    def _get_full_path(self, path: str) -> Path:
        full_path = (self.base_dir / path).resolve()
        # Basic traversal check
        if not str(full_path).startswith(str(self.base_dir)):
            raise PermissionError(f"Attempted to access path outside base directory: {path}")
        return full_path

    def read(self, path: str) -> str:
        full_path = self._get_full_path(path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return full_path.read_text(encoding='utf-8')

    def write(self, path: str, content: str) -> None:
        full_path = self._get_full_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding='utf-8')

    def write_atomic(self, path: str, content: str) -> None:
        """
        Atomic write using temp file + os.rename()
        - Write to {path}.tmp
        - os.replace({path}.tmp, {path})
        """
        full_path = self._get_full_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        fd, temp_path = tempfile.mkstemp(dir=str(full_path.parent), prefix=f"{full_path.name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_path, str(full_path))
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e

    def exists(self, path: str) -> bool:
        try:
            return self._get_full_path(path).exists()
        except PermissionError:
            return False

    def delete(self, path: str) -> None:
        full_path = self._get_full_path(path)
        if full_path.exists():
            if full_path.is_dir():
                shutil.rmtree(full_path)
            else:
                full_path.unlink()
