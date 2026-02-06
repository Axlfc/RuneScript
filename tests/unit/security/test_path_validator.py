import pytest
import os
from src.security.path_validator import ParanoidPathValidator
from src.security.exceptions import PathValidationError

def test_path_validator_safe(tmp_path):
    validator = ParanoidPathValidator(base_dir=tmp_path)
    safe_path = validator.validate("test.py")
    assert str(safe_path).endswith("test.py")

def test_path_validator_traversal(tmp_path):
    validator = ParanoidPathValidator(base_dir=tmp_path)
    with pytest.raises(PathValidationError):
        validator.validate("../outside.py")

def test_path_validator_forbidden_extension(tmp_path):
    validator = ParanoidPathValidator(base_dir=tmp_path)
    with pytest.raises(PathValidationError):
        validator.validate("test.exe")

def test_path_validator_system_path(tmp_path):
    validator = ParanoidPathValidator(base_dir=tmp_path)
    with pytest.raises(PathValidationError):
        validator.validate("/etc/passwd")
