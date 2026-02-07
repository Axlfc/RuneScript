import pytest
import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch
from src.core.tdd_validator import TDDValidator, ValidationResult

@pytest.fixture
def validator():
    return TDDValidator()

def test_extract_dependencies_from_test_advanced(validator, tmp_path):
    test_file = tmp_path / "test_complex.py"
    test_file.write_text("""
import os
import bs4
files = ['index.html', 'css/style.css']
""")
    deps = validator._extract_file_dependencies_from_test(tmp_path, test_file)
    assert "index.html" in deps
    assert "css/style.css" in deps

def test_run_test_with_streaming(validator, tmp_path):
    test_file = tmp_path / "test.py"
    test_file.write_text("print('streaming')")

    with patch("subprocess.Popen") as mock_popen:
        mock_process = Mock()
        mock_process.stdout = ["line 1", "line 2"]
        mock_process.stderr = []
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process

        callback = Mock()
        result = validator._run_test(tmp_path, "test.py", output_callback=callback)

        assert callback.called
        assert result.returncode == 0

def test_run_all_tests_python_pytest(validator, tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_1.py").write_text("import pytest\ndef test_a(): pass")

    with patch.object(validator.sandbox, "execute") as mock_exec:
        mock_exec.return_value = {'success': True, 'stdout': 'OK', 'stderr': ''}
        validator._run_all_tests(tmp_path)
        # Should detect 'import pytest' and use sandbox.execute with pytest main
        assert "pytest.main" in mock_exec.call_args[0][0]

def test_run_all_tests_no_pytest(validator, tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_simple.py").write_text("assert 1 == 1")

    with patch.object(validator.sandbox, "execute") as mock_exec, \
         patch.object(validator.analyzer, "analyze") as mock_analyze:
        mock_analyze.return_value = {'is_safe': True, 'threats': []}
        mock_exec.return_value = {'success': True, 'stdout': 'OK', 'stderr': ''}

        validator._run_all_tests(tmp_path)
        # Should run as standalone script in sandbox
        assert "pytest.main" not in mock_exec.call_args[0][0]

def test_validate_red_execution_error_specific(validator):
    with patch.object(validator, "_run_test") as mock_run:
        # Specific execution error
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="ModuleNotFoundError: No module named 'selenium'")
        result = validator.validate_red(Path("."), "test.py")
        assert result.success is False
        assert "Execution error" in result.message
