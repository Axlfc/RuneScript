import sys
from unittest.mock import patch
import pytest

def test_sandbox_without_resource():
    # Force resource to be None in sys.modules to simulate Windows
    with patch.dict(sys.modules, {'resource': None}):
        # We need to reload the module to pick up the mocked None
        import src.security.sandbox
        from importlib import reload
        reload(src.security.sandbox)

        from src.security.sandbox import SecureSandbox

        sandbox = SecureSandbox(timeout=5)
        result = sandbox.execute("print('No resource, no problem')")

        assert result['success']
        assert "No resource, no problem" in result['stdout']

    # Cleanup: reload sandbox again to restore original state for other tests
    reload(src.security.sandbox)

def test_sandbox_initialization_no_resource():
    """Verify that SecureSandbox can be initialized even if resource is None."""
    with patch('src.security.sandbox.resource', None):
        from src.security.sandbox import SecureSandbox
        sandbox = SecureSandbox()
        assert sandbox is not None
