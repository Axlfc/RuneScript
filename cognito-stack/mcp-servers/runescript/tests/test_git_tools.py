import pytest
import os
import subprocess
import tempfile
from src.tools.git_tools import (
    git_status, git_diff, git_branch_create, git_checkout, git_add, git_commit, git_push, git_open_pr
)

pytestmark = pytest.mark.asyncio

@pytest.fixture
def git_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "redgreenrefactor"], cwd=str(repo), check=True)
    subprocess.run(["git", "config", "user.name", "TestUser"], cwd=str(repo), check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(repo), check=True)

    (repo / "README.md").write_text("Hello Git", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=str(repo), check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=str(repo), check=True)
    return str(repo)

async def test_git_status_and_diff(git_repo):
    status1 = await git_status(git_repo)
    assert status1["clean"] is True
    assert status1["branch"] == "redgreenrefactor"

    (os.path.join(git_repo, "README.md"))
    with open(os.path.join(git_repo, "README.md"), "w") as f:
        f.write("Hello Modified Git")

    status2 = await git_status(git_repo)
    assert status2["clean"] is False
    assert "README.md" in status2["unstaged"]

    diff_res = await git_diff(git_repo, path="README.md")
    assert "Hello Modified Git" in diff_res["diff"]

async def test_security_branch_naming_guard(git_repo):
    with pytest.raises(PermissionError) as exc_info:
        await git_branch_create(git_repo, "invalid-branch-name")
    assert "Branch Guard" in str(exc_info.value)

async def test_security_commit_protected_branch_blocked(git_repo):
    with pytest.raises(PermissionError) as exc_info:
        await git_commit(git_repo, "Direct commit attempt")
    assert "Branch Protection Guard" in str(exc_info.value)

async def test_security_push_confirmation_required(git_repo):
    with pytest.raises(PermissionError) as exc_info:
        await git_push(git_repo, "jules/test-branch")
    assert "Human Confirmation Required" in str(exc_info.value)

async def test_security_open_pr_confirmation_required(git_repo):
    with pytest.raises(PermissionError) as exc_info:
        await git_open_pr(git_repo, "Title", "Body", "jules/test")
    assert "Human Confirmation Required" in str(exc_info.value)

async def test_git_end_to_end_flow(git_repo):
    # 1. Create agent branch
    branch_res = await git_branch_create(git_repo, "jules/feature-test")
    assert branch_res["created"] is True

    # 2. Modify & add
    with open(os.path.join(git_repo, "new_file.py"), "w") as f:
        f.write("print('new feature')\n")
    await git_add(git_repo, ["new_file.py"])

    # 3. Commit on feature branch
    commit_res = await git_commit(git_repo, "feat: add new feature script")
    assert commit_res["success"] is True

    # 4. Verify clean status
    status_final = await git_status(git_repo)
    assert status_final["clean"] is True
    assert status_final["branch"] == "jules/feature-test"
