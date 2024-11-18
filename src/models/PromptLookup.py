import os
import json
from difflib import get_close_matches
from typing import List, Dict, Optional, Tuple


class PromptLookup:
    def __init__(self, prompt_folder: str):
        self.prompt_folder = prompt_folder
        self.alias_cache: Dict[str, dict] = {}
        self.ensure_prompt_folder_exists()
        self.refresh_cache()

    def ensure_prompt_folder_exists(self):
        """Ensure the prompt folder exists, create if it doesn't."""
        if not os.path.exists(self.prompt_folder):
            os.makedirs(self.prompt_folder)
            print(f"Created missing prompt folder: {self.prompt_folder}")

    def refresh_cache(self):
        """Refresh the alias cache from prompt files."""
        self.alias_cache.clear()
        for filename in os.listdir(self.prompt_folder):
            if filename.endswith('.json') and filename != "categories.json":
                try:
                    with open(os.path.join(self.prompt_folder, filename), 'r') as f:
                        prompt_data = json.load(f)
                        if 'alias' in prompt_data:
                            self.alias_cache[prompt_data['alias']] = prompt_data
                except Exception as e:
                    print(f"Error reading file {filename}: {e}")
                    continue

    def find_prompt_by_alias(self, alias: str) -> Optional[dict]:
        """Find an exact match for a prompt alias."""
        return self.alias_cache.get(alias)

    def get_fuzzy_matches(self, partial_alias: str, min_score: float = 0.6) -> List[Tuple[str, float]]:
        """
        Find fuzzy matches for a partial alias.
        Returns list of tuples (alias, score) sorted by score.
        """
        if not partial_alias:
            return []

        # Get all aliases
        aliases = list(self.alias_cache.keys())

        # First try prefix matching
        prefix_matches = [(alias, 1.0) for alias in aliases if alias.startswith(partial_alias)]

        # Then try fuzzy matching for non-prefix matches
        fuzzy_matches = []
        for alias in aliases:
            if not alias.startswith(partial_alias):
                # Calculate Levenshtein ratio
                score = self._calculate_similarity(partial_alias, alias)
                if score >= min_score:
                    fuzzy_matches.append((alias, score))

        # Combine and sort results
        all_matches = prefix_matches + fuzzy_matches
        return sorted(all_matches, key=lambda x: (-x[1], x[0]))

    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity score between two strings."""
        try:
            matches = get_close_matches(s1, [s2], n=1, cutoff=0.0)
            return len(matches[0]) / max(len(s1), len(s2)) if matches else 0.0
        except Exception:
            return 0.0

    def get_completions(self, partial_alias: str) -> List[str]:
        """Get tab completion suggestions for a partial alias."""
        matches = self.get_fuzzy_matches(partial_alias, min_score=0.4)
        return [alias for alias, _ in matches]


class PromptInterpreter:
    def __init__(self, prompt_lookup: PromptLookup):
        self.prompt_lookup = prompt_lookup
        self.current_completion_index = 0
        self.current_completions: List[str] = []
        self.last_tab_partial: Optional[str] = None

    def interpret_input(self, text: str) -> Optional[dict]:
        """Interpret input text to find prompt if it starts with /."""
        if not text.startswith('/'):
            return None

        alias = text[1:].strip()
        return self.prompt_lookup.find_prompt_by_alias(alias)

    def handle_tab_completion(self, text: str) -> Optional[str]:
        """Handle tab completion for prompt aliases."""
        if not text.startswith('/'):
            return None

        partial = text[1:].strip()

        # If this is a new tab completion sequence
        if partial != self.last_tab_partial:
            self.current_completions = self.prompt_lookup.get_completions(partial)
            self.current_completion_index = 0
            self.last_tab_partial = partial

        # If we have completions, return the next one
        if self.current_completions:
            completion = self.current_completions[self.current_completion_index]
            self.current_completion_index = (self.current_completion_index + 1) % len(self.current_completions)
            return f"/{completion}"

        return None


def setup_prompt_completion(input_widget, prompt_interpreter):
    """Set up tab completion for a text input widget."""

    def handle_tab(event):
        current_text = input_widget.get("1.0", "end-1c").strip()
        completion = prompt_interpreter.handle_tab_completion(current_text)

        if completion:
            input_widget.delete("1.0", "end")
            input_widget.insert("1.0", completion)
            return "break"  # Prevent default tab behavior

        return None  # Allow default tab behavior

    input_widget.bind("<Tab>", handle_tab)
