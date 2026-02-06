import pytest
import os
from pathlib import Path
from src.core.storage import FileSystemStorage

def test_storage_read_write(tmp_path):
    storage = FileSystemStorage(tmp_path)
    storage.write("test.txt", "content")
    assert storage.read("test.txt") == "content"

def test_storage_write_atomic(tmp_path):
    storage = FileSystemStorage(tmp_path)
    storage.write_atomic("atomic.txt", "atomic content")
    assert storage.read("atomic.txt") == "atomic content"

def test_storage_exists_delete(tmp_path):
    storage = FileSystemStorage(tmp_path)
    storage.write("to_delete.txt", "data")
    assert storage.exists("to_delete.txt")
    storage.delete("to_delete.txt")
    assert not storage.exists("to_delete.txt")

def test_storage_traversal_protection(tmp_path):
    storage = FileSystemStorage(tmp_path)
    with pytest.raises(PermissionError):
        storage.write("../outside.txt", "bad")
