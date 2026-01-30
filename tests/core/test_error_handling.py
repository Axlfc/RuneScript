# tests/core/test_error_handling.py
import pytest
from pathlib import Path
from src.core.plan_parser import PlanParser
from src.core.task_tracker import TaskTracker
from src.core.plan_parser import Task
import os

def test_parser_handles_nonexistent_file():
    """Parser handles nonexistent file gracefully."""
    parser = PlanParser()
    tasks = parser.parse(Path("/nonexistent/file.md"))

    assert tasks == []  # Should return empty, not crash

def test_parser_handles_permission_denied(tmp_path):
    """Parser handles permission denied gracefully."""
    plan_file = tmp_path / "IMPLEMENTATION_PLAN.md"
    plan_file.write_text("- [ ] Task")

    # Make file unreadable
    os.chmod(plan_file, 0o000)

    try:
        parser = PlanParser()
        tasks = parser.parse(plan_file)
        assert tasks == []
    finally:
        # Restore permissions for cleanup
        os.chmod(plan_file, 0o644)

def test_tracker_handles_readonly_file(tmp_path):
    """TaskTracker handles readonly file gracefully."""
    plan_file = tmp_path / "IMPLEMENTATION_PLAN.md"
    plan_file.write_text("- [ ] Task")

    # Make readonly
    os.chmod(plan_file, 0o444)

    task = Task(status="pending", description="Task", phase="Test", line_number=1)
    tracker = TaskTracker()

    with pytest.raises(Exception):
        tracker.mark_completed(plan_file, task)

    # Restore permissions
    os.chmod(plan_file, 0o644)
