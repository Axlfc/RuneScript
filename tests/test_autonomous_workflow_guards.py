import json
import subprocess

from src.agents.feature_implementation_agent import FeatureImplementationAgent
from src.agents.test_generation_agent import TestGenerationAgent
from src.core.automated_testing import AutomatedTestingFramework


class _FakeState:
    def __init__(self, code_files=None):
        self.state = {"code_files": code_files or {}}


class _FakeAgent:
    def __init__(self):
        self.tdd = object()
        self.project_scope = {"project_name": "HAIS", "description": "multi-agent system"}
        self.bootstrap_metadata = {
            "project_name": "HAIS",
            "project_description": "HAIS autonomous multi-agent system",
        }
        self.current_iteration_goal = "Implement the repository inspector"
        self.feedback_buffer = None
        self.architecture = {
            "project_name": "HAIS",
            "testing_framework": "pytest",
            "architecture_summary": "Backend plus dashboard over WebSocket",
        }
        self.state = _FakeState({
            "hais/inspector.py": "def inspect_repository():\n    return {}\n"
        })
        self.last_stage = None
        self.last_context = None

    def get_relevant_rag_context(self, *args, **kwargs):
        return []

    def process_prompt_with_ai(self, stage, context):
        self.last_stage = stage
        self.last_context = context
        if stage == "test_generation":
            return json.dumps([{
                "name": "test_inspector",
                "description": "inspector works",
                "module": "test_inspector.py",
                "content": "def test_inspector():\n    assert True\n",
            }])
        if stage == "feature_implementation":
            return json.dumps({
                "implemented_modules": [],
                "test_coverage": {},
            })
        raise AssertionError(f"unexpected stage: {stage}")


def test_full_stack_web_architecture_does_not_disable_test_generation():
    agent = _FakeAgent()
    generator = TestGenerationAgent(agent)

    tests = generator.generate_tests(agent.architecture)

    assert len(tests) == 1
    assert agent.last_stage == "test_generation"
    assert agent.last_context["bootstrap_metadata"]["project_name"] == "HAIS"
    assert agent.last_context["iteration_goal"] == "Implement the repository inspector"


def test_design_only_project_can_explicitly_skip_test_generation():
    agent = _FakeAgent()
    generator = TestGenerationAgent(agent)

    tests = generator.generate_tests({
        "project_name": "Poster",
        "project_type": "design_only",
        "testing_framework": "manual",
    })

    assert tests == []
    assert agent.last_stage is None


def test_implementation_context_preserves_project_identity_files_and_failure():
    agent = _FakeAgent()
    agent.feedback_buffer = {
        "success": False,
        "test_errors": "ImportError: cannot import name parse_features",
    }
    implementation = FeatureImplementationAgent(agent)

    result = implementation.implement_features([{
        "name": "test_inspector",
        "module": "test_inspector.py",
        "content": "def test_inspector():\n    assert True\n",
    }])

    assert result["implemented_modules"] == []
    assert agent.last_stage == "feature_implementation"
    assert agent.last_context["project_name"] == "HAIS"
    assert agent.last_context["iteration_goal"] == "Implement the repository inspector"
    assert agent.last_context["previous_feedback"]["success"] is False
    assert agent.last_context["existing_files"][0]["filename"] == "hais/inspector.py"


def test_testing_framework_records_pytest_diagnostics(monkeypatch, tmp_path):
    completed = subprocess.CompletedProcess(
        args=["python", "-m", "pytest"],
        returncode=1,
        stdout="1 failed",
        stderr="traceback",
    )

    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: completed)

    framework = AutomatedTestingFramework(str(tmp_path))
    assert framework.run_tests() is False
    assert framework.last_result["returncode"] == 1
    assert framework.last_result["stdout"] == "1 failed"
    assert framework.last_result["stderr"] == "traceback"
