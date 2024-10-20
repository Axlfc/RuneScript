import json


def load_localization(file_path):
    """
    load_localization

    Args:
        file_path (Any): Description of file_path.

    Returns:
        None: Description of return value.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


localization_data = load_localization("data/locales/en.json")
