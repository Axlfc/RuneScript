import pytest
import os
import json
import uuid
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.core.ProjectLifecycleManager import ProjectLifecycleManager

@pytest.fixture
def mock_controller():
    controller = Mock()
    controller.ui_manager = Mock()
    controller.projects_base_dir = "/tmp/projects"
    controller.ai_orchestrator = Mock()
    controller.current_project = None
    return controller

@pytest.fixture
def lifecycle_manager(mock_controller):
    return ProjectLifecycleManager(mock_controller)

def test_generate_project_with_ai(lifecycle_manager, mock_controller):
    mock_controller.ui_manager.prompt_entry.get.return_value = "A new project"
    with patch("src.core.ProjectLifecycleManager.AIResponseParser.validate_prompt", return_value=True), \
         patch("src.core.ProjectLifecycleManager.AIResponseParser.sanitize_prompt", return_value="A new project"), \
         patch("src.core.ProjectLifecycleManager.threading.Thread") as mock_thread:

        lifecycle_manager.generate_project_with_ai(nia_mode=True)

        assert mock_controller.ui_manager.log_output.called
        assert mock_thread.called
        assert lifecycle_manager.generation_in_progress is True

def test_finalize_project_generation(lifecycle_manager, mock_controller, tmp_path):
    mock_controller.current_project = str(tmp_path)
    mock_controller.ui_manager.prompt_entry.get.return_value = "Prompt"

    metadata = {
        "project_name": "Test",
        "initial_files": {},
        "project_tasks": ["Task 1"]
    }

    with patch("src.core.ProjectLifecycleManager.ProjectIO.create_structure"), \
         patch("src.core.ProjectLifecycleManager.WebProjectGenerator"), \
         patch.object(lifecycle_manager, "_process_generated_files"), \
         patch.object(lifecycle_manager, "_generate_project_docs"), \
         patch.object(lifecycle_manager, "_run_initial_tests"):

        lifecycle_manager.finalize_project_generation(metadata)

        assert mock_controller.ui_manager.update_ai_plan.called
        assert lifecycle_manager.generation_in_progress is False

def test_run_nia_autonomous_loop_basic(lifecycle_manager, mock_controller, tmp_path):
    project_path = str(tmp_path)
    prompt = "Create a python app"

    with patch("src.core.ProjectLifecycleManager.GitBasedFileManager") as mock_git_cls, \
         patch("src.core.ProjectLifecycleManager.TechStackDetector") as mock_detector_cls, \
         patch("src.core.ProjectLifecycleManager.SpecGenerator") as mock_spec_cls, \
         patch("src.core.ProjectLifecycleManager.PlanGenerator") as mock_plan_cls, \
         patch("src.core.ProjectLifecycleManager.PlanReviewer") as mock_reviewer_cls, \
         patch("src.core.ProjectLifecycleManager.LoopOrchestrator") as mock_orch_cls, \
         patch.object(lifecycle_manager, "_initialize_project_files"), \
         patch.object(lifecycle_manager, "_filter_redundant_tasks"), \
         patch("src.core.ProjectLifecycleManager.PlanParser") as mock_parser_cls:

        # Setup mocks
        mock_detector = mock_detector_cls.return_value
        mock_detector.detect_from_prompt.return_value = "python_backend"
        mock_detector.get_config.return_value = {"key": "val"} # Real dict

        mock_spec = mock_spec_cls.return_value
        mock_spec.generate.return_value = "Spec content"

        mock_plan = mock_plan_cls.return_value
        mock_plan.generate.return_value = "- [ ] Task 1"
        mock_plan.validate_plan.return_value = True
        mock_plan.detect_complexity.return_value = "medium"

        mock_reviewer = mock_reviewer_cls.return_value
        mock_reviewer.review_and_improve.return_value = (True, "", {}, 1)

        mock_orch = mock_orch_cls.return_value
        mock_orch.run.return_value = Mock(status="ALL_COMPLETE", stats={})

        mock_parser = mock_parser_cls.return_value
        mock_parser.parse.return_value = []

        # Run
        lifecycle_manager._run_nia_autonomous_loop(prompt, project_path)

        assert mock_orch.run.called
        assert (tmp_path / "SPEC.md").exists()
        assert (tmp_path / "IMPLEMENTATION_PLAN.md").exists()
