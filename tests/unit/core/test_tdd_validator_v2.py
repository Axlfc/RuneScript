import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.core.tdd_validator import TDDValidator

def test_add_allowed_import():
    v = TDDValidator()
    v.add_allowed_import("new_module")
    assert "new_module" in v.allowed_imports

@patch("src.core.tdd_validator.SecureSandbox")
@patch("src.core.tdd_validator.CodeSecurityAnalyzer")
def test_run_test_python_sandbox(mock_analyzer, mock_sandbox, tmp_path):
    v = TDDValidator()
    mock_analyzer.return_value.analyze.return_value = {"is_safe": True, "threats": []}
    mock_sandbox.return_value.execute_test.return_value = {"success": True, "stdout": "Passed", "stderr": "", "error": None}

    test_file = tmp_path / "test_simple.py"
    test_file.write_text("def test_pass(): assert True")

    res = v._run_test(tmp_path, str(test_file))
    assert res.returncode == 0
    assert "Passed" in res.stdout

def test_extract_file_dependencies():
    v = TDDValidator()
    tmp_file = Path("test_deps.py")
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.read_text", return_value='os.path.join("data", "config.json")'):
            deps = v._extract_file_dependencies_from_test(Path("."), tmp_file)
            assert "config.json" in deps
