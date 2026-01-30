# tests/core/test_plan_parser.py
import pytest
from pathlib import Path
from src.core.plan_parser import PlanParser, Task

@pytest.fixture
def sample_plan(tmp_path):
    """Create a sample implementation plan."""
    plan_file = tmp_path / "IMPLEMENTATION_PLAN.md"
    plan_file.write_text("""
# Implementation Plan

## PHASE 1: Setup
- [ ] Task 1: Setup database
- [x] Task 2: Configure API
- [?] Task 3: Deploy BLOCKED: needs approval

## PHASE 2: Features
- [ ] Task 4: Implement login
""")
    return plan_file

def test_parse_identifies_pending_tasks(sample_plan):
    """Parser correctly identifies pending tasks."""
    parser = PlanParser()
    tasks = parser.parse(sample_plan)

    pending = [t for t in tasks if t.status == "pending"]
    assert len(pending) == 2
    assert "Task 1" in pending[0].description
    assert "Task 4" in pending[1].description

def test_parse_identifies_completed_tasks(sample_plan):
    """Parser correctly identifies completed tasks."""
    parser = PlanParser()
    tasks = parser.parse(sample_plan)

    completed = [t for t in tasks if t.status == "completed"]
    assert len(completed) == 1
    assert "Task 2" in completed[0].description

def test_parse_identifies_blocked_tasks(sample_plan):
    """Parser correctly identifies blocked tasks."""
    parser = PlanParser()
    tasks = parser.parse(sample_plan)

    blocked = [t for t in tasks if t.status == "blocked"]
    assert len(blocked) == 1
    assert "Task 3" in blocked[0].description
    assert "BLOCKED" in blocked[0].description

def test_find_next_pending_returns_first(sample_plan):
    """Parser returns first pending task."""
    parser = PlanParser()
    tasks = parser.parse(sample_plan)
    next_task = parser.find_next_pending(tasks)

    assert next_task is not None
    assert "Task 1" in next_task.description

def test_find_next_pending_returns_none_when_all_complete(tmp_path):
    """Parser returns None when all tasks complete."""
    plan_file = tmp_path / "IMPLEMENTATION_PLAN.md"
    plan_file.write_text("""
- [x] Task 1
- [x] Task 2
""")

    parser = PlanParser()
    tasks = parser.parse(plan_file)
    next_task = parser.find_next_pending(tasks)

    assert next_task is None

def test_parse_handles_empty_file(tmp_path):
    """Parser handles empty plan file gracefully."""
    plan_file = tmp_path / "IMPLEMENTATION_PLAN.md"
    plan_file.write_text("")

    parser = PlanParser()
    tasks = parser.parse(plan_file)

    assert tasks == []

def test_parse_handles_malformed_file(tmp_path):
    """Parser handles malformed plan file gracefully."""
    plan_file = tmp_path / "IMPLEMENTATION_PLAN.md"
    plan_file.write_text("""
This is not a valid plan file.
It has no task markers at all.
""")

    parser = PlanParser()
    tasks = parser.parse(plan_file)

    assert tasks == []
