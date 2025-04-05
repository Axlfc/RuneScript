import json
import re
import logging
import unicodedata
from typing import Optional, Union, Dict, List


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
        """Normalize and strip unsafe characters from user prompt."""
        if not isinstance(prompt, str):
            return ""
        clean = ''.join(
            c for c in unicodedata.normalize('NFKD', prompt)
            if unicodedata.category(c)[0] != 'C'  # Remove control chars
        )
        return clean.strip()

    @staticmethod
    def validate_prompt(prompt: str) -> bool:
        """Ensure the prompt is descriptive enough for generation."""
        if not prompt or len(prompt) < 10:
            return False

        lowered = prompt.lower()
        has_keyword = any(word in lowered for word in (
            'create', 'build', 'design', 'develop', 'generate', 'html', 'website',
            'app', 'api', 'tool', 'script', 'python', 'js', 'game', 'component'
        ))

        return has_keyword

    @staticmethod
    def parse_ai_response(response: Optional[str]) -> Union[Dict, List, None]:
        """Extracts and parses the first valid JSON object or array from an AI response."""
        if not response:
            logging.warning("Empty response received for parsing.")
            return None

        try:
            return json.loads(response)
        except Exception:
            pass  # Try extracting manually

        json_match = re.search(r'(\{.*\}|\[.*\])', response, re.DOTALL)
        if json_match:
            candidate = json_match.group(1)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError as e:
                logging.error(f"Regex-extracted JSON failed to parse: {e}")

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

        logging.warning("Failed to extract valid JSON from AI response.")
        return None
