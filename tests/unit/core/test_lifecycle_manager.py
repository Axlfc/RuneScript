import pytest
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch
from src.core.ProjectLifecycleManager import ProjectLifecycleManager

@pytest.fixture
def mock_controller():
    controller = Mock()
    controller.ui_manager = Mock()
    controller.projects_base_dir = "/tmp/projects"
    controller.ai_orchestrator = Mock()
    return controller

@pytest.fixture
def lifecycle_manager(mock_controller):
    return ProjectLifecycleManager(mock_controller)

def test_write_file_basic(lifecycle_manager, tmp_path):
    project_path = str(tmp_path)
    lifecycle_manager._write_file(project_path, "test.txt", "content")
    assert (tmp_path / "test.txt").exists()
    assert (tmp_path / "test.txt").read_text() == "content"

def test_detect_project_type(lifecycle_manager):
    assert 'python' in lifecycle_manager._detect_project_type("This is a Python project")
    assert 'node' in lifecycle_manager._detect_project_type("This uses npm and react")
    assert 'web' in lifecycle_manager._detect_project_type("Just simple html/css")

def test_detect_dependencies(lifecycle_manager, tmp_path):
    project_path = str(tmp_path)
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_app.py").write_text("import requests\nfrom bs4 import BeautifulSoup")
    deps = lifecycle_manager._detect_dependencies(project_path, "needs pandas")
    assert "requests" in deps
    assert "bs4" in deps
    assert "pandas" in deps

def test_generate_project_docs(lifecycle_manager, tmp_path):
    project_path = str(tmp_path)
    metadata = {
        "project_name": "TestProj",
        "project_description": "A test project",
        "key_features": ["Feature 1"],
        "project_tasks": ["Task 1"],
        "implemented_features": ["Base structure"],
        "planned_features": ["AI Loop"]
    }
    lifecycle_manager._generate_project_docs(project_path, metadata)
    assert (tmp_path / "README.md").exists()
    assert (tmp_path / "TODO.md").exists()
    assert (tmp_path / "LIST.md").exists()
    assert (tmp_path / "docs" / "DEVELOPMENT.md").exists()

def test_initialize_project_files(lifecycle_manager, tmp_path):
    with patch.object(lifecycle_manager, "_detect_project_type", return_value=['python']), \
         patch.object(lifecycle_manager, "_detect_dependencies", return_value=['pytest', 'requests']), \
         patch("subprocess.run") as mock_run, \
         patch("lib.nia_git_manager.GitBasedFileManager"):
        lifecycle_manager._initialize_project_files(tmp_path, "Test Spec")
        assert (tmp_path / "requirements.txt").exists()
        assert (tmp_path / ".gitignore").exists()
        assert (tmp_path / "README.md").exists()

def test_process_generated_files(lifecycle_manager, tmp_path):
    project_path = str(tmp_path)
    metadata = {
        "initial_files": {"index.html": "<html></html>"},
        "code_files": [{"filename": "app.py", "content": "print(1)"}],
        "test_files": [{"path": "tests/test_app.py", "content": "assert 1"}]
    }
    lifecycle_manager._process_generated_files(project_path, metadata)
    assert (tmp_path / "index.html").exists()
    assert (tmp_path / "app.py").exists()
    assert (tmp_path / "tests/test_app.py").exists()

def test_save_metrics(lifecycle_manager, tmp_path):
    project_path = str(tmp_path)
    lifecycle_manager._save_metrics(project_path, {"test": "metric"})
    metrics_file = tmp_path / "nia_metrics.json"
    assert metrics_file.exists()
    data = json.loads(metrics_file.read_text())
    assert data["test"] == "metric"

def test_run_tests(lifecycle_manager, mock_controller):
    mock_controller.current_project = "/tmp/proj"
    with patch("src.core.ProjectLifecycleManager.run_pytest", return_value=(True, "Passed", "")):
        lifecycle_manager.run_tests()
        assert mock_controller.ui_manager.log_output.called

def test_stop_project(lifecycle_manager, mock_controller):
    lifecycle_manager.generation_in_progress = True
    lifecycle_manager.stop_project()
    assert lifecycle_manager.generation_in_progress is False
    assert lifecycle_manager.stop_event.is_set()
    assert mock_controller.ai_orchestrator.stop_generation.called
