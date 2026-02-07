import pytest
from src.core.automated_testing import AutomatedTestingFramework
from unittest.mock import patch, Mock

def test_run_tests():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0)
        framework = AutomatedTestingFramework(".")
        assert framework.run_tests() is True
