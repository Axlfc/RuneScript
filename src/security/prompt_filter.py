import logging
from .string_sanitizer import StringSanitizer

logger = logging.getLogger(__name__)

class PromptFilter:
    """Specialized filter for AI prompt context."""

    def __init__(self, sanitizer: StringSanitizer = None):
        self.sanitizer = sanitizer or StringSanitizer()

    def prepare_context(self, context_name: str, content: str) -> str:
        """Wraps content in XML delimiters after sanitization."""
        sanitized = self.sanitizer.sanitize_string(content, max_length=5000)
        escaped = self.sanitizer.escape_xml_delimiters(sanitized)
        # Ensure f-string safety
        safe_content = self.sanitizer.filter_prompt_injection(escaped)

        return f"<{context_name}>\n{safe_content}\n</{context_name}>"
