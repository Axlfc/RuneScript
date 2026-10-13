import pytest
import os
import shutil
import tempfile
from src.tools.fs_tools import (
    fs_read_file, fs_write_file, fs_list_directory, fs_apply_diff, fs_file_exists,
    resolve_and_validate_path, MAX_WRITE_BYTES
)

pytestmark = pytest.mark.asyncio

@pytest.fixture
def tmp_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("Hello RuneScript\n", encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src" / "main.py").write_text("print('main')\n", encoding="utf-8")
    return str(repo)

async def test_fs_read_file_success(tmp_repo):
    res = await fs_read_file(tmp_repo, "README.md")
    assert res["content"] == "Hello RuneScript\n"
    assert res["truncated"] is False

async def test_fs_write_file_and_backup(tmp_repo):
    # Initial write
    res1 = await fs_write_file(tmp_repo, "test.txt", "Initial content", create_dirs=True)
    assert res1["bytes_written"] == len("Initial content")
    assert res1["backup_created"] is None

    # Overwrite - should trigger backup
    res2 = await fs_write_file(tmp_repo, "test.txt", "Updated content")
    assert res2["backup_created"] is not None
    assert os.path.exists(res2["backup_created"])

async def test_fs_list_directory(tmp_repo):
    res = await fs_list_directory(tmp_repo, ".")
    names = [e["name"] for e in res["entries"]]
    assert "README.md" in names
    assert "src" in names

async def test_fs_apply_diff(tmp_repo):
    diff = "<<<<<<< SEARCH\nHello RuneScript\n=======\nHello RuneScript MCP Diff Applied\n>>>>>>> REPLACE\n"
    res = await fs_apply_diff(tmp_repo, "README.md", diff)
    assert res["applied_blocks"] == 1
    assert res["backup_created"] is not None

    read_res = await fs_read_file(tmp_repo, "README.md")
    assert read_res["content"] == "Hello RuneScript MCP Diff Applied\n"

async def test_fs_file_exists(tmp_repo):
    res1 = await fs_file_exists(tmp_repo, "README.md")
    assert res1["exists"] is True
    assert res1["is_file"] is True

    res2 = await fs_file_exists(tmp_repo, "non_existent.txt")
    assert res2["exists"] is False

async def test_security_path_traversal_blocked(tmp_repo):
    with pytest.raises(PermissionError) as exc_info:
        await fs_read_file(tmp_repo, "../../etc/passwd")
    assert "Path Traversal Guard" in str(exc_info.value)

async def test_security_out_of_bounds_symlink_blocked(tmp_repo):
    outside_file = tempfile.NamedTemporaryFile(delete=False)
    outside_file.write(b"secret")
    outside_file.close()

    symlink_path = os.path.join(tmp_repo, "symlink_secret.txt")
    os.symlink(outside_file.name, symlink_path)

    with pytest.raises(PermissionError) as exc_info:
        await fs_read_file(tmp_repo, "symlink_secret.txt")
    assert "Path Traversal Guard" in str(exc_info.value) or "Symlink Guard" in str(exc_info.value)
    os.remove(outside_file.name)

async def test_security_write_size_exceeded_blocked(tmp_repo):
    huge_content = "A" * (MAX_WRITE_BYTES + 100)
    with pytest.raises(ValueError) as exc_info:
        await fs_write_file(tmp_repo, "huge.txt", huge_content, create_dirs=True)
    assert "exceeds maximum write size" in str(exc_info.value)
