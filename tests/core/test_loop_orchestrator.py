# tests/core/test_loop_orchestrator.py
import pytest
from pathlib import Path
from src.core.loop_orchestrator import LoopOrchestrator
import threading
import time
from unittest.mock import Mock, patch

@pytest.fixture
def mock_project(tmp_path):
    (tmp_path / "SPEC.md").write_text("# Spec")
    (tmp_path / "IMPLEMENTATION_PLAN.md").write_text("""
## PHASE 1
- [ ] Task 1
- [ ] Task 2
""")
    (tmp_path / "NIA_PROMPT.md").write_text("# Prompt")
    return tmp_path

def test_loop_can_be_stopped(mock_project):
    """Loop stops when cancellation token is set."""
    orchestrator = LoopOrchestrator(mock_project)
    # Mock setup to avoid slow venv creation
    orchestrator._setup_environment = Mock()

    stop_event = threading.Event()

    # Mock AI client to simulate work
    with patch.object(orchestrator.ai_client, "execute_nia_iteration") as mock_exec:
        def mock_work(*args, **kwargs):
            time.sleep(0.5)
            return Mock(files={"test.py": "code"}, test_file=None, test_name=None)

        mock_exec.side_effect = mock_work

        # Start loop in thread
        thread = threading.Thread(
            target=lambda: orchestrator.run(max_iterations=10, stop_event=stop_event)
        )
        thread.start()

        # Give it a bit of time
        time.sleep(0.2)
        assert thread.is_alive()

        # Stop it
        stop_event.set()
        thread.join(timeout=5)

        assert not thread.is_alive()

def test_loop_stops_between_iterations(mock_project):
    """Loop stops between iterations if stop_event is set."""
    orchestrator = LoopOrchestrator(mock_project)
    # Mock setup to avoid slow venv creation
    orchestrator._setup_environment = Mock()
    stop_event = threading.Event()

    # Mock AI client to return quickly
    with patch.object(orchestrator.ai_client, "execute_nia_iteration") as mock_exec:
        mock_exec.return_value = Mock(files={"test.py": "code"}, test_file=None, test_name=None)

        # We'll set the stop_event after the first iteration
        # Actually, we can just run it once and check if it respects it.

        # I'll use a counter in the mock to set the stop event
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            stop_event.set() # Stop after first call
            return Mock(files={"test.py": "code"}, test_file=None, test_name=None)

        mock_exec.side_effect = side_effect

        result = orchestrator.run(max_iterations=10, stop_event=stop_event)

        assert result.status == "STOPPED"
        assert call_count == 1
