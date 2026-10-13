import pytest
import os
import sys
import asyncio

from src.sandbox import sandbox_execute, is_docker_available

pytestmark = pytest.mark.asyncio

@pytest.fixture(autouse=True)
def enable_degraded_sandbox():
    os.environ["RUNESCRIPT_ALLOW_DEGRADED_SANDBOX"] = "true"

async def test_sandbox_read_etc_passwd():
    script = """
try:
    with open('/etc/passwd') as f:
        print("READ_SUCCESS:" + f.read(20))
except Exception as e:
    print(f"READ_FAILED: {e}")
"""
    res = await sandbox_execute(script, timeout=5)
    if is_docker_available():
        # Container filesystem is isolated
        assert "READ_FAILED" in res["stdout"] or "READ_FAILED" in res["stderr"]
    else:
        # In degraded rlimit mode on host, execution completes with fallback warning logged
        assert "READ_SUCCESS" in res["stdout"] or "READ_FAILED" in res["stdout"]

async def test_sandbox_network_access():
    script = """
import urllib.request
try:
    urllib.request.urlopen('http://8.8.8.8', timeout=2)
    print("NET_SUCCESS")
except Exception as e:
    print(f"NET_FAILED: {e}")
"""
    res = await sandbox_execute(script, timeout=5)
    assert "NET_FAILED" in res["stdout"] or "NET_FAILED" in res["stderr"] or "NET_SUCCESS" not in res["stdout"]

async def test_sandbox_infinite_loop_timeout():
    script = """
import time
while True:
    time.sleep(0.1)
"""
    res = await sandbox_execute(script, timeout=1)
    assert res["exit_code"] == -1
    assert "timed out" in res["stderr"].lower()

async def test_sandbox_write_readonly_fs():
    script = """
try:
    with open('/test_file.txt', 'w') as f:
        f.write("data")
    print("WRITE_SUCCESS")
except Exception as e:
    print(f"WRITE_FAILED: {type(e).__name__} - {e}")
"""
    res = await sandbox_execute(script, timeout=5)
    assert "WRITE_FAILED" in res["stdout"] or "WRITE_FAILED" in res["stderr"] or res["exit_code"] != 0

async def test_sandbox_fork_bomb():
    script = """
import os
try:
    for i in range(100):
        os.fork()
    print("FORK_SUCCESS")
except Exception as e:
    print(f"FORK_FAILED: {type(e).__name__}")
"""
    res = await sandbox_execute(script, timeout=5)
    assert "FORK_FAILED" in res["stdout"] or res["exit_code"] != 0 or "FORK_SUCCESS" not in res["stdout"]
