import pytest
from unittest.mock import MagicMock
from src.core.subtask_manager import SubtaskManager

def test_subtask_manager_flow():
    state = MagicMock()
    log_fn = MagicMock()
    sm = SubtaskManager(state=state, log_fn=log_fn)

    sm.create_subtask("t1", "desc")
    assert sm.get_subtask_status("t1")["status"] == "pending"

    sm.start_subtask("t1")
    assert sm.get_subtask_status("t1")["status"] == "in_progress"

    sm.complete_subtask("t1", result="ok")
    assert sm.get_subtask_status("t1")["status"] == "completed"
    assert sm.get_subtask_result("t1") == "ok"

def test_subtask_dependencies():
    state = MagicMock()
    log_fn = MagicMock()
    sm = SubtaskManager(state=state, log_fn=log_fn)

    sm.create_subtask("t1", "desc 1")
    sm.create_subtask("t2", "desc 2", dependencies=["t1"])

    assert sm.start_subtask("t2") is False

    sm.start_subtask("t1")
    sm.complete_subtask("t1")

    # After t1 completes, t2 should automatically start because of _check_dependent_tasks
    assert sm.get_subtask_status("t2")["status"] == "in_progress"
