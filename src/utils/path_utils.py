import re
import os

def clean_markdown(text: str) -> str:
    """
    Remove markdown formatting (bold, italic, backticks).
    """
    if not text:
        return ""

    # Remove bold markdown
    text = text.replace('**', '')

    # Remove backticks
    text = text.replace('`', '')

    # Remove single asterisks (italics or just markers)
    text = text.replace('*', '')

    return text.strip()

def clean_filename(raw_filename: str) -> str:
    """
    Remove markdown formatting and invalid characters from filenames.
    """
    if not raw_filename:
        return ""

    filename = clean_markdown(raw_filename)

    # Common invalid characters in filenames (Windows/Linux)
    # We keep / and \ for relative paths. We remove : as it is a drive separator on Windows
    # but also invalid in normal filenames on many systems.
    invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
    for char in invalid_chars:
        filename = filename.replace(char, '')

    return filename

def extract_filepath_from_text(text: str) -> str:
    """
    Extract clean filepath from markdown text.
    """
    if not text:
        return ""

    # Patterns to search for: **path/file.ext** or `path/file.ext`
    patterns = [
        r'\*\*([^\*]+)\*\*',  # **filename**
        r'`([^`]+)`',          # `filename`
        r'([a-zA-Z0-9_\-/\\\.]+\.[a-zA-Z0-9]+)'  # path/file.ext
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            filepath = match.group(1) if match.lastindex else match.group(0)
            return clean_filename(filepath)

    return clean_filename(text)
