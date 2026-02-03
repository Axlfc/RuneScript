import re
import json
import logging
from typing import List, Dict, Optional
from src.models.ai_assistant import AIAssistant
from .plan_parser import Task
from src.utils.path_utils import clean_filename, extract_filepath_from_text
from src.prompts.templates import get_nia_iteration_prompt

class nIAResponse:
    """Structured response from nIA iteration."""
    def __init__(self, raw_response: str):
        self.raw = raw_response
        self.files: Dict[str, str] = self._parse_files(raw_response)
        self.test_file: Optional[str] = self._identify_test_file()
        self.test_name: Optional[str] = self._identify_test_name()

    def _parse_files(self, text: str) -> Dict[str, str]:
        """Extract files from markdown code blocks with filenames."""
        files = {}

        # 1. Primary pattern: File: path/to/file\n```language\ncontent\n```
        pattern = r"File:\s*([^\n]+)\s*\n```[^\n]*\n(.*?)\n```"
        matches = re.finditer(pattern, text, re.DOTALL)
        for match in matches:
            filename = clean_filename(match.group(1).strip())
            if filename:
                content = match.group(2)
                files[filename] = content

        # 2. Fallback pattern: [Any text with filename].ext\n```language\ncontent\n```
        # We always run this to catch files that might not have the "File:" prefix
        fallback_pattern = r"([^\n]*[a-zA-Z0-9_\-\./]+\.[a-zA-Z0-9]+[^\n]*)\n```[^\n]*\n(.*?)\n```"
        matches = re.finditer(fallback_pattern, text, re.DOTALL)
        for match in matches:
            raw_filename_line = match.group(1).strip()
            # Try to extract a clean path from this line
            filename = extract_filepath_from_text(raw_filename_line)

            if filename and filename not in files:
                # Basic validation: must have an extension and not be too long
                if '.' in filename and len(filename) < 255:
                    content = match.group(2)
                    files[filename] = content

        return files

    def _identify_test_file(self) -> Optional[str]:
        for filename in self.files.keys():
            if 'test' in filename.lower():
                return filename
        return None

    def _identify_test_name(self) -> Optional[str]:
        test_file_content = self.files.get(self.test_file or "")
        if test_file_content:
            # Look for def test_...
            match = re.search(r"def\s+(test_[a-zA-Z0-9_]+)", test_file_content)
            if match:
                return match.group(1)
        return None

class nIAClaudeClient:
    """
    Wrapper over existing AIAssistant for nIA loop.
    """

    def __init__(self):
        self.ai = AIAssistant()

    def execute_nia_iteration(
        self,
        spec: str,
        plan: str,
        prompt: str,
        task: Task,
        context: str = ""
    ) -> nIAResponse:
        """
        Execute one nIA iteration.
        """
        is_frontend = "HTML/CSS" in spec or "BeautifulSoup" in spec or "Frontend" in spec

        test_instructions = ""
        if is_frontend:
            test_instructions = """
IMPORTANT FOR FRONTEND PROJECTS:
- Generate standalone Python scripts for testing (e.g., in 'tests/' directory).
- DO NOT use 'import pytest'.
- Use 'assert' for validations and 'print("✅ ...")' for success messages.
- Include 'if __name__ == "__main__":' to execute all test functions.
- You can use 'from bs4 import BeautifulSoup' for HTML parsing.
- If the task involves creating a project structure, ensure that your implementation code includes at least one file for each directory that needs to exist (use '.gitkeep' if the directory is intended to be empty).
"""

        full_prompt = get_nia_iteration_prompt(prompt, test_instructions, spec, plan, context, task.description)

        response = self.ai.generate(full_prompt)

        # LOG RAW RESPONSE
        logging.info("=" * 80)
        logging.info("RAW LLM RESPONSE:")
        logging.info("=" * 80)
        logging.info(response)
        logging.info("=" * 80)

        return nIAResponse(response)
