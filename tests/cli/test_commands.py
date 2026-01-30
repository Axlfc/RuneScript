# tests/cli/test_commands.py
import pytest
from pathlib import Path
from typer.testing import CliRunner
from src.cli.commands import app
import shutil

runner = CliRunner()

def test_cli_help_works():
    """CLI --help displays help text."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Red-Green-Refactor" in result.stdout

def test_init_command_creates_project(tmp_path, monkeypatch):
    """rgr init creates project structure."""
    monkeypatch.chdir(tmp_path)

    # We need to mock SpecGenerator and PlanGenerator to avoid real AI calls
    with pytest.MonkeyPatch.context() as m:
        m.setattr("src.cli.commands.SpecGenerator.generate", lambda self, prompt: "# Spec Content")
        m.setattr("src.cli.commands.PlanGenerator.generate", lambda self, spec: "# Plan Content")

        result = runner.invoke(app, ["init", "A test project", "--name", "test-project"])

        assert result.exit_code == 0
        assert (tmp_path / "test-project").exists()
        assert (tmp_path / "test-project" / "SPEC.md").exists()
        assert (tmp_path / "test-project" / "IMPLEMENTATION_PLAN.md").exists()

def test_status_command_shows_progress(tmp_path, monkeypatch):
    """rgr status displays project status."""
    monkeypatch.chdir(tmp_path)

    # Create a project structure manually
    project_path = tmp_path / "test-project"
    project_path.mkdir()
    (project_path / "IMPLEMENTATION_PLAN.md").write_text("""
# Implementation Plan
## PHASE 1
- [x] Task 1
- [ ] Task 2
""")

    monkeypatch.chdir(project_path)
    result = runner.invoke(app, ["status"])

    assert result.exit_code == 0
    assert "Progress" in result.stdout
    assert "50.0%" in result.stdout
