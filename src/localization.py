import json

def load_localization(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


# Assuming your en.json is in the same directory as your Python files
localization_data = load_localization('data/locales/en.json')