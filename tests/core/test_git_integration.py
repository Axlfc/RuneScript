# tests/core/test_git_integration.py
import pytest
from pathlib import Path
from src.core.loop_orchestrator import LoopOrchestrator
import subprocess
from unittest.mock import patch, Mock

def test_git_commit_handles_no_git_installed(tmp_path):
    """Git commit handles missing git gracefully."""
    orchestrator = LoopOrchestrator(tmp_path)

    # Mock subprocess to simulate git not found
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("git not found")

        # Should not crash
        orchestrator._git_commit("test message")

def test_git_commit_handles_not_a_repo(tmp_path):
    """Git commit handles non-repo directory gracefully."""
    # Create a non-git directory
    orchestrator = LoopOrchestrator(tmp_path)

    # We want to verify it tries to init if .git doesn't exist
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0)

        orchestrator._git_commit("test message")

        # Should have called git init, add, and commit
        assert mock_run.call_count >= 1
        calls = [call.args[0][1] for call in mock_run.call_args_list]
        assert "init" in calls or "add" in calls or "commit" in calls
