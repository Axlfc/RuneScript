import json
import re
import logging
import unicodedata
from typing import Optional, Union, Dict, List


def extract_code_blocks(markdown: str) -> Dict[str, str]:
    """
    Extract code blocks in Markdown formatted with filenames.
    Format: ```<language> # filename: path/to/file.py\n<code>\n```
    """
    pattern = r"```[\w+-]*\s*#\s*filename:\s*(.+?)\s*\n(.*?)```"
    matches = re.findall(pattern, markdown, re.DOTALL)
    return {filename.strip(): content.strip() for filename, content in matches}


def create_default_metadata(name, error_message):
    """Helper function to create default metadata with error information"""
    return {
        'project_name': name,
        'project_description': error_message,
        'project_structure': [],
        'key_features': [],
        'project_tasks': ['Resolve AI response parsing error'],
        'implemented_features': [],
        'planned_features': [],
        'feature_priorities': {
            'high': [],
            'medium': [],
            'low': []
        },
        'validation_notes': [error_message]
    }


class AIResponseParser:
    @staticmethod
    def sanitize_prompt(prompt: str) -> str:
        """
        Sanitize and enhance the user prompt to improve AI response quality.
        """
        sanitized = prompt.strip()

        # Web project context enhancer
        web_keywords = ["html", "website", "webpage", "web page", "site", "landing page"]
        is_web_project = any(keyword in sanitized.lower() for keyword in web_keywords)

        if is_web_project:
            if "project structure" not in sanitized.lower():
                sanitized += "\n\nPlease include HTML, CSS, and JavaScript files organized in a proper structure."
            if "responsive" not in sanitized.lower():
                sanitized += "\nMake sure the design is responsive and works well on all devices."

        return sanitized

    @staticmethod
    def validate_prompt(prompt: str) -> bool:
        """
        Check if the prompt is clear and meaningful.
        """
        if not prompt or len(prompt.strip()) < 5:
            return False
        return len(prompt.split()) >= 3

    @staticmethod
    def parse_ai_response(response: Optional[str]) -> Union[Dict, List, None]:
        """
        Attempts to parse a structured response from the AI output.
        Supports JSON, escaped JSON, and Markdown code blocks with filenames.
        """
        if not response:
            logging.warning("Empty response received for parsing.")
            return None

        # Try direct JSON first
        try:
            return json.loads(response)
        except Exception:
            pass

        # Try regex-extracted JSON
        json_match = re.search(r'(\{.*\}|\[.*\])', response, re.DOTALL)
        if json_match:
            candidate = json_match.group(1)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError as e:
                logging.error(f"Regex-extracted JSON failed to parse: {e}")

        # Handle escaped JSON in "raw" field
        if '"raw":' in response:
            raw_match = re.search(r'"raw"\s*:\s*"(.+?)"', response, re.DOTALL)
            if raw_match:
                raw_content = raw_match.group(1).encode('utf-8').decode('unicode_escape')
                try:
                    json_start = raw_content.find('{')
                    json_end = raw_content.rfind('}') + 1
                    if json_start != -1 and json_end > json_start:
                        return json.loads(raw_content[json_start:json_end])
                except json.JSONDecodeError as e:
                    logging.warning(f"Failed to parse JSON inside raw field: {e}")

        # Fallback to extracting Markdown code blocks
        code_blocks = extract_code_blocks(response)
        if code_blocks:
            return {
                "initial_files": code_blocks,
                "project_name": "Markdown Project",
                "project_description": "Extracted from Markdown format",
                "project_structure": list(code_blocks.keys()),
                "key_features": [],
                "project_tasks": [],
                "implemented_features": [],
                "planned_features": [],
                "feature_priorities": {"high": [], "medium": [], "low": []},
                "validation_notes": ["Parsed from markdown-style code blocks."]
            }

        logging.warning("Failed to extract valid data from AI response.")
        return None
