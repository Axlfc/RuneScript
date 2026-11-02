import json
import re
import logging
import unicodedata
from typing import Optional, Union, Dict, List, Any


def extract_code_blocks(markdown: str) -> Dict[str, str]:
    """
    Extract code blocks in Markdown formatted with filenames.
    Format: ```<language> # filename: path/to/file.py\n<code>\n```
    """
    pattern = r"```[\w+-]*\s*#\s*filename:\s*(.+?)\s*\n(.*?)```"
    matches = re.findall(pattern, markdown, re.DOTALL)
    return {filename.strip(): content.strip() for filename, content in matches}


def create_default_metadata(name, error_message):
    """Helper function to create default metadata with error information."""
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
    _METADATA_KEYS = {
        "project_name",
        "project_description",
        "project_structure",
        "key_features",
        "project_tasks",
        "implemented_features",
        "planned_features",
        "feature_priorities",
        "validation_notes",
        "initial_files",
        "code_files",
        "next_steps",
    }

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

    @classmethod
    def _looks_like_metadata(cls, value: Any) -> bool:
        return isinstance(value, dict) and bool(cls._METADATA_KEYS.intersection(value.keys()))

    @classmethod
    def _extract_json_values(cls, response: str) -> List[Union[Dict, List]]:
        """
        Scan noisy LLM output for independently decodable JSON values.

        Unlike a greedy {.*} regex, JSONDecoder.raw_decode stops at the end of
        each valid JSON value and safely skips braces belonging to prose or code.
        """
        decoder = json.JSONDecoder()
        values: List[Union[Dict, List]] = []
        seen_starts = set()

        for index, char in enumerate(response):
            if char not in "{[" or index in seen_starts:
                continue

            try:
                value, consumed = decoder.raw_decode(response[index:])
            except json.JSONDecodeError:
                continue

            if isinstance(value, (dict, list)):
                values.append(value)
                seen_starts.add(index)
                # No need to manually skip nested positions: metadata candidates
                # are preferred below, and duplicate values are harmless.

        return values

    @classmethod
    def parse_ai_response(cls, response: Optional[str]) -> Union[Dict, List, None]:
        """
        Parse structured LLM output without treating arbitrary code braces as JSON.

        Supports pure JSON, JSON embedded in explanatory text, escaped JSON in a
        raw wrapper, and Markdown filename code blocks.
        """
        if not response:
            logging.warning("Empty response received for parsing.")
            return None

        response = response.strip()

        # Strategy 1: pure JSON is the normal/expected contract.
        try:
            parsed = json.loads(response)
            if isinstance(parsed, dict) and isinstance(parsed.get("raw"), str):
                nested = cls.parse_ai_response(parsed["raw"])
                return nested if nested is not None else parsed
            return parsed
        except json.JSONDecodeError:
            pass

        # Strategy 2: fenced JSON block, if the provider ignored the no-Markdown rule.
        fenced_matches = re.findall(r"```(?:json)?\s*(.*?)```", response, re.DOTALL | re.IGNORECASE)
        for fenced in fenced_matches:
            try:
                parsed = json.loads(fenced.strip())
            except json.JSONDecodeError:
                continue
            if cls._looks_like_metadata(parsed):
                return parsed

        # Strategy 3: scan for valid JSON values rather than using a greedy regex.
        values = cls._extract_json_values(response)
        for value in values:
            if cls._looks_like_metadata(value):
                return value

        # Preserve legacy support for non-metadata structured responses.
        if values:
            return values[0]

        # Strategy 4: legacy escaped JSON in a "raw" field that was not itself
        # valid JSON because of surrounding provider output.
        if '"raw":' in response:
            raw_match = re.search(r'"raw"\s*:\s*"(.*?)"\s*[,}]', response, re.DOTALL)
            if raw_match:
                try:
                    raw_content = json.loads(f'"{raw_match.group(1)}"')
                except json.JSONDecodeError:
                    raw_content = raw_match.group(1).encode("utf-8").decode("unicode_escape")
                nested = cls.parse_ai_response(raw_content)
                if nested is not None:
                    return nested

        # Strategy 5: project files explicitly tagged in Markdown.
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
