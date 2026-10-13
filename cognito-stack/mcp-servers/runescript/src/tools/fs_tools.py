import os
import shutil
import time
import hashlib
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# Maximum allowed write size (5MB)
MAX_WRITE_BYTES = 5_242_880

class FsReadFileInput(BaseModel):
    path: str = Field(..., description="Path relative to RUNESCRIPT_PATH.")
    max_bytes: int = Field(default=1048576, ge=1, le=10485760, description="Max bytes to read.")

class FsWriteFileInput(BaseModel):
    path: str = Field(..., description="Path relative to RUNESCRIPT_PATH.")
    content: str = Field(..., description="File content to write.")
    create_dirs: bool = Field(default=False, description="Create parent directories if missing.")

class FsListDirectoryInput(BaseModel):
    path: str = Field(default=".", description="Directory path to list.")
    recursive: bool = Field(default=False, description="List recursively.")

class FsApplyDiffInput(BaseModel):
    path: str = Field(..., description="Path relative to RUNESCRIPT_PATH.")
    diff: str = Field(..., description="Git merge diff block with SEARCH and REPLACE.")

class FsFileExistsInput(BaseModel):
    path: str = Field(..., description="Path relative to RUNESCRIPT_PATH.")

def resolve_and_validate_path(path: str, runescript_path: str) -> str:
    """
    Resolves path against RUNESCRIPT_PATH and enforces strict path traversal guards.
    """
    base = os.path.realpath(runescript_path)
    if not os.path.isabs(path):
        target = os.path.realpath(os.path.join(base, path))
    else:
        target = os.path.realpath(path)

    try:
        common = os.path.commonpath([base, target])
    except ValueError:
        raise PermissionError(f"Path Traversal Guard: '{path}' resolves on a different drive than RUNESCRIPT_PATH '{base}'.")

    if common != base:
        raise PermissionError(f"Path Traversal Guard: '{path}' resolves outside RUNESCRIPT_PATH '{base}'.")

    # Symlink check
    check_link = target if os.path.islink(target) else os.path.join(base, path)
    if os.path.islink(check_link):
        link_target = os.path.realpath(os.readlink(check_link))
        try:
            link_common = os.path.commonpath([base, link_target])
        except ValueError:
            raise PermissionError(f"Symlink Guard: Link points outside RUNESCRIPT_PATH '{base}'.")
        if link_common != base:
            raise PermissionError(f"Symlink Guard: Link points outside RUNESCRIPT_PATH '{base}'.")

    return target

def create_pre_write_backup(target_path: str, runescript_path: str) -> Optional[str]:
    """Creates an automatic pre-write backup under .nia/backups/."""
    if not os.path.exists(target_path):
        return None
    backup_dir = os.path.join(runescript_path, ".nia", "backups")
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    file_hash = hashlib.md5(target_path.encode()).hexdigest()[:8]
    filename = os.path.basename(target_path)
    backup_path = os.path.join(backup_dir, f"{timestamp}_{file_hash}_{filename}.bak")

    shutil.copy2(target_path, backup_path)
    return backup_path

async def fs_read_file(runescript_path: str, path: str, max_bytes: int = 1048576) -> Dict[str, Any]:
    target = resolve_and_validate_path(path, runescript_path)
    if not os.path.isfile(target):
        raise FileNotFoundError(f"File not found: '{path}'")

    with open(target, "r", encoding="utf-8", errors="replace") as f:
        data = f.read(max_bytes + 1)

    truncated = len(data) > max_bytes
    return {
        "path": path,
        "content": data[:max_bytes],
        "bytes_read": min(len(data), max_bytes),
        "truncated": truncated
    }

async def fs_write_file(runescript_path: str, path: str, content: str, create_dirs: bool = False) -> Dict[str, Any]:
    content_bytes = content.encode("utf-8")
    if len(content_bytes) > MAX_WRITE_BYTES:
        raise ValueError(f"Content exceeds maximum write size of 5MB ({len(content_bytes)} bytes).")

    target = resolve_and_validate_path(path, runescript_path)
    backup_path = create_pre_write_backup(target, runescript_path)

    if create_dirs:
        os.makedirs(os.path.dirname(target), exist_ok=True)
    elif not os.path.exists(os.path.dirname(target)):
        raise FileNotFoundError(f"Parent directory does not exist for path '{path}'. Set create_dirs=True.")

    with open(target, "w", encoding="utf-8") as f:
        f.write(content)

    return {
        "path": path,
        "bytes_written": len(content_bytes),
        "backup_created": backup_path
    }

async def fs_list_directory(runescript_path: str, path: str = ".", recursive: bool = False) -> Dict[str, Any]:
    target = resolve_and_validate_path(path, runescript_path)
    if not os.path.isdir(target):
        raise NotADirectoryError(f"Not a directory: '{path}'")

    entries = []
    if recursive:
        for root, dirs, files in os.walk(target):
            for f in files:
                full_p = os.path.join(root, f)
                rel_p = os.path.relpath(full_p, target)
                entries.append({"name": rel_p, "type": "file"})
    else:
        for item in os.listdir(target):
            is_dir = os.path.isdir(os.path.join(target, item))
            entries.append({"name": item, "type": "directory" if is_dir else "file"})

    return {
        "path": path,
        "entries": entries
    }

async def fs_apply_diff(runescript_path: str, path: str, diff: str) -> Dict[str, Any]:
    target = resolve_and_validate_path(path, runescript_path)
    if not os.path.isfile(target):
        raise FileNotFoundError(f"File not found to apply diff: '{path}'")

    with open(target, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse Git Merge Diff format
    search_marker = "<<<<<<< SEARCH\n"
    divider_marker = "=======\n"
    replace_marker = ">>>>>>> REPLACE\n"

    blocks_applied = 0
    new_content = content

    pos = 0
    while True:
        s_idx = diff.find(search_marker, pos)
        if s_idx == -1:
            break
        d_idx = diff.find(divider_marker, s_idx)
        r_idx = diff.find(replace_marker, d_idx)
        if d_idx == -1 or r_idx == -1:
            raise ValueError("Malformed diff format. Missing ======= or >>>>>>> REPLACE markers.")

        search_block = diff[s_idx + len(search_marker):d_idx]
        replace_block = diff[d_idx + len(divider_marker):r_idx]

        if search_block not in new_content:
            raise ValueError(f"SEARCH block not found in original file: {repr(search_block[:50])}")

        new_content = new_content.replace(search_block, replace_block, 1)
        blocks_applied += 1
        pos = r_idx + len(replace_marker)

    if blocks_applied == 0:
        raise ValueError("No valid SEARCH/REPLACE diff blocks found in input.")

    backup_path = create_pre_write_backup(target, runescript_path)
    with open(target, "w", encoding="utf-8") as f:
        f.write(new_content)

    return {
        "path": path,
        "applied_blocks": blocks_applied,
        "backup_created": backup_path
    }

async def fs_file_exists(runescript_path: str, path: str) -> Dict[str, Any]:
    try:
        target = resolve_and_validate_path(path, runescript_path)
        exists = os.path.exists(target)
        is_file = os.path.isfile(target)
        is_dir = os.path.isdir(target)
    except Exception:
        exists = False
        is_file = False
        is_dir = False

    return {
        "path": path,
        "exists": exists,
        "is_file": is_file,
        "is_directory": is_dir
    }
