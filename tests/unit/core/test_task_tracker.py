import pytest
from pathlib import Path
from src.core.task_tracker import TaskTracker
from src.core.plan_parser import Task

@pytest.fixture
def plan_file(tmp_path):
    path = tmp_path / "IMPLEMENTATION_PLAN.md"
    path.write_text("# Plan\n## PHASE 1\n- [ ] Task 1\n" + "X" * 150)
    return path

def test_mark_completed(plan_file):
    tracker = TaskTracker()
    task = Task(status="pending", description="Task 1", phase="1", line_number=3)
    tracker.mark_completed(plan_file, task)
    assert "[x]" in plan_file.read_text()

def test_mark_blocked(plan_file):
    tracker = TaskTracker()
    task = Task(status="pending", description="Task 1", phase="1", line_number=3)
    tracker.mark_blocked(plan_file, task, "Reason")
    assert "[?] BLOCKED: Reason" in plan_file.read_text()
