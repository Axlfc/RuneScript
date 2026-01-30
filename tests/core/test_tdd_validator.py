# tests/core/test_tdd_validator.py
import pytest
from pathlib import Path
from src.core.tdd_validator import TDDValidator, CyclePhase
from unittest.mock import Mock, patch
import subprocess

def test_validate_red_passes_when_test_fails():
    """RED validation passes when test fails as expected."""
    validator = TDDValidator()

    with patch("subprocess.run") as mock_run:
        # Simulate test failure (returncode != 0)
        mock_run.return_value = Mock(returncode=1, stderr="AssertionError", stdout="")

        result = validator.validate_red("test_file.py", "test_name")

        assert result.success is True
        assert "RED phase" in result.message

def test_validate_red_fails_when_test_passes():
    """RED validation fails when test passes unexpectedly."""
    validator = TDDValidator()

    with patch("subprocess.run") as mock_run:
        # Simulate test passing (returncode == 0)
        mock_run.return_value = Mock(returncode=0, stderr="", stdout="")

        result = validator.validate_red("test_file.py", "test_name")

        assert result.success is False
        assert "should fail" in result.message.lower()

def test_validate_green_passes_when_test_passes():
    """GREEN validation passes when test passes."""
    validator = TDDValidator()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stderr="", stdout="")

        result = validator.validate_green("test_file.py", "test_name")

        assert result.success is True
        assert "GREEN phase" in result.message

def test_validate_green_fails_when_test_fails():
    """GREEN validation fails when test still failing."""
    validator = TDDValidator()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=1, stderr="Still failing", stdout="")

        result = validator.validate_green("test_file.py", "test_name")

        assert result.success is False
        assert "still failing" in result.message.lower()

def test_validate_refactor_passes_when_all_tests_pass():
    """REFACTOR validation passes when all tests pass."""
    validator = TDDValidator()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stderr="", stdout="")

        result = validator.validate_refactor(Path("project/"))

        assert result.success is True
        assert "REFACTOR" in result.message

def test_validate_refactor_fails_on_regression():
    """REFACTOR validation fails when regression detected."""
    validator = TDDValidator()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=1, stderr="Regression!", stdout="")

        result = validator.validate_refactor(Path("project/"))

        assert result.success is False
        assert "regression" in result.message.lower()
