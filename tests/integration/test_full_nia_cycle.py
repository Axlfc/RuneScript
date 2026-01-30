# tests/integration/test_full_nia_cycle.py
import pytest
from pathlib import Path
from src.core.loop_orchestrator import LoopOrchestrator
from src.core.plan_parser import PlanParser
import subprocess
from unittest.mock import Mock, patch

@pytest.mark.integration
def test_full_cycle_single_iteration(tmp_path, monkeypatch):
    """Complete nIA cycle for one iteration."""
    monkeypatch.chdir(tmp_path)

    # Initialize git repo manually or let LoopOrchestrator do it
    # subprocess.run(["git", "init"], cwd=tmp_path)

    # Create project files
    (tmp_path / "SPEC.md").write_text("# Test Project")
    (tmp_path / "IMPLEMENTATION_PLAN.md").write_text("""
# Implementation Plan
## PHASE 1
- [ ] Task 1: Create hello function

## Progress
- Total Tasks: 1
- Completed: 0
- Remaining: 1
- Blocked: 0
""")
    (tmp_path / "NIA_PROMPT.md").write_text("# Prompt")
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()

    orchestrator = LoopOrchestrator(tmp_path)

    # Mock Claude client to avoid real API calls
    mock_response = Mock()
    mock_response.files = {"src/hello.py": "def hello(): return 'world'", "tests/test_hello.py": "from src.hello import hello\ndef test_hello(): assert hello() == 'world'"}
    mock_response.test_file = "tests/test_hello.py"
    mock_response.test_name = "test_hello"

    with patch.object(orchestrator.ai_client, "execute_nia_iteration", return_value=mock_response):
        # Also mock validator to avoid actually running pytest on these temporary files
        # unless we want a real integration test. Let's try real first, but it might fail due to env.
        # Actually, let's mock subprocess.run inside TDDValidator to return success.
        with patch("subprocess.run") as mock_sub_run:
            # We need to handle multiple calls to subprocess.run
            # 1. git version check
            # 2. git init
            # 3. TDDValidator._run_test (RED) -> should return 1
            # 4. TDDValidator._run_test (GREEN) -> should return 0
            # 5. TDDValidator._run_all_tests (REFACTOR) -> should return 0
            # 6. git add
            # 7. git commit

            def side_effect(cmd, *args, **kwargs):
                if "pytest" in cmd:
                    if "tests/test_hello.py::test_hello" in cmd and mock_sub_run.call_count <= 4: # Simplified logic
                         return Mock(returncode=1, stdout="", stderr="RED")
                    return Mock(returncode=0, stdout="", stderr="GREEN")
                return Mock(returncode=0, stdout="", stderr="")

            mock_sub_run.side_effect = side_effect

            result = orchestrator.run(max_iterations=1)

    # Verify result
    assert result.status == "ALL_COMPLETE" or result.iterations == 1

    # Verify plan was updated
    parser = PlanParser()
    tasks = parser.parse(tmp_path / "IMPLEMENTATION_PLAN.md")
    assert tasks[0].status == "completed"

    # Verify files were written
    assert (tmp_path / "src/hello.py").exists()
    assert (tmp_path / "tests/test_hello.py").exists()
