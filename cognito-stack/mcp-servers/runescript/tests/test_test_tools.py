import pytest
import os
from src.tools.test_tools import parse_pytest_output, run_tests

def test_parse_pytest_output_passed():
    stdout = "collected 7 items\ntest_server.py ....... [100%]\n============================== 7 passed in 1.24s =============================="
    parsed = parse_pytest_output(stdout, "", 0)
    assert parsed["passed"] == 7
    assert parsed["failed"] == 0
    assert parsed["duration_seconds"] == 1.24
    assert parsed["exit_code"] == 0

def test_parse_pytest_output_failed():
    stdout = "collected 10 items\nFAILED test_foo.py\n======================== 2 failed, 8 passed in 3.50s ========================"
    parsed = parse_pytest_output(stdout, "", 1)
    assert parsed["passed"] == 8
    assert parsed["failed"] == 2
    assert parsed["duration_seconds"] == 3.50
    assert parsed["exit_code"] == 1

@pytest.mark.asyncio
async def test_run_tests_mcp_self():
    os.environ["RUNESCRIPT_ALLOW_DEGRADED_SANDBOX"] = "true"
    repo_path = os.environ.get("RUNESCRIPT_PATH", "/app")
    res = await run_tests(
        runescript_path=repo_path,
        path="cognito-stack/mcp-servers/runescript/tests/test_fs_tools.py",
        framework="pytest",
        timeout=30
    )
    assert res["passed"] >= 1
    assert res["failed"] == 0
