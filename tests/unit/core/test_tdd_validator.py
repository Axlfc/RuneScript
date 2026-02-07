import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.core.tdd_validator import TDDValidator, ValidationResult

def test_validate_red_pass():
    validator = TDDValidator()
    # Mocking _run_test which returns a CompletedProcess
    with patch.object(validator, "_run_test") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="Failing", stderr="")
        res = validator.validate_red(Path("."), "test.py")
        assert res.success is True
        assert "expected" in res.message

def test_validate_red_fail_passed():
    validator = TDDValidator()
    with patch.object(validator, "_run_test") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="Passing", stderr="")
        res = validator.validate_red(Path("."), "test.py")
        assert res.success is False
        assert "passed when it should fail" in res.message

def test_validate_green_pass():
    validator = TDDValidator()
    with patch.object(validator, "_run_test") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="Passing", stderr="")
        res = validator.validate_green(Path("."), "test.py")
        assert res.success is True

def test_validate_refactor_pass():
    validator = TDDValidator()
    with patch.object(validator, "_run_all_tests") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="All Passing", stderr="")
        res = validator.validate_refactor(Path("."))
        assert res.success is True
