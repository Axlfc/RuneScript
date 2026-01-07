import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
import os
import sys
from pathlib import Path

# --- Pre-Import Setup ---
MOCK_RUNESCRIPT_PATH = '/tmp/mock-runescript'
os.environ['RUNESCRIPT_PATH'] = MOCK_RUNESCRIPT_PATH
Path(MOCK_RUNESCRIPT_PATH).mkdir(parents=True, exist_ok=True)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.modules['src.ai.assistant'] = MagicMock()
sys.modules['src.executor.script_executor'] = MagicMock()
sys.modules['src.editor.syntax_validator'] = MagicMock()

# --- Imports ---
import pytest
from src.server import call_runescript_tool, list_runescript_tools

pytestmark = pytest.mark.asyncio

# --- Fixtures ---
@pytest.fixture
def mock_wrapper():
    """
    Fixture to provide a mocked instance of RuneScriptWrapper.
    This is a more robust way to patch, targeting the exact location
    where the class is used.
    """
    with patch('src.server.runescript_wrapper', autospec=True) as mock:
        mock.generate_script = AsyncMock(return_value="print('hello')")
        mock.execute_script = AsyncMock(return_value={"status": "success", "output": ""})
        mock.validate_syntax = AsyncMock(return_value={"valid": True, "errors": []})
        mock.list_templates = AsyncMock(return_value=[{"name": "test_template"}])
        yield mock

# --- Tests ---
async def test_list_tools():
    """Verify that the list_tools handler returns the correct tool definitions."""
    result = await list_runescript_tools()
    assert "tools" in result
    tool_names = [t["name"] for t in result["tools"]]
    assert "generate_script" in tool_names
    assert "execute_script" in tool_names
    assert "validate_syntax" in tool_names
    assert "list_templates" in tool_names
    assert len(tool_names) == 4

async def test_call_generate_script_success(mock_wrapper):
    """Test a successful call to the 'generate_script' tool."""
    args = {"language": "python", "description": "create a hello world script"}
    result = await call_runescript_tool("generate_script", args)

    mock_wrapper.generate_script.assert_called_once_with(language="python", description="create a hello world script")
    assert "content" in result
    content = json.loads(result["content"][0]["text"])
    assert content == "print('hello')"

async def test_call_execute_script_success(mock_wrapper):
    """Test a successful call to the 'execute_script' tool."""
    args = {"script": "print('test')", "language": "python", "timeout": 10, "args": {}, "environment": {}}
    result = await call_runescript_tool("execute_script", args)

    mock_wrapper.execute_script.assert_called_once_with(script="print('test')", language="python", args={}, timeout=10)
    assert "content" in result
    content = json.loads(result["content"][0]["text"])
    assert content == {"status": "success", "output": ""}

async def test_call_list_templates_success(mock_wrapper):
    """Test a successful call to the 'list_templates' tool."""
    result = await call_runescript_tool("list_templates", {})
    mock_wrapper.list_templates.assert_called_once()
    content = json.loads(result["content"][0]["text"])
    assert content == [{"name": "test_template"}]

async def test_call_tool_unknown_name():
    """Test calling a tool that does not exist."""
    result = await call_runescript_tool("non_existent_tool", {})
    assert "Error: Unknown tool 'non_existent_tool'" in result["content"][0]["text"]

async def test_call_tool_validation_error(mock_wrapper):
    """Test a tool call with invalid arguments that should trigger a Pydantic error."""
    args = {"language": "python", "description": "short"}
    result = await call_runescript_tool("generate_script", args)

    assert not mock_wrapper.generate_script.called
    assert "Input validation failed" in result["content"][0]["text"]

@patch('src.server.TOOL_HANDLERS', {
    "generate_script": MagicMock(side_effect=Exception("Something went wrong"))
})
async def test_call_tool_unexpected_exception():
    """Test how the server handles an unexpected exception from a tool handler."""
    args = {"language": "python", "description": "a valid description"}
    result = await call_runescript_tool("generate_script", args)

    assert "An unexpected error occurred: Something went wrong" in result["content"][0]["text"]
