import asyncio
import os
import sys
import subprocess
import ast
from typing import List, Dict, Any, Optional

from .sandbox import sandbox_execute
from .tools import fs_tools, test_tools, git_tools

# --- RuneScript Integration ---
try:
    RUNESCRIPT_PATH = os.environ["RUNESCRIPT_PATH"]
except KeyError:
    raise RuntimeError(
        "The 'RUNESCRIPT_PATH' environment variable is not set. "
        "Please set it to the absolute path of your RuneScript project clone."
    )

if not os.path.exists(RUNESCRIPT_PATH):
    raise RuntimeError(
        f"RuneScript path '{RUNESCRIPT_PATH}' does not exist. "
        "Please verify the 'RUNESCRIPT_PATH' environment variable."
    )

sys.path.insert(0, RUNESCRIPT_PATH)

try:
    from src.models.ai_assistant import AIAssistant
except ImportError:
    AIAssistant = None


class RuneScriptWrapper:
    """
    A wrapper class to interface with the internal modules of the RuneScript
    desktop application, exposing its functionalities as async methods.
    """

    def __init__(self):
        """Initializes the wrapper and the underlying RuneScript components."""
        try:
            if AIAssistant:
                self.ai_assistant = AIAssistant()
            else:
                self.ai_assistant = None
        except Exception:
            self.ai_assistant = None

    async def generate_script(self, language: str, description: str) -> str:
        prompt = f"Generate a script in {language}. Description: {description}"
        if self.ai_assistant:
            try:
                res = await asyncio.to_thread(self.ai_assistant.generate, prompt)
                if res and not res.startswith("Error:"):
                    return res
            except Exception:
                pass

        if language.lower() == "python":
            return '# Generated script\nprint("Hello World from RuneScript MCP")\n'
        elif language.lower() in ["javascript", "js"]:
            return '// Generated script\nconsole.log("Hello World from RuneScript MCP");\n'
        else:
            return f"// Generated script in {language}\n"

    async def execute_script(
        self, script: str, language: str, args: Dict[str, Any] = None, timeout: int = 10, environment: Dict[str, str] = None
    ) -> Dict[str, Any]:
        return await sandbox_execute(
            script=script,
            language=language,
            timeout=timeout,
            profile="untrusted",
            env=environment or {},
            repo_path=RUNESCRIPT_PATH
        )

    async def sandbox_execute(
        self, script: str, language: str = "python", timeout: int = 10, profile: str = "untrusted", env: Dict[str, str] = None
    ) -> Dict[str, Any]:
        return await sandbox_execute(
            script=script,
            language=language,
            timeout=timeout,
            profile=profile,
            env=env or {},
            repo_path=RUNESCRIPT_PATH
        )

    async def fs_read_file(self, path: str, max_bytes: int = 1048576) -> Dict[str, Any]:
        return await fs_tools.fs_read_file(RUNESCRIPT_PATH, path, max_bytes)

    async def fs_write_file(self, path: str, content: str, create_dirs: bool = False) -> Dict[str, Any]:
        return await fs_tools.fs_write_file(RUNESCRIPT_PATH, path, content, create_dirs)

    async def fs_list_directory(self, path: str = ".", recursive: bool = False) -> Dict[str, Any]:
        return await fs_tools.fs_list_directory(RUNESCRIPT_PATH, path, recursive)

    async def fs_apply_diff(self, path: str, diff: str) -> Dict[str, Any]:
        return await fs_tools.fs_apply_diff(RUNESCRIPT_PATH, path, diff)

    async def fs_file_exists(self, path: str) -> Dict[str, Any]:
        return await fs_tools.fs_file_exists(RUNESCRIPT_PATH, path)

    async def run_tests(self, path: str = None, framework: str = "pytest", timeout: int = 300) -> Dict[str, Any]:
        return await test_tools.run_tests(RUNESCRIPT_PATH, path, framework, timeout)

    async def git_status(self) -> Dict[str, Any]:
        return await git_tools.git_status(RUNESCRIPT_PATH)

    async def git_diff(self, path: Optional[str] = None, staged: bool = False) -> Dict[str, Any]:
        return await git_tools.git_diff(RUNESCRIPT_PATH, path, staged)

    async def git_branch_create(self, name: str, base: str = "redgreenrefactor") -> Dict[str, Any]:
        return await git_tools.git_branch_create(RUNESCRIPT_PATH, name, base)

    async def git_checkout(self, branch: str) -> Dict[str, Any]:
        return await git_tools.git_checkout(RUNESCRIPT_PATH, branch)

    async def git_add(self, paths: List[str]) -> Dict[str, Any]:
        return await git_tools.git_add(RUNESCRIPT_PATH, paths)

    async def git_commit(self, message: str) -> Dict[str, Any]:
        return await git_tools.git_commit(RUNESCRIPT_PATH, message)

    async def git_push(self, branch: str, remote: str = "origin", confirm: bool = False) -> Dict[str, Any]:
        return await git_tools.git_push(RUNESCRIPT_PATH, branch, remote, confirm)

    async def git_open_pr(self, title: str, body: str, head: str, base: str = "redgreenrefactor", confirm: bool = False) -> Dict[str, Any]:
        return await git_tools.git_open_pr(RUNESCRIPT_PATH, title, body, head, base, confirm)

    async def validate_syntax(self, script: str, language: str) -> Dict[str, Any]:
        if language.lower() == "python":
            try:
                ast.parse(script)
                return {"valid": True, "errors": [], "warnings": []}
            except SyntaxError as e:
                return {
                    "valid": False,
                    "errors": [f"SyntaxError at line {e.lineno}, col {e.offset}: {e.msg}"],
                    "warnings": [],
                }
        await asyncio.sleep(0.01)
        return {
            "valid": True,
            "errors": [],
            "warnings": ["Validation logic is not fully implemented for non-python languages."],
        }

    async def list_templates(self) -> List[Dict[str, str]]:
        await asyncio.sleep(0.01)
        return [
            {"name": "python_fastapi_server", "language": "python", "description": "A simple FastAPI server."},
            {"name": "python_web_scraper", "language": "python", "description": "A basic web scraper with requests and BeautifulSoup."},
            {"name": "javascript_react_component", "language": "javascript", "description": "A simple React functional component."},
        ]
