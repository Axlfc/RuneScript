from typing import Dict, List, Tuple
import os
import json

class LanguageManager:
    def __init__(self, locales_dir: str = "data/locales"):
        self.locales_dir = locales_dir

    def get_available_languages(self) -> List[Tuple[str, str]]:
        """
        Scans the locales directory and returns a list of tuples containing
        (language_code, language_name)
        """
        available_languages = []

        # Dictionary of language codes to their full names in English
        language_names = {
            "en": "English",
            "es": "Español (Spanish)",
            "ca": "Català (Catalan)",
            "fr": "Français (French)",
            "de": "Deutsch (German)",
            "it": "Italiano (Italian)",
            "pt": "Português (Portuguese)",
            # Add more languages as needed
        }

        try:
            # List all JSON files in the locales directory
            for file_name in os.listdir(self.locales_dir):
                if file_name.endswith('.json'):
                    lang_code = file_name[:-5]  # Remove .json extension
                    # Get the language name, fallback to code if not in our dictionary
                    lang_name = language_names.get(lang_code, lang_code)
                    available_languages.append((lang_code, lang_name))

            # Sort by language name
            available_languages.sort(key=lambda x: x[1])
            return available_languages

        except FileNotFoundError:
            print(f"Locales directory not found: {self.locales_dir}")
            return [("en", "English")]  # Default fallback

    def load_language_file(self, lang_code: str) -> Dict:
        """
        Loads the language file for the given language code
        """
        try:
            file_path = os.path.join(self.locales_dir, f"{lang_code}.json")
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            file_path = os.path.join(self.locales_dir, "en.json")
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
