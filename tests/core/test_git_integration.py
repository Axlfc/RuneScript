# tests/core/test_git_integration.py
import pytest
from pathlib import Path
from src.core.loop_orchestrator import LoopOrchestrator
import subprocess
from unittest.mock import patch, Mock

def test_git_commit_delegates_to_git_manager(tmp_path):
    """_git_commit delegates work to git_manager."""
    orchestrator = LoopOrchestrator(tmp_path)

    with patch.object(orchestrator.git_manager, "create_checkpoint") as mock_checkpoint:
        orchestrator._git_commit("test message")
        mock_checkpoint.assert_called_once_with("test message")

def test_git_commit_handles_error_gracefully(tmp_path):
    """_git_commit handles exceptions in git_manager gracefully."""
    orchestrator = LoopOrchestrator(tmp_path)

    with patch.object(orchestrator.git_manager, "create_checkpoint") as mock_checkpoint:
        mock_checkpoint.side_effect = Exception("Git error")

        # Should not crash
        orchestrator._git_commit("test message")
        mock_checkpoint.assert_called_once()
