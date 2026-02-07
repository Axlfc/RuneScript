import pytest
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.core.loop_orchestrator import LoopOrchestrator, LoopResult
from src.core.plan_parser import Task
from src.core.tdd_validator import ValidationResult

@pytest.fixture
def project_path(tmp_path):
    (tmp_path / "SPEC.md").write_text("# Test Spec")
    (tmp_path / "IMPLEMENTATION_PLAN.md").write_text("""# Plan
## PHASE 1
- [ ] Task 1
""")
    (tmp_path / "NIA_PROMPT.md").write_text("# Prompt")
    return tmp_path

@pytest.fixture
def orchestrator(project_path):
    with patch("src.core.loop_orchestrator.ConfigManager") as mock_config_cls, \
         patch("src.core.loop_orchestrator.IntelligenceOrchestrator"), \
         patch("src.core.loop_orchestrator.GitBasedFileManager"):

        mock_config = mock_config_cls.return_value
        feedback_mock = MagicMock()
        feedback_mock.max_events_per_second = 10
        mock_config.get_feedback_config.return_value = feedback_mock

        intel_mock = MagicMock()
        mock_config.get_intelligence_config.return_value = intel_mock

        security_mock = MagicMock()
        security_mock.package_name_pattern = r".*"
        security_mock.safe_packages = ["selenium"]
        security_mock.pip_install_timeout = 30
        mock_config.get_security_config.return_value = security_mock

        orch = LoopOrchestrator(project_path)
        orch.parser = MagicMock()
        orch.tracker = MagicMock()
        orch.validator = MagicMock()
        orch.ai_client = MagicMock()
        orch.quality_checker = MagicMock()
        orch.issue_manager = MagicMock()
        orch.storage = MagicMock()
        orch.intelligence = MagicMock()
        orch.git_manager = MagicMock()
        orch.git_manager.generate_patch.return_value = ("patch_path", "diff_path")
        orch.git_manager._load_manifest.return_value = {"patches": []}
        orch.tech_stack = "python_backend"
        return orch

def test_full_rgr_cycle_success(orchestrator, project_path):
    mock_response = MagicMock()
    mock_response.files = {"app.py": "print('hello')", "tests/test_app.py": "def test_pass(): assert True"}
    mock_response.test_file = "tests/test_app.py"
    mock_response.test_name = "test_pass"
    mock_response.raw = "AI Response"
    mock_response._identify_test_file.return_value = "tests/test_app.py"
    orchestrator.ai_client.execute_nia_iteration.return_value = mock_response

    orchestrator.validator.validate_red.return_value = ValidationResult(True, "RED Pass")
    orchestrator.validator.validate_green.return_value = ValidationResult(True, "GREEN Pass")
    orchestrator.validator.validate_refactor.return_value = ValidationResult(True, "REFACTOR Pass")
    orchestrator.quality_checker.validate.return_value = []

    task = Task(status="pending", description="Task 1", phase="1", line_number=3)
    orchestrator.parser.parse.return_value = [task]
    orchestrator.parser.find_next_pending.side_effect = [task, None]

    with patch("src.core.loop_orchestrator.Path.exists", return_value=True), \
         patch.object(orchestrator, "_write_file", return_value=True):
        result = orchestrator.run(max_iterations=2)

    assert result.status == "ALL_COMPLETE"
