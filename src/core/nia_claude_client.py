import re
import json
import logging
import os
from typing import List, Dict, Optional
from src.models.ai_assistant import AIAssistant
from .plan_parser import Task
from .robust_parser import RobustJSONParser
from src.utils.path_utils import clean_filename, extract_filepath_from_text
from src.prompts.templates import get_nia_iteration_prompt

SYSTEM_MANAGED_FILES = {
    'IMPLEMENTATION_PLAN.md',
    '.nia_config.json',
    'nia_metrics.json',
    '.gitignore'
}

class nIAResponse:
    """Structured response from nIA iteration."""
    def __init__(self, raw_response: str):
        self.raw = raw_response
        self.parsing_method = "unknown"
        self.files: Dict[str, str] = self._parse_files(raw_response)
        self.files = self._filter_system_files(self.files)
        self.test_file = self._identify_test_file()
        self.test_name: Optional[str] = self._identify_test_name()

    def _sanitize_llm_json(self, raw_response: str) -> str:
        """Fix common JSON formatting errors from LLM, like template literals."""
        import re

        # Fix template literals (backticks) -> JSON strings for specific keys
        def fix_backtick_content(match):
            key = match.group(1)
            content = match.group(2)
            # Escape backslashes first, then quotes
            content = content.replace('\\', '\\\\').replace('"', '\\"')
            # Replace actual newlines with \n
            content = content.replace('\n', '\\n').replace('\r', '')
            return f'"{key}": "{content}"'

        # Pattern: "key": `value`
        sanitized = re.sub(
            r'"(content|path|File)"\s*:\s*`([^`]*)`',
            fix_backtick_content,
            raw_response,
            flags=re.DOTALL
        )

        return sanitized

    def _detect_response_format(self, text: str) -> str:
        """Detect if response is Gemini markdown or Ollama JSON."""
        # Try to extract JSON first
        data = RobustJSONParser.extract_json(text)
        if data:
            if 'files' in data and isinstance(data['files'], list):
                return 'ollama_json'
            if 'tasks' in data and isinstance(data['tasks'], list):
                return 'ollama_json_tasks'
            # If it's some other JSON but we don't recognize the structure,
            # we might still want to try parsing it if it has files
            if any(k in data for k in ['files', 'tasks']):
                return 'ollama_json'

        # If no clear JSON structure, assume markdown
        if 'File:' in text or '```' in text or '<file' in text:
            return 'gemini_markdown'

        return 'unknown'

    def _parse_ollama_json(self, text: str) -> Dict[str, str]:
        """Parse Ollama JSON format: {"files": [{"path": "...", "content": "..."}]}"""
        files = {}
        data = RobustJSONParser.extract_json(text)

        if not data:
            return files

        if 'files' in data:
            for file_obj in data['files']:
                if isinstance(file_obj, dict):
                    path = file_obj.get('path', '').strip() or file_obj.get('File', '').strip()
                    content = file_obj.get('content', '')

                    if path:
                        path = os.path.normpath(path).replace('\\', '/')
                        if path.startswith('./'): path = path[2:]
                        files[path] = content
                        logging.info(f"  ✅ Parsed (JSON): {path} ({len(content)} chars)")

        return files

    def _parse_ollama_json_tasks(self, text: str) -> Dict[str, str]:
        """Parse Ollama format: {"tasks": [{"implementation": {"code_blocks": [...]}}]}"""
        files = {}
        data = RobustJSONParser.extract_json(text)

        if not data:
            return files

        if 'tasks' in data:
            for task in data['tasks']:
                if not isinstance(task, dict): continue
                impl = task.get('implementation', {})
                if not isinstance(impl, dict): continue
                code_blocks = impl.get('code_blocks', [])

                if isinstance(code_blocks, list):
                    for block in code_blocks:
                        if not isinstance(block, dict): continue
                        # Support both "File" and "path" keys
                        file_path = block.get('File', '').strip() or block.get('path', '').strip()
                        content = block.get('content', '')

                        if file_path:
                            file_path = os.path.normpath(file_path).replace('\\', '/')
                            if file_path.startswith('./'): file_path = file_path[2:]
                            files[file_path] = content
                            logging.info(f"  ✅ Parsed (JSON Tasks): {file_path} ({len(content)} chars)")

        return files

    def _parse_ollama_json_manual(self, text: str) -> Dict[str, str]:
        """Manually extract files using regex when JSON parsing fails (e.g. invalid escapes or literal newlines)."""
        files = {}

        # Patterns for path and content
        path_pattern = r'"(?:path|File)"\s*:\s*"([^"]+)"'
        content_start_pattern = r'"content"\s*:\s*"'

        last_pos = 0
        while True:
            # Search from last position
            path_match = re.search(path_pattern, text[last_pos:])
            if not path_match:
                break

            path = path_match.group(1)
            path_end = last_pos + path_match.end()

            # Look for content following the path
            content_match = re.search(content_start_pattern, text[path_end:])
            if not content_match:
                last_pos = path_end
                continue

            content_start = path_end + content_match.end()

            # Find the end of content: " followed by optional whitespace and then , or } or ] or end of string
            # We use DOTALL because content might have literal newlines
            content_end_match = re.search(r'"\s*(?:,|\}|\]|$)', text[content_start:], re.DOTALL)

            if content_end_match:
                content_end = content_start + content_end_match.start()
                content = text[content_start:content_end]

                # Basic unescaping for manual parsing
                content = content.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')

                path = os.path.normpath(path).replace('\\', '/')
                if path.startswith('./'): path = path[2:]

                if path and content:
                    files[path] = content
                    logging.info(f"  ✅ Parsed (Manual Regex): {path} ({len(content)} chars)")

                last_pos = content_start + content_end_match.end()
            else:
                last_pos = path_end

        return files

    def _filter_system_files(self, files: Dict[str, str]) -> Dict[str, str]:
        """Removes files that the LLM should not modify."""
        filtered = {}
        for path, content in files.items():
            basename = os.path.basename(path)
            if basename in SYSTEM_MANAGED_FILES or path in SYSTEM_MANAGED_FILES:
                logging.warning(f"🚫 AI attempted to modify system file: {path}. Ignoring this file.")
                continue
            filtered[path] = content
        return filtered

    def _parse_files(self, text: str) -> Dict[str, str]:
        """Extract files from LLM response (Gemini OR Ollama format)."""
        files = {}

        logging.info("--- Starting Universal File Parsing ---")

        # 0. Pre-processing: Fix common JSON errors like backticks
        text = self._sanitize_llm_json(text)

        # 0.1. If the whole response is one big code block, strip it
        stripped_text = text.strip()
        if stripped_text.startswith('```') and stripped_text.endswith('```'):
            if stripped_text.count('File:') > 1 or stripped_text.count('Archivo:') > 1:
                logging.info("  Detected whole response wrapped in code block. Stripping markers for parsing...")
                lines = stripped_text.split('\n')
                if len(lines) > 2:
                    text = '\n'.join(lines[1:-1])

        # 1. Attempt STRICT JSON
        format_type = self._detect_response_format(text)
        if format_type == 'ollama_json':
            files = self._parse_ollama_json(text)
            if files:
                self.parsing_method = "strict_json"
        elif format_type == 'ollama_json_tasks':
            files = self._parse_ollama_json_tasks(text)
            if files:
                self.parsing_method = "strict_json_tasks"

        if files:
            logging.info(f"📦 Total files extracted (Strict JSON): {len(files)}")
            return files

        # 2. Attempt JSON with manual unescaping/regex
        files = self._parse_ollama_json_manual(text)
        if files:
            logging.info(f"📦 Total files extracted (Cleaned/Manual JSON): {len(files)}")
            self.parsing_method = "manual_json"
            return files

        # 3. Fallback to Markdown parsing logic
        logging.info("Falling back to Markdown parsing logic...")

        # 1. XML-style tags: <file path="path/to/file">content</file>
        xml_pattern = r'<file\s+path=["\']([^"\']+)["\']\s*>(.*?)</file>'
        xml_matches = re.finditer(xml_pattern, text, re.DOTALL | re.IGNORECASE)
        for match in xml_matches:
            filename = clean_filename(match.group(1).strip())
            filename = os.path.normpath(filename).replace('\\', '/')
            if filename.startswith('./'): filename = filename[2:]

            content = match.group(2)
            if filename not in files:
                files[filename] = content
                logging.info(f"  Detected (XML Tag): {filename} ({len(content)} chars)")

        # 2. Split-based approach to isolate sections starting with "File:"
        # This is more robust against descriptive text between the filename and code block
        sections = re.split(r'(?i)(?:File|Archivo|Ruta|Path|Archivo de código):', text)

        for section in sections[1:]:  # Skip text before first marker
            lines = section.strip().split('\n')
            if not lines:
                continue

            # Extract filename from the first line of the section (cleaning markdown)
            raw_path = lines[0].strip()
            filename = clean_filename(raw_path)

            # Normalize path to prevent duplicates like ./file.js and file.js
            filename = os.path.normpath(filename).replace('\\', '/')
            if filename.startswith('./'):
                filename = filename[2:]

            # Find the FIRST code block in this section
            # Robust pattern to catch empty files (like .gitkeep) and files without trailing newline
            block_match = re.search(r'```[^\n]*\n?(.*?)\n?```', section, re.DOTALL)

            # Use code block if found and not empty (unless it's a .gitkeep)
            if filename and block_match and (block_match.group(1).strip() or filename.endswith('.gitkeep')):
                content = block_match.group(1)

                # If it's a .gitkeep or empty file, ensure it's treated correctly
                if not content.strip() and filename.endswith('.gitkeep'):
                    content = ""

                if filename not in files:
                    files[filename] = content
                    logging.info(f"  Detected (Split): {filename} ({len(content)} chars)")

            elif filename:
                # FALLBACK: If no code block found in section, use the rest of the section as content
                # This handles cases where code is NOT wrapped in internal blocks (e.g. LLM used one big block)
                content = '\n'.join(lines[1:]).strip()

                # Basic cleanup of stray markers that might have been part of the split
                if content.endswith('```'):
                    content = content[:-3].strip()

                if content or filename.endswith('.gitkeep'):
                    if filename not in files:
                        files[filename] = content
                        logging.info(f"  Detected (Split-Fallback): {filename} ({len(content)} chars)")

        # 3. Fallback pattern: catch files that might not have the "File:" prefix
        # but have a filename on a line before a code block
        # Pattern: line with filename, followed by optional lines, then code block
        fallback_pattern = r"([a-zA-Z0-9_\-\./\\]+\.[a-zA-Z0-9]+)[^\n]*\n(?:.*?\n)*?```[^\n]*\n?(.*?)\n?```"
        matches = list(re.finditer(fallback_pattern, text, re.DOTALL | re.IGNORECASE))

        # Track basenames already handled with a path
        paths_by_basename = {os.path.basename(p): p for p in files.keys()}

        for match in matches:
            filename = clean_filename(match.group(1).strip())
            filename = os.path.normpath(filename).replace('\\', '/')
            if filename.startswith('./'):
                filename = filename[2:]

            basename = os.path.basename(filename)

            if filename and filename not in files:
                content = match.group(2)

                # Allow empty content for .gitkeep
                if not content.strip() and filename.endswith('.gitkeep'):
                    content = ""
                elif not content.strip():
                    continue

                # SKIP if we already have this basename in a more specific path detected via Split
                if basename in paths_by_basename and paths_by_basename[basename] != filename:
                    logging.warning(f"  Skipping fallback duplicate basename: {filename} (already have {paths_by_basename[basename]})")
                    continue

                # Basic validation: must have an extension and not be too long
                allowed_exts = {'.py', '.html', '.css', '.js', '.json', '.md', '.txt', '.sh', '.sql', '.gitkeep'}
                ext = os.path.splitext(filename)[1].lower()

                if (ext in allowed_exts or filename.endswith('.gitkeep')) and len(filename) < 255:
                    content = match.group(2)
                    files[filename] = content
                    logging.info(f"  Detected (Fallback): {filename} ({len(content)} chars)")
                    paths_by_basename[basename] = filename

        if files:
            self.parsing_method = "markdown_fallback"
            # Strict validation for markdown fallback
            if not self._validate_markdown_extraction(files):
                 logging.warning("⚠️ Markdown extraction failed strict validation.")
                 return {}

        logging.info(f"Total unique files extracted: {len(files)}")
        return self._strip_root_folders(files)

    def _strip_root_folders(self, files: Dict[str, str]) -> Dict[str, str]:
        """Removes common root folder prefixes like 'project/' if they wrap all files."""
        if len(files) < 1:
            return files

        # Potential roots to strip
        potential_roots = ['project/', 'src/', 'app/']

        for root in potential_roots:
            if all(f.startswith(root) for f in files.keys()):
                # Check that we don't strip something important if there's only one file
                # but usually if all files are under 'project/' it's a wrapper
                logging.info(f"  📂 Detected common root folder '{root}'. Stripping from all paths.")
                return {f[len(root):]: c for f, c in files.items()}

        return files

    def _validate_markdown_extraction(self, files: Dict[str, str]) -> bool:
        """Validates that markdown extraction didn't result in obvious garbage."""
        if not files:
            return False

        for path, content in files.items():
            # Basic sanity checks
            if len(path) > 255 or not content.strip():
                if not path.endswith('.gitkeep'):
                    return False

            # Check for unfinished code blocks in content
            if content.count('```') % 2 != 0:
                logging.warning(f"Possible truncated code block in {path}")
                # We might still allow it but it's a warning signal

        return True

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
        context: str = "",
        ram_context: str = "",
        agents_rules: str = ""
    ) -> nIAResponse:
        """
        Execute one nIA iteration.
        """
        is_frontend = "HTML/CSS" in spec or "BeautifulSoup" in spec or "Frontend" in spec

        test_instructions = ""
        if is_frontend:
            test_instructions = """
IMPORTANT FOR FRONTEND PROJECTS:
- Generate standalone Python scripts for testing (e.g., in 'tests/test_structure.py').
- DO NOT use 'import pytest'.
- **NEVER use `requests.get()` for local files**: Read them from disk with `open()`.
- Use 'from bs4 import BeautifulSoup' for HTML parsing.
- Use 'assert' for validations and 'print("✅ ...")' for success messages.
- Include 'if __name__ == "__main__":' to execute all test functions.
- **ROBUST VALIDATION**: Use `in` or `.endswith()` for path checks (e.g., `assert 'css/style.css' in link['href']`).
- **DIAGNOSTICS**: If an assertion fails, print the actual value for debugging.
  Example: `if 'css/style.css' not in link['href']: print(f"DEBUG: Found href='{{link['href']}}'"); assert False`
- If the task involves creating a project structure, ensure that your implementation code includes at least one file for each directory that needs to exist (use '.gitkeep' if the directory is intended to be empty).
"""

        full_prompt = get_nia_iteration_prompt(prompt, test_instructions, spec, plan, context, task.description, ram_context, agents_rules)

        response = self.ai.generate(full_prompt)

        # LOG RAW RESPONSE
        logging.info("=" * 80)
        logging.info("RAW LLM RESPONSE:")
        logging.info("=" * 80)
        logging.info(response)
        logging.info("=" * 80)

        return nIAResponse(response)
