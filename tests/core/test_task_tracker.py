# tests/core/test_task_tracker.py
import pytest
from pathlib import Path
from src.core.task_tracker import TaskTracker
from src.core.plan_parser import PlanParser, Task

@pytest.fixture
def plan_file(tmp_path):
    """Create a sample plan file."""
    plan = tmp_path / "IMPLEMENTATION_PLAN.md"
    content = """# Implementation Plan
## PHASE 1
- [ ] Task 1: First task
- [ ] Task 2: Second task
- [ ] Task 3: Third task
- [ ] Task 4: Fourth task
- [ ] Task 5: Fifth task

## Progress
- Total Tasks: 5
- Completed: 0
- Remaining: 5
- Blocked: 0
"""
    # Ensure it's long enough for validator
    content = content.ljust(200, '-')
    plan.write_text(content)
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
    assert "- Remaining: 4" in content

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

def test_backups_created_on_update(plan_file):
    """Verifies that backups are created before modifications."""
    parser = PlanParser()
    tasks = parser.parse(plan_file)

    tracker = TaskTracker()
    tracker.mark_completed(plan_file, tasks[0])

    backup_dir = plan_file.parent / ".plan_backups"
    assert backup_dir.exists()
    assert len(list(backup_dir.glob("plan_*.md"))) >= 1

def test_rollback_to_valid_backup(plan_file):
    """Verifies restoration of a valid backup."""
    from src.core.task_tracker import PlanVersionControl
    from src.core.plan_validator import PlanValidator

    pvc = PlanVersionControl(plan_file)
    validator = PlanValidator(min_tasks=1)

    # Create a valid backup
    valid_content = plan_file.read_text().ljust(150, '-')
    valid_backup = pvc.backup_dir / "plan_valid.md"
    valid_backup.write_text(valid_content)

    # Corrupt current plan
    plan_file.write_text("CORRUPT")

    # Rollback
    assert pvc.rollback_to_last_valid(validator) is True
    assert "## PHASE 1" in plan_file.read_text()
