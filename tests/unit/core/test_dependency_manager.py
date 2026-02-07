import pytest
from unittest.mock import MagicMock, patch
from src.core.dependency_manager import DependencyManagementUnit

def test_dependency_manager_init():
    dm = DependencyManagementUnit(project_path=".")
    assert dm.project_path == "."

def test_save_requirements(tmp_path):
    dm = DependencyManagementUnit(project_path=tmp_path)
    dm.save_requirements(["requests", "pytest"])
    req_file = tmp_path / "requirements.txt"
    assert req_file.exists()
    assert "requests" in req_file.read_text()
