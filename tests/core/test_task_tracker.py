# tests/core/test_task_tracker.py
import pytest
from pathlib import Path
from src.core.task_tracker import TaskTracker
from src.core.plan_parser import PlanParser, Task

@pytest.fixture
def plan_file(tmp_path):
    """Create a sample plan file."""
    plan = tmp_path / "IMPLEMENTATION_PLAN.md"
    plan.write_text("""
## PHASE 1
- [ ] Task 1: First task
- [ ] Task 2: Second task

## Progress
- Total Tasks: 2
- Completed: 0
- Remaining: 2
- Blocked: 0
""")
    return plan

def test_mark_completed_updates_file(plan_file):
    """Marking task as completed updates the file correctly."""
    parser = PlanParser()
    tasks = parser.parse(plan_file)
    first_task = tasks[0]

    tracker = TaskTracker()
    tracker.mark_completed(plan_file, first_task)

    # Re-parse and verify
    updated_tasks = parser.parse(plan_file)
    assert updated_tasks[0].status == "completed"
    assert updated_tasks[1].status == "pending"

    # Verify statistics update
    content = plan_file.read_text()
    assert "- Completed: 1" in content
    assert "- Remaining: 1" in content

def test_mark_blocked_updates_file_with_reason(plan_file):
    """Marking task as blocked includes reason."""
    parser = PlanParser()
    tasks = parser.parse(plan_file)
    first_task = tasks[0]

    tracker = TaskTracker()
    tracker.mark_blocked(plan_file, first_task, "Missing dependency")

    # Re-parse and verify
    updated_tasks = parser.parse(plan_file)
    assert updated_tasks[0].status == "blocked"
    assert "BLOCKED: Missing dependency" in updated_tasks[0].description

    # Verify statistics update
    content = plan_file.read_text()
    assert "- Blocked: 1" in content

def test_mark_completed_preserves_other_tasks(plan_file):
    """Marking one task doesn't affect others."""
    parser = PlanParser()
    tasks = parser.parse(plan_file)
    first_task = tasks[0]

    tracker = TaskTracker()
    tracker.mark_completed(plan_file, first_task)

    # Verify second task unchanged
    updated_tasks = parser.parse(plan_file)
    assert updated_tasks[1].status == "pending"
    assert "Second task" in updated_tasks[1].description
