import os
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.core.loop_orchestrator import LoopOrchestrator

@pytest.mark.integration
def test_autonomous_smoke_cycle(tmp_path):
    project_path = tmp_path / "smoke"
    project_path.mkdir()
    (project_path / "SPEC.md").write_text("# Spec Content")
    (project_path / "NIA_PROMPT.md").write_text("# Prompt Content")

    # Create .nia_config.json to set tech_stack
    config = {
        "tech_stack": "python_backend",
        "tech_config": {
            "test_command": "{python} -m pytest {test_file}"
        }
    }
    (project_path / ".nia_config.json").write_text(json.dumps(config))

    # Create a valid plan that passes PlanValidator (needs to be long enough)
    plan_content = "# IMPLEMENTATION PLAN\n\n## PHASE 1: Initial Setup\n- [ ] Task 1: Create basic app\n\n" + ("x" * 200)
    plan_path = project_path / "IMPLEMENTATION_PLAN.md"
    plan_path.write_text(plan_content, encoding='utf-8')

    # Mock dependencies
    with patch("src.core.loop_orchestrator.nIAClaudeClient") as mock_ai_cls, \
         patch("subprocess.run") as mock_run, \
         patch("src.core.loop_orchestrator.ConfigManager") as mock_config_cls, \
         patch("src.core.loop_orchestrator.IntelligenceOrchestrator"), \
         patch("src.core.loop_orchestrator.GitBasedFileManager") as mock_git_cls, \
         patch("src.core.loop_orchestrator.SecurityAuditor"):

        # Setup Config Mock
        mock_config = mock_config_cls.return_value
        mock_feedback = MagicMock()
        mock_feedback.max_events_per_second = 10.0
        mock_config.get_feedback_config.return_value = mock_feedback

        mock_intel = MagicMock()
        mock_config.get_intelligence_config.return_value = mock_intel

        # Setup Git Manager Mock
        mock_git = mock_git_cls.return_value
        mock_git.generate_patch.return_value = ("patch.diff", "diff.txt")

        # Setup AI Mock
        mock_ai = mock_ai_cls.return_value

        # Iteration 1: Return a test and implementation
        mock_response = MagicMock()
        mock_response.files = {
            "app.py": "def add(a,b): return a+b",
            "tests/test_app.py": "from app import add\ndef test_add(): assert add(2,3) == 5"
        }
        mock_response.test_file = "tests/test_app.py"
        mock_response.status = "SUCCESS"
        mock_response._identify_test_file.return_value = "tests/test_app.py"

        mock_ai.execute_nia_iteration.return_value = mock_response

        # Subprocess mocks for tests
        mock_run.return_value = Mock(returncode=0, stdout="Passed", stderr="")

        orchestrator = LoopOrchestrator(project_path)

        with patch.object(orchestrator, "validator") as mock_v:
            mock_v.validate_red.return_value = MagicMock(success=True)
            mock_v.validate_green.return_value = MagicMock(success=True)
            mock_v.validate_refactor.return_value = MagicMock(success=True)

            result = orchestrator.run(max_iterations=1)

            assert result.status in ["ALL_COMPLETE", "MAX_ITERATIONS"]
