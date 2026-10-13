import asyncio
import os
import subprocess
import urllib.request
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

PROTECTED_BRANCHES = {"redgreenrefactor", "main", "ancient", "master"}

class GitStatusInput(BaseModel):
    pass

class GitDiffInput(BaseModel):
    path: Optional[str] = Field(default=None, description="Optional path to filter diff.")
    staged: bool = Field(default=False, description="Show staged diff.")

class GitBranchCreateInput(BaseModel):
    name: str = Field(..., description="Branch name. MUST start with jules/ or agent/.")
    base: str = Field(default="redgreenrefactor", description="Base branch.")

class GitCheckoutInput(BaseModel):
    branch: str = Field(..., description="Branch to checkout.")

class GitAddInput(BaseModel):
    paths: List[str] = Field(..., description="List of file paths to stage.")

class GitCommitInput(BaseModel):
    message: str = Field(..., min_length=5, max_length=200, description="Commit message.")

class GitPushInput(BaseModel):
    branch: str = Field(..., description="Branch to push.")
    remote: str = Field(default="origin", description="Remote name.")
    confirm: bool = Field(default=False, description="Confirmation flag. Must be True or CONFIRM_PUSH=yes env var.")

class GitOpenPrInput(BaseModel):
    title: str = Field(..., description="PR title.")
    body: str = Field(..., description="PR description.")
    head: str = Field(..., description="Head branch.")
    base: str = Field(default="redgreenrefactor", description="Base branch.")
    confirm: bool = Field(default=False, description="Confirmation flag. Must be True or CONFIRM_PR=yes env var.")

def _run_git_cmd(repo_path: str, args: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + args,
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

async def git_status(runescript_path: str) -> Dict[str, Any]:
    proc = _run_git_cmd(runescript_path, ["status", "--porcelain", "-b"])
    if proc.returncode != 0:
        raise RuntimeError(f"Git status failed: {proc.stderr}")

    lines = proc.stdout.splitlines()
    branch = "unknown"
    staged = []
    unstaged = []
    untracked = []

    if lines and lines[0].startswith("##"):
        branch_line = lines[0][3:]
        branch = branch_line.split("...")[0].split(" ")[0]

    for line in lines[1:]:
        if not line:
            continue
        st, filepath = line[:2], line[3:]
        if st[0] in ("M", "A", "D", "R", "C"):
            staged.append(filepath)
        if st[1] in ("M", "D"):
            unstaged.append(filepath)
        if st == "??":
            untracked.append(filepath)

    return {
        "branch": branch,
        "clean": len(staged) == 0 and len(unstaged) == 0 and len(untracked) == 0,
        "staged": staged,
        "unstaged": unstaged,
        "untracked": untracked
    }

async def git_diff(runescript_path: str, path: Optional[str] = None, staged: bool = False) -> Dict[str, Any]:
    args = ["diff"]
    if staged:
        args.append("--staged")
    if path:
        args.extend(["--", path])

    proc = _run_git_cmd(runescript_path, args)
    return {
        "path": path,
        "staged": staged,
        "diff": proc.stdout
    }

async def git_branch_create(runescript_path: str, name: str, base: str = "redgreenrefactor") -> Dict[str, Any]:
    if not (name.startswith("jules/") or name.startswith("agent/")):
        raise PermissionError(f"Branch Guard: Branch name '{name}' must start with 'jules/' or 'agent/'.")

    proc = _run_git_cmd(runescript_path, ["checkout", "-b", name, base])
    if proc.returncode != 0:
        raise RuntimeError(f"Failed to create branch: {proc.stderr}")

    return {
        "branch": name,
        "base": base,
        "created": True
    }

async def git_checkout(runescript_path: str, branch: str) -> Dict[str, Any]:
    proc = _run_git_cmd(runescript_path, ["checkout", branch])
    if proc.returncode != 0:
        raise RuntimeError(f"Failed to checkout branch '{branch}': {proc.stderr}")

    return {
        "branch": branch,
        "success": True
    }

async def git_add(runescript_path: str, paths: List[str]) -> Dict[str, Any]:
    proc = _run_git_cmd(runescript_path, ["add"] + paths)
    if proc.returncode != 0:
        raise RuntimeError(f"Failed to stage paths: {proc.stderr}")

    return {
        "staged_paths": paths,
        "success": True
    }

async def git_commit(runescript_path: str, message: str) -> Dict[str, Any]:
    status_res = await git_status(runescript_path)
    curr_branch = status_res["branch"]

    if curr_branch in PROTECTED_BRANCHES:
        raise PermissionError(f"Branch Protection Guard: Direct commits to protected branch '{curr_branch}' are forbidden.")

    proc = _run_git_cmd(runescript_path, ["commit", "-m", message])
    if proc.returncode != 0:
        raise RuntimeError(f"Git commit failed: {proc.stderr}")

    return {
        "branch": curr_branch,
        "message": message,
        "success": True,
        "output": proc.stdout
    }

async def git_push(runescript_path: str, branch: str, remote: str = "origin", confirm: bool = False) -> Dict[str, Any]:
    env_confirm = os.environ.get("CONFIRM_PUSH", "").lower() in ("yes", "true", "1")
    if not (confirm or env_confirm):
        raise PermissionError("Human Confirmation Required: Push aborted. Set CONFIRM_PUSH=yes or pass confirm=True.")

    if branch in PROTECTED_BRANCHES:
        raise PermissionError(f"Branch Protection Guard: Pushing directly to protected branch '{branch}' is forbidden.")

    proc = _run_git_cmd(runescript_path, ["push", remote, branch])
    return {
        "branch": branch,
        "remote": remote,
        "success": proc.returncode == 0,
        "output": proc.stdout if proc.returncode == 0 else proc.stderr
    }

async def git_open_pr(runescript_path: str, title: str, body: str, head: str, base: str = "redgreenrefactor", confirm: bool = False) -> Dict[str, Any]:
    env_confirm = os.environ.get("CONFIRM_PR", "").lower() in ("yes", "true", "1")
    if not (confirm or env_confirm):
        raise PermissionError("Human Confirmation Required: Open PR aborted. Set CONFIRM_PR=yes or pass confirm=True.")

    github_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not github_token:
        raise ValueError("Secret Guard: GITHUB_TOKEN environment variable is missing.")

    # Call GitHub API to open PR
    url = "https://api.github.com/repos/Axlfc/RuneScript/pulls"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "RuneScript-MCP-Server"
    }
    payload = json.dumps({
        "title": title,
        "body": body,
        "head": head,
        "base": base
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {
                "pr_number": data.get("number"),
                "html_url": data.get("html_url"),
                "state": data.get("state")
            }
    except Exception as e:
        raise RuntimeError(f"GitHub API call failed: {e}")
