import pytest
from unittest.mock import MagicMock, patch
from src.core.ProjectLifecycleManager import ProjectLifecycleManager

@pytest.fixture
def plm():
    controller = MagicMock()
    return ProjectLifecycleManager(controller=controller)

def test_initialization(plm):
    assert plm.controller is not None

def test_start_nia_loop_no_orchestrator(plm):
    with patch("src.core.ProjectLifecycleManager.LoopOrchestrator") as mock_orch:
        plm._run_nia_autonomous_loop("prompt", ".")
        assert mock_orch.called

def test_stop_project(plm):
    plm.orchestrator = MagicMock()
    plm.generation_in_progress = True
    plm.stop_project()
    assert plm.stop_event.is_set()
