import asyncio
import logging
import os
import resource
import shutil
import subprocess
import sys
import uuid
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Concurrency semaphore
MAX_CONCURRENT = int(os.environ.get("RUNESCRIPT_SANDBOX_MAX_CONCURRENT", "4"))
_sandbox_semaphore = asyncio.Semaphore(MAX_CONCURRENT)
_degraded_warning_logged = False
_docker_availability_cached: Optional[bool] = None

def is_docker_available() -> bool:
    """Checks if Docker daemon can actually run containers in this environment."""
    global _docker_availability_cached
    if _docker_availability_cached is not None:
        return _docker_availability_cached

    try:
        res = subprocess.run(
            ["docker", "run", "--rm", "python:3.11-slim", "python3", "-c", "import sys"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3
        )
        _docker_availability_cached = (res.returncode == 0)
    except Exception:
        _docker_availability_cached = False

    return _docker_availability_cached

async def sandbox_execute(
    script: str,
    language: str = "python",
    timeout: int = 10,
    profile: str = "untrusted",
    env: Optional[Dict[str, str]] = None,
    repo_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes a script inside an isolated sandbox (Docker ephemeral container or rlimit fallback).

    Profiles:
    - 'untrusted': No mounts, --tmpfs /tmp:rw,noexec,nosuid,size=64m, --network=none, --memory=256m
    - 'trusted-tests': Mounts repo_path as :ro, -w /repo, --tmpfs /tmp:rw,exec,nosuid,size=256m, --network=none, --memory=512m
    """
    global _degraded_warning_logged
    env = env or {}

    async with _sandbox_semaphore:
        if is_docker_available():
            return await _execute_in_docker(script, language, timeout, profile, env, repo_path)

        # Check if degraded sandbox is allowed
        allow_degraded = os.environ.get("RUNESCRIPT_ALLOW_DEGRADED_SANDBOX", "").lower() in ("true", "1", "yes")
        if not allow_degraded:
            return {
                "stdout": "",
                "stderr": "E_DOCKER_INFRASTRUCTURE_ERROR: Docker daemon is unavailable and RUNESCRIPT_ALLOW_DEGRADED_SANDBOX is not set.",
                "exit_code": -1
            }

        if not _degraded_warning_logged:
            logger.warning("Docker is unavailable or overlayfs unusable. Executing in degraded process rlimit sandbox mode.")
            _degraded_warning_logged = True

        return await _execute_in_rlimit(script, language, timeout, profile, env)

async def _execute_in_docker(
    script: str,
    language: str,
    timeout: int,
    profile: str,
    env: Dict[str, str],
    repo_path: Optional[str]
) -> Dict[str, Any]:
    container_id = f"runescript-sandbox-{uuid.uuid4()}"

    cmd = [
        "docker", "run", "-i", "--rm",
        "--name", container_id,
        "--label", "runescript-sandbox=true",
        "--network=none",
        "--read-only",
        "--cap-drop=ALL",
        "--user=10001:10001",
        "--security-opt=no-new-privileges"
    ]

    if profile == "untrusted":
        cmd.extend([
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
            "--memory=256m",
            "--cpus=1",
            "--pids-limit=64"
        ])
    elif profile == "trusted-tests":
        cmd.extend([
            "--tmpfs", "/tmp:rw,exec,nosuid,size=256m",
            "--memory=512m",
            "--cpus=2",
            "--pids-limit=128"
        ])
        if repo_path and os.path.exists(repo_path):
            cmd.extend(["-v", f"{os.path.abspath(repo_path)}:/repo:ro", "-w", "/repo"])
        cmd.extend(["-e", "PYTHONDONTWRITEBYTECODE=1"])

    for k, v in env.items():
        cmd.extend(["-e", f"{k}={v}"])

    image_name = "runescript-sandbox:3.11-slim" if profile == "trusted-tests" else "python:3.11-slim"

    if language.lower() == "python":
        cmd.extend([image_name, "python3", "-"])
    elif language.lower() in ("bash", "sh"):
        cmd.extend([image_name, "sh", "-s"])
    else:
        return {
            "stdout": "",
            "stderr": f"Language '{language}' is not supported in Docker sandbox.",
            "exit_code": 1
        }

    proc = None
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=script.encode("utf-8")),
            timeout=timeout
        )
        return {
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "exit_code": proc.returncode
        }
    except asyncio.TimeoutError:
        # Kill container forcefully
        subprocess.run(["docker", "kill", container_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if proc:
            try:
                proc.kill()
            except Exception:
                pass
        return {
            "stdout": "",
            "stderr": f"Execution timed out after {timeout} seconds",
            "exit_code": -1
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": f"Docker execution error: {e}",
            "exit_code": -1
        }

async def _execute_in_rlimit(
    script: str,
    language: str,
    timeout: int,
    profile: str,
    env: Dict[str, str]
) -> Dict[str, Any]:
    """Fallback process execution using resource.setrlimit on POSIX systems."""
    if language.lower() != "python":
        return {
            "stdout": "",
            "stderr": f"Language '{language}' not supported in rlimit fallback.",
            "exit_code": 1
        }

    def _set_rlimits():
        try:
            # RLIMIT_CPU: CPU time limit
            resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout + 2))
            # RLIMIT_AS: Memory limit (256MB)
            resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
            # RLIMIT_NPROC: Process limit (64)
            if hasattr(resource, 'RLIMIT_NPROC'):
                resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
        except Exception:
            pass

    cmd = [sys.executable, "-c", script]
    run_env = dict(os.environ)
    run_env.update(env)

    proc = None
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=_set_rlimits,
            env=run_env
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout
        )
        return {
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "exit_code": proc.returncode
        }
    except asyncio.TimeoutError:
        if proc:
            try:
                proc.kill()
            except Exception:
                pass
        return {
            "stdout": "",
            "stderr": f"Execution timed out after {timeout} seconds",
            "exit_code": -1
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1
        }
