import pytest
from pathlib import Path
from src.core.issue_manager import IssueManager

@pytest.fixture
def im(tmp_path):
    return IssueManager(project_path=tmp_path)

def test_create_issue(im):
    im.create_issue(category="Testing", priority="High", description="Desc", title="Test Issue")
    issues = im.get_issues()
    assert len(issues) == 1
    assert issues[0]['description'] == "Desc"
    assert issues[0]['title'] == "Test Issue"

def test_resolve_issue(im):
    im.create_issue(category="Testing", priority="High", description="Desc", title="Test Issue")
    issues = im.get_issues()
    issue_id = issues[0]['id']
    im.resolve_issue(issue_id, resolution="Fixed it")

    updated_issues = im.get_issues()
    assert updated_issues[0]['status'] == "Resolved"
    assert updated_issues[0]['resolution'] == "Fixed it"
