import pytest
from src.core.plan_validator import PlanValidator

def test_validate_plan():
    validator = PlanValidator(min_tasks=1)
    content = "# Plan\n## PHASE 1\n- [ ] Task 1\n" + "X" * 150
    assert validator.validate(content) is True

def test_validate_too_short():
    validator = PlanValidator(min_tasks=1)
    assert validator.validate("Too short") is False

def test_extract_phases():
    content = "# Plan\n## PHASE 1: One\n## PHASE 2: Two"
    phases = PlanValidator.extract_phases(content)
    assert len(phases) == 2
