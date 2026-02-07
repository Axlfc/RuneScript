import pytest
import os
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

def test_run_initial_tests(lifecycle_manager, tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_1.py").write_text("pass")

    with patch("src.core.ProjectLifecycleManager.run_pytest", return_value=(True, "OK", "")) as mock_run:
        lifecycle_manager._run_initial_tests(str(tmp_path))
        assert mock_run.called

def test_pause_project(lifecycle_manager, mock_controller):
    lifecycle_manager.generation_in_progress = True
    lifecycle_manager.pause_project()
    assert mock_controller.ui_manager.log_output.called

def test_detect_project_type_complex(lifecycle_manager):
    assert 'node' in lifecycle_manager._detect_project_type("Uses node and react")
    assert 'web' in lifecycle_manager._detect_project_type("simple landing page")
