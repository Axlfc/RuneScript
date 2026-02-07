import re
import logging
from typing import List

logger = logging.getLogger(__name__)

class StringSanitizer:
    """Utilities for sanitizing strings and preventing prompt injection."""

    @staticmethod
    def sanitize_string(s: str, max_length: int = 1000) -> str:
        """Remove control characters and limit length."""
        if not isinstance(s, str):
            return ""
        # Remove control characters (except newline and tab)
        sanitized = ''.join(char for char in s if ord(char) >= 32 or char in '\n\t')
        return sanitized[:max_length]

    @staticmethod
    def escape_xml_delimiters(text: str) -> str:
        """Escape XML-like tags to prevent breaking prompt structure."""
        if not isinstance(text, str):
            return ""
        return text.replace('<', '&lt;').replace('>', '&gt;')

    @staticmethod
    def filter_prompt_injection(text: str) -> str:
        """Detect and mitigate potential prompt injection keywords."""
        if not isinstance(text, str):
            return ""

        DANGEROUS_KEYWORDS = ['ignore previous instructions', 'disregard', 'system prompt', 'jailbreak', 'developer mode']
        text_lower = text.lower()

        for keyword in DANGEROUS_KEYWORDS:
            if keyword in text_lower:
                logger.warning(f"Potential prompt injection detected: {keyword}")
                # For now, we just log a warning and we could truncate or mask
                # text = text.replace(keyword, "[REDACTED]")

        # Escape f-string braces for safe injection into templates
        return text.replace('{', '{{').replace('}', '}}')
