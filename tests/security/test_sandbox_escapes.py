import pytest
import os
from src.security.sandbox import SecureSandbox

def test_sandbox_timeout():
    sandbox = SecureSandbox(timeout=1)
    code = "import time\nwhile True: time.sleep(0.1)"
    result = sandbox.execute(code, allowed_imports=['time'])
    assert not result['success']
    assert "timed out" in result['error'].lower()

def test_sandbox_memory_limit():
    sandbox = SecureSandbox(memory_limit_mb=10) # Small limit
    # Try to allocate 100MB
    code = "x = ' ' * (100 * 1024 * 1024)"
    result = sandbox.execute(code)
    # This should fail due to RLIMIT_AS
    assert not result['success']

def test_sandbox_import_restriction():
    sandbox = SecureSandbox()
    code = "import os\nos.system('ls')"
    # 'os' is NOT in the default allowed_imports in our integration
    # (actually it was in my sandbox.py default, but let's override)
    result = sandbox.execute(code, allowed_imports=['json'])
    assert not result['success']
    assert "ImportError" in result['error']

def test_sandbox_file_write_restriction():
    sandbox = SecureSandbox()
    code = "with open('secret.txt', 'w') as f: f.write('pwned')"
    # 'open' is replaced with SafeOpen which blocks writing
    result = sandbox.execute(code)
    assert not result['success']
    assert "PermissionError" in result['error'] or "Sandbox blocked" in result['error']
    # Because we set safe_builtins['open'] = None

def test_sandbox_stdout_capture():
    sandbox = SecureSandbox()
    code = "print('Hello Sandbox')"
    result = sandbox.execute(code)
    assert result['success']
    assert "Hello Sandbox" in result['stdout']
