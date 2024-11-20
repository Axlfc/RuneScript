import json


def load_localization(file_path="data/locales/en.json"):
    if file_path == "data/locales/.json":
        file_path = "data/locales/en.json"
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

