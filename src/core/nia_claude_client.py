import re
import json
import logging
import os
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

        logging.info("--- Starting Robust File Parsing ---")

        # 1. Split-based approach to isolate sections starting with "File:"
        # This is more robust against descriptive text between the filename and code block
        sections = re.split(r'(?i)(?:File|Archivo|Ruta|Path|Archivo de código):', text)

        for section in sections[1:]:  # Skip text before first marker
            lines = section.strip().split('\n')
            if not lines:
                continue

            # Extract filename from the first line of the section (cleaning markdown)
            raw_path = lines[0].strip()
            filename = clean_filename(raw_path)

            # Find the FIRST code block in this section
            block_match = re.search(r'```[^\n]*\n(.*?)\n```', section, re.DOTALL)
            if filename and block_match:
                content = block_match.group(1)
                if filename not in files:
                    files[filename] = content
                    logging.info(f"  Detected (Split): {filename} ({len(content)} chars)")

        # 2. Fallback pattern: catch files that might not have the "File:" prefix
        # but have a filename on a line before a code block
        # Pattern: line with filename, followed by optional lines, then code block
        fallback_pattern = r"([a-zA-Z0-9_\-\./\\]+\.[a-zA-Z0-9]+)[^\n]*\n(?:.*?\n)*?```[^\n]*\n(.*?)\n```"
        matches = list(re.finditer(fallback_pattern, text, re.DOTALL | re.IGNORECASE))

        for match in matches:
            filename = clean_filename(match.group(1).strip())
            if filename and filename not in files:
                # Basic validation: must have an extension and not be too long
                allowed_exts = {'.py', '.html', '.css', '.js', '.json', '.md', '.txt', '.sh', '.sql'}
                ext = os.path.splitext(filename)[1].lower()

                if ext in allowed_exts and len(filename) < 255:
                    content = match.group(2)
                    files[filename] = content
                    logging.info(f"  Detected (Fallback): {filename} ({len(content)} chars)")

        logging.info(f"Total unique files extracted: {len(files)}")
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
