import pytest
from src.core.iteration_state import IterationState

def test_iteration_state():
    state = IterationState("T")
    state.register_attempt({"f": "c"}, True)
    assert state.attempt_number == 1
