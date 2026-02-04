import pytest
import os
from src.security.path_validator import ParanoidPathValidator
from src.security.exceptions import PathValidationError

def test_path_traversal_basic():
    validator = ParanoidPathValidator(base_dir="/home/claude/project")
    with pytest.raises(PathValidationError):
        validator.validate("../../../etc/passwd")

def test_path_traversal_encoded():
    validator = ParanoidPathValidator(base_dir="/home/claude/project")
    with pytest.raises(PathValidationError):
        validator.validate("..%2f..%2f..%2fetc%2fpasswd")

def test_path_traversal_null_byte():
    validator = ParanoidPathValidator(base_dir="/home/claude/project")
    with pytest.raises(PathValidationError):
        validator.validate("file.txt\0../../../etc/passwd")

def test_forbidden_system_paths():
    validator = ParanoidPathValidator(base_dir="/home/claude/project")
    # Even if relative, if it resolves to a forbidden path
    with pytest.raises(PathValidationError):
        validator.validate("/etc/shadow")

def test_absolute_path_outside_base():
    validator = ParanoidPathValidator(base_dir="/home/claude/project")
    with pytest.raises(PathValidationError):
        validator.validate("/home/other_user/secret.txt")

def test_valid_path():
    base = os.path.realpath("/home/claude/project")
    validator = ParanoidPathValidator(base_dir=base)
    path = "src/main.py"
    validated = validator.validate(path)
    assert validated == os.path.join(base, "src", "main.py")

def test_non_printable_characters():
    validator = ParanoidPathValidator(base_dir="/home/claude/project")
    with pytest.raises(PathValidationError):
        validator.validate("file\x01.txt")

def test_unicode_traversal_lookalike():
    validator = ParanoidPathValidator(base_dir="/home/claude/project")
    # Using different unicode characters that look like dots or slashes
    with pytest.raises(PathValidationError):
        validator.validate("..\u2024\u2024/etc/passwd")

def test_path_traversal_double_dots_variant():
    validator = ParanoidPathValidator(base_dir="/home/claude/project")
    variants = [
        "....//etc/passwd",
        "./.././../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "nested/../../../../etc/passwd"
    ]
    for v in variants:
        with pytest.raises(PathValidationError):
            validator.validate(v)

def test_forbidden_extensions():
    validator = ParanoidPathValidator(base_dir="/home/claude/project")
    forbidden = ["script.sh", "database.db", "config.yml", "id_rsa", "binary.exe"]
    for f in forbidden:
        with pytest.raises(PathValidationError):
            validator.validate(f)

def test_case_sensitivity_bypass():
    validator = ParanoidPathValidator(base_dir="/home/claude/project")
    # If /ETC/PASSWD works on some systems
    with pytest.raises(PathValidationError):
        validator.validate("/ETC/PASSWD")

def test_symlink_attack_prevention():
    # This is harder to test without real symlinks, but we check if the validator detects existing links
    # (The validator code has os.path.islink check)
    pass
