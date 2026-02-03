import pytest
from src.prompts.templates import (
    get_spec_system_prompt,
    get_plan_system_prompt,
    get_reviewer_prompt,
    get_nia_iteration_prompt
)

def test_spec_prompt_formatting():
    tools = {
        'python': True,
        'python_path': '/usr/bin/python3',
        'node': False,
        'npm': False
    }
    prompt = get_spec_system_prompt(tools)
    assert "Python is available: True" in prompt
    assert "/usr/bin/python3" in prompt

def test_plan_prompt_formatting():
    tech_info = '{"lang": "python"}'
    prompt = get_plan_system_prompt(tech_info)
    assert '{"lang": "python"}' in prompt
    # Verify double braces remained as single braces in output
    assert '"phases": [' in prompt
    assert '"tasks": [' in prompt

def test_reviewer_prompt_formatting():
    prompt = get_reviewer_prompt("request", "spec", "plan")
    assert "SOLICITUD ORIGINAL:\nrequest" in prompt
    assert "ESPECIFICACIÓN GENERADA:\nspec" in prompt
    assert '"approved": true/false' in prompt

def test_nia_iteration_prompt_formatting():
    prompt = get_nia_iteration_prompt("base_prompt", "test_inst", "spec", "plan", "context", "task")
    assert "base_prompt" in prompt
    assert "test_inst" in prompt
    assert "=== NEXT TASK ===\ntask" in prompt
