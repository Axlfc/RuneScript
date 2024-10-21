import json

def load_localization(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)
localization_data = load_localization('data/locales/en.json')