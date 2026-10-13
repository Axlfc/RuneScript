import asyncio
import json
import logging
import os
import sys
import time
import traceback
from collections import defaultdict, deque
from datetime import datetime, UTC
from logging.handlers import RotatingFileHandler
from typing import Any, Dict

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool
from pydantic import ValidationError

from .schemas.tool_schemas import ExecuteScriptInput, GenerateScriptInput
from .tools import (execute_script, generate_script, list_templates,
                    validate_syntax, fs_tools, test_tools, git_tools)
from .wrapper import RuneScriptWrapper

# --- Logging Setup with Rotation ---
log_formatter = logging.Formatter('%(message)s')
file_handler = RotatingFileHandler("runescript_mcp.log", maxBytes=10 * 1024 * 1024, backupCount=5)
file_handler.setFormatter(log_formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(logging.StreamHandler())

def log_operation(tool_name: str, arguments: dict, success: bool, duration: float, error_info: str = None):
    """Logs a tool operation in a structured JSON format."""
    log_data = {
        "timestamp": datetime.now(UTC).isoformat(),
        "tool": tool_name,
        "arguments": arguments,
        "success": success,
        "duration_ms": round(duration * 1000, 2),
        "error": error_info
    }
    logger.info(json.dumps(log_data))

# --- Rate Limiter ---
RATE_LIMIT_PER_MINUTE = int(os.environ.get("RUNESCRIPT_MCP_RATE_LIMIT", "60"))
_tool_call_history = defaultdict(deque)

def is_rate_limited(tool_name: str) -> bool:
    """Sliding window rate limiter (max RATE_LIMIT_PER_MINUTE per tool per 60s)."""
    now = time.time()
    history = _tool_call_history[tool_name]
    while history and history[0] < now - 60:
        history.popleft()
    if len(history) >= RATE_LIMIT_PER_MINUTE:
        return True
    history.append(now)
    return False

# --- Server Initialization ---
server = Server("runescript-mcp-server")

try:
    runescript_wrapper = RuneScriptWrapper()
except RuntimeError as e:
    logger.critical(json.dumps({
        "timestamp": datetime.now(UTC).isoformat(),
        "level": "CRITICAL",
        "message": "Failed to initialize RuneScriptWrapper. Server cannot start.",
        "error": str(e)
    }))
    exit(1)

TOOL_HANDLERS = {
    "generate_script": generate_script.generate_script,
    "execute_script": execute_script.execute_script,
    "validate_syntax": validate_syntax.validate_syntax,
    "list_templates": list_templates.list_templates,
    "fs_read_file": lambda w, **kwargs: w.fs_read_file(**kwargs),
    "fs_write_file": lambda w, **kwargs: w.fs_write_file(**kwargs),
    "fs_list_directory": lambda w, **kwargs: w.fs_list_directory(**kwargs),
    "fs_apply_diff": lambda w, **kwargs: w.fs_apply_diff(**kwargs),
    "fs_file_exists": lambda w, **kwargs: w.fs_file_exists(**kwargs),
    "run_tests": lambda w, **kwargs: w.run_tests(**kwargs),
    "git_status": lambda w, **kwargs: w.git_status(**kwargs),
    "git_diff": lambda w, **kwargs: w.git_diff(**kwargs),
    "git_branch_create": lambda w, **kwargs: w.git_branch_create(**kwargs),
    "git_checkout": lambda w, **kwargs: w.git_checkout(**kwargs),
    "git_add": lambda w, **kwargs: w.git_add(**kwargs),
    "git_commit": lambda w, **kwargs: w.git_commit(**kwargs),
    "git_push": lambda w, **kwargs: w.git_push(**kwargs),
    "git_open_pr": lambda w, **kwargs: w.git_open_pr(**kwargs),
}

# --- Tool Definitions ---
@server.list_tools()
async def list_runescript_tools() -> list[Tool]:
    """Provides the definitions of all available tools."""
    return [
        Tool(
            name="generate_script",
            description="Generates a script in a specified language based on a natural language description.",
            inputSchema=GenerateScriptInput.model_json_schema(),
        ),
        Tool(
            name="execute_script",
            description="Executes a script in a sandboxed environment with a configurable timeout.",
            inputSchema=ExecuteScriptInput.model_json_schema(),
        ),
        Tool(
            name="validate_syntax",
            description="Checks a script for syntax errors without executing it. (Stubbed)",
            inputSchema={
                "type": "object",
                "properties": {
                    "script": {"type": "string", "description": "The script to validate."},
                    "language": {"type": "string", "enum": ["python", "javascript"]},
                },
                "required": ["script", "language"],
            },
        ),
        Tool(
            name="list_templates",
            description="Lists available code templates for script generation. (Stubbed)",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="fs_read_file",
            description="Reads the contents of a file within the repository up to max_bytes.",
            inputSchema=fs_tools.FsReadFileInput.model_json_schema(),
        ),
        Tool(
            name="fs_write_file",
            description="Writes or overwrites a file within the repository, creating backups automatically.",
            inputSchema=fs_tools.FsWriteFileInput.model_json_schema(),
        ),
        Tool(
            name="fs_list_directory",
            description="Lists files and subdirectories within a path inside the repository.",
            inputSchema=fs_tools.FsListDirectoryInput.model_json_schema(),
        ),
        Tool(
            name="fs_apply_diff",
            description="Applies a Git Merge Diff block (SEARCH/REPLACE) to modify an existing file.",
            inputSchema=fs_tools.FsApplyDiffInput.model_json_schema(),
        ),
        Tool(
            name="fs_file_exists",
            description="Verifies if a file or directory exists within the repository.",
            inputSchema=fs_tools.FsFileExistsInput.model_json_schema(),
        ),
        Tool(
            name="run_tests",
            description="Runs pytest test suite inside trusted-tests sandbox and returns parsed summary.",
            inputSchema=test_tools.RunTestsInput.model_json_schema(),
        ),
        Tool(
            name="git_status",
            description="Gets the current working tree git status.",
            inputSchema=git_tools.GitStatusInput.model_json_schema(),
        ),
        Tool(
            name="git_diff",
            description="Shows git diff for working directory or staged changes.",
            inputSchema=git_tools.GitDiffInput.model_json_schema(),
        ),
        Tool(
            name="git_branch_create",
            description="Creates a new feature branch (must start with jules/ or agent/).",
            inputSchema=git_tools.GitBranchCreateInput.model_json_schema(),
        ),
        Tool(
            name="git_checkout",
            description="Switches git branches.",
            inputSchema=git_tools.GitCheckoutInput.model_json_schema(),
        ),
        Tool(
            name="git_add",
            description="Stages files in git.",
            inputSchema=git_tools.GitAddInput.model_json_schema(),
        ),
        Tool(
            name="git_commit",
            description="Commits staged changes (blocked on protected branches).",
            inputSchema=git_tools.GitCommitInput.model_json_schema(),
        ),
        Tool(
            name="git_push",
            description="Pushes branch to remote (requires human confirmation).",
            inputSchema=git_tools.GitPushInput.model_json_schema(),
        ),
        Tool(
            name="git_open_pr",
            description="Opens a Pull Request on GitHub via API (requires human confirmation).",
            inputSchema=git_tools.GitOpenPrInput.model_json_schema(),
        ),
    ]

# --- Tool Invocation ---
@server.call_tool()
async def call_runescript_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handles incoming requests to call a specific tool."""
    start_time = asyncio.get_event_loop().time()

    if is_rate_limited(name):
        duration = asyncio.get_event_loop().time() - start_time
        err_msg = f"Rate limit exceeded for tool '{name}'. Maximum {RATE_LIMIT_PER_MINUTE} requests per minute allowed."
        log_operation(name, arguments, success=False, duration=duration, error_info=err_msg)
        return {"content": [{"type": "text", "text": f"Error: {err_msg}"}]}

    handler = TOOL_HANDLERS.get(name)
    if not handler:
        return {"content": [{"type": "text", "text": f"Error: Unknown tool '{name}'"}]}

    try:
        if not arguments:
             result = await handler(runescript_wrapper)
        else:
             result = await handler(runescript_wrapper, **arguments)

        duration = asyncio.get_event_loop().time() - start_time
        log_operation(name, arguments, success=True, duration=duration)

        if not isinstance(result, (dict, list, str, int, float, bool, type(None))):
             result = str(result)

        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

    except ValidationError as e:
        duration = asyncio.get_event_loop().time() - start_time
        error_info = f"Input validation failed: {e}"
        log_operation(name, arguments, success=False, duration=duration, error_info=error_info)
        return {"content": [{"type": "text", "text": error_info}]}

    except Exception as e:
        duration = asyncio.get_event_loop().time() - start_time
        error_info = f"An unexpected error occurred: {traceback.format_exc()}"
        log_operation(name, arguments, success=False, duration=duration, error_info=str(e))
        return {"content": [{"type": "text", "text": f"An unexpected error occurred: {e}"}]}


# --- Main Execution ---
async def main():
    """Starts the MCP server and connects it to stdio."""
    logger.info(json.dumps({
        "timestamp": datetime.now(UTC).isoformat(),
        "level": "INFO",
        "message": "RuneScript MCP Server is starting up."
    }))
    async with stdio_server() as (read_stream, write_stream):
        options = server.create_initialization_options()
        await server.run(read_stream, write_stream, options)
    logger.info(json.dumps({
        "timestamp": datetime.now(UTC).isoformat(),
        "level": "INFO",
        "message": "RuneScript MCP Server has shut down."
    }))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info(json.dumps({
            "timestamp": datetime.now(UTC).isoformat(),
            "level": "INFO",
            "message": "Server shutdown requested by user."
        }))
    except Exception as e:
        logger.critical(json.dumps({
            "timestamp": datetime.now(UTC).isoformat(),
            "level": "CRITICAL",
            "message": f"A critical error forced the server to stop: {e}",
            "error_details": traceback.format_exc()
        }))
