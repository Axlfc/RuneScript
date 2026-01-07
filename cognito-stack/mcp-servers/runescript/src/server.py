import asyncio
import json
import logging
import traceback
from datetime import datetime, UTC  # Updated import
from typing import Any, Dict

from mcp.server import Server
from mcp.server.stdio import stdio_server
from pydantic import ValidationError

from .schemas.tool_schemas import ExecuteScriptInput, GenerateScriptInput
from .tools import (execute_script, generate_script, list_templates,
                    validate_syntax)
from .wrapper import RuneScriptWrapper

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(message)s', handlers=[
    logging.FileHandler("runescript_mcp.log"),
    logging.StreamHandler()
])
logger = logging.getLogger(__name__)

def log_operation(tool_name: str, arguments: dict, success: bool, duration: float, error_info: str = None):
    """Logs a tool operation in a structured JSON format."""
    log_data = {
        "timestamp": datetime.now(UTC).isoformat(),  # Updated to timezone-aware UTC
        "tool": tool_name,
        "arguments": arguments,
        "success": success,
        "duration_ms": round(duration * 1000, 2),
        "error": error_info
    }
    logger.info(json.dumps(log_data))

# --- Server Initialization ---
server = Server(
    "runescript-mcp-server",
    "1.0.0",
    "A server to interact with the RuneScript application."
)

try:
    runescript_wrapper = RuneScriptWrapper()
except RuntimeError as e:
    logger.critical(json.dumps({
        "timestamp": datetime.now(UTC).isoformat(), # Updated
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
}

# --- Tool Definitions ---
@server.list_tools()
async def list_runescript_tools() -> Dict[str, Any]:
    """Provides the definitions of all available tools."""
    return {
        "tools": [
            {
                "name": "generate_script",
                "description": "Generates a script in a specified language based on a natural language description.",
                "inputSchema": GenerateScriptInput.model_json_schema(),
            },
            {
                "name": "execute_script",
                "description": "Executes a script in a sandboxed environment with a configurable timeout.",
                "inputSchema": ExecuteScriptInput.model_json_schema(),
            },
            {
                "name": "validate_syntax",
                "description": "Checks a script for syntax errors without executing it. (Stubbed)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "script": {"type": "string", "description": "The script to validate."},
                        "language": {"type": "string", "enum": ["python", "javascript"]},
                    },
                    "required": ["script", "language"],
                },
            },
            {
                "name": "list_templates",
                "description": "Lists available code templates for script generation. (Stubbed)",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]
    }

# --- Tool Invocation ---
@server.call_tool()
async def call_runescript_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handles incoming requests to call a specific tool."""
    start_time = asyncio.get_event_loop().time()

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
        "timestamp": datetime.now(UTC).isoformat(), # Updated
        "level": "INFO",
        "message": "RuneScript MCP Server is starting up."
    }))
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)
    logger.info(json.dumps({
        "timestamp": datetime.now(UTC).isoformat(), # Updated
        "level": "INFO",
        "message": "RuneScript MCP Server has shut down."
    }))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info(json.dumps({
            "timestamp": datetime.now(UTC).isoformat(), # Updated
            "level": "INFO",
            "message": "Server shutdown requested by user."
        }))
    except Exception as e:
        logger.critical(json.dumps({
            "timestamp": datetime.now(UTC).isoformat(), # Updated
            "level": "CRITICAL",
            "message": f"A critical error forced the server to stop: {e}",
            "error_details": traceback.format_exc()
        }))
