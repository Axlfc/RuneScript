from typing import List, Dict, Any
import logging
import os


def detect_relevant_files(prompt: str, project_path: str) -> List[str]:
    """
    Naive keyword-to-filename mapping to detect likely relevant files based on prompt.
    """
    relevant_map = {
        "html": ["index.html"],
        "css": ["style.css", "styles.css", "main.css"],
        "javascript": ["scripts.js", "main.js", "app.js"],
        "design": ["index.html", "style.css", "scripts.js"],
        "webpage": ["index.html", "style.css", "scripts.js"],
        "portfolio": ["index.html", "style.css", "scripts.js"],
        "landing": ["index.html"],
        "backend": ["app.py", "main.py", "api.py"],
        "api": ["app.py", "api.py"],
        "test": ["test_", "_test.py"]
    }

    prompt = prompt.lower()
    matched_files = set()

    for keyword, files in relevant_map.items():
        if keyword in prompt:
            for fname in files:
                full_path = os.path.join(project_path, fname)
                if os.path.exists(full_path):
                    matched_files.add(full_path)

    return list(matched_files)


def enrich_context_with_relevant_files(context: Dict[str, Any], project_path: str) -> Dict[str, Any]:
    prompt_text = context.get("prompt") or context.get("project_scope", {}).get("description", "")
    relevant_files = detect_relevant_files(prompt_text, project_path)
    enriched_files = []

    for file_path in relevant_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                enriched_files.append({
                    "filename": os.path.relpath(file_path, project_path),
                    "content": f.read()
                })
        except Exception as e:
            logging.warning(f"Failed to read relevant file: {file_path}: {e}")

    if enriched_files:
        context["relevant_files"] = enriched_files
        context["instruction"] = (
            f"Update the following files to match the goal: '{prompt_text}'. "
            "Only change what's necessary. Do not delete unrelated code."
        )
    return context


