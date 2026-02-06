
import pytest
from src.core.plan_validator import PlanValidator

def test_validator_valid_plan():
    validator = PlanValidator(min_tasks=2)
    valid_plan = """# Implementation Plan
## PHASE 1: Setup
- [ ] Task 1
- [ ] Task 2
"""
    # Needs to be at least 100 chars
    valid_plan = valid_plan.ljust(150, '-')
    assert validator.validate(valid_plan) is True

def test_validator_placeholder_failure():
    validator = PlanValidator()
    corrupt_plan = """# Implementation Plan
## PHASE 1: Setup
- [x] Task 1
...[Rest of plan remains same]...
"""
    corrupt_plan = corrupt_plan.ljust(150, '-')
    assert validator.validate(corrupt_plan) is False

def test_validator_min_tasks_failure():
    validator = PlanValidator(min_tasks=5)
    short_plan = """# Implementation Plan
## PHASE 1: Setup
- [ ] Task 1
"""
    short_plan = short_plan.ljust(150, '-')
    assert validator.validate(short_plan) is False

def test_validator_no_phases_failure():
    validator = PlanValidator()
    no_phases = """# Implementation Plan
Just some text without any phase headers.
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3
- [ ] Task 4
- [ ] Task 5
"""
    no_phases = no_phases.ljust(150, '-')
    assert validator.validate(no_phases) is False
