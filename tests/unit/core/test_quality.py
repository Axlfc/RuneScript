import pytest
from src.core.quality import QualityChecker

def test_check_placeholders():
    checker = QualityChecker()
    assert checker.check_placeholders({"app.py": "..."}) == "app.py"
