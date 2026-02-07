import pytest
from pathlib import Path
from src.core.project_context import ProjectContext

def test_project_context_init(tmp_path):
    ctx = ProjectContext(project_name="Test", description="Desc", path=str(tmp_path))
    assert ctx.project_name == "Test"
    assert ctx.description == "Desc"
    assert ctx.path == str(tmp_path)

def test_project_context_to_dict(tmp_path):
    ctx = ProjectContext(project_name="Test", description="Desc", path=str(tmp_path))
    d = ctx.to_dict()
    assert d["project_name"] == "Test"
    assert "last_updated" in d

def test_save_load_context(tmp_path):
    ctx = ProjectContext(project_name="Test", description="Desc", path=str(tmp_path))
    ctx.save_context()

    ctx2 = ProjectContext.load_context(str(tmp_path))
    assert ctx2.project_name == "Test"
    assert ctx2.description == "Desc"
