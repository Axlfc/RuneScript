import json
import os


def read_config_parameter(parameter_path):
    """
    Read a specific parameter from user_config.json (if available) or config.json.

    Parameters:
    - parameter_path: Dot-separated path to the parameter (e.g., "view_options.is_directory_view_visible")

    Returns:
    - The value of the parameter if found, otherwise None.
    """
    user_config_file_path = "data/user_config.json"
    default_config_file_path = "data/config.json"

    # Function to get nested value
    def get_nested_value(data_dict, keys_list):
        current_level = data_dict
        for key in keys_list:
            if isinstance(current_level, dict) and key in current_level:
                current_level = current_level[key]
            else:
                return None  # Key not found
        return current_level

    path_parts = parameter_path.split('.')

    # Try to read from user_config.json first
    try:
        with open(user_config_file_path, 'r') as user_config_file:
            user_config_data = json.load(user_config_file)
            value = get_nested_value(user_config_data, path_parts)
            if value is not None:
                return value
    except FileNotFoundError:
        pass  # user_config.json does not exist, proceed to read from config.json
    except Exception as e:
        print(f"Error reading user_config.json: {e}")
        # Proceed to read from config.json

    # Read from config.json
    try:
        with open(default_config_file_path, 'r') as config_file:
            config_data = json.load(config_file)
            value = get_nested_value(config_data, path_parts)
            return value  # May return None if not found
    except Exception as e:
        print(f"Error reading config.json: {e}")

    # Parameter not found in both user_config.json and config.json
    return None


def write_config_parameter(parameter_path, parameter_value):
    """
    Write a parameter and its value to user_config.json, creating the file if necessary.

    Parameters:
    - parameter_path: Dot-separated path to the parameter (e.g., "view_options.is_directory_view_visible")
    - parameter_value: Value to assign to the parameter.

    Returns:
    - True if the parameter was successfully written, otherwise False.
    """
    user_config_file_path = "data/user_config.json"
    default_config_file_path = "data/config.json"

    # Check if user_config.json exists and is not empty
    if os.path.exists(user_config_file_path) and os.path.getsize(user_config_file_path) > 0:
        try:
            # Read existing user_config.json
            with open(user_config_file_path, 'r') as user_config_file:
                user_config_data = json.load(user_config_file)
        except Exception as e:
            print(f"Error reading user_config.json: {e}")
            return False
    else:
        # Copy data from config.json to user_config.json
        try:
            with open(default_config_file_path, 'r') as default_config_file:
                config_data = json.load(default_config_file)
                user_config_data = config_data
        except Exception as e:
            print(f"Error copying data from config.json: {e}")
            return False

        # Write the initial user_config.json
        try:
            with open(user_config_file_path, 'w') as user_config_file:
                json.dump(user_config_data, user_config_file, indent=4)
        except Exception as e:
            print(f"Error writing user_config.json: {e}")
            return False

    # Update the specific parameter value within the nested structure
    path_parts = parameter_path.split('.')
    current_level = user_config_data

    for part in path_parts[:-1]:
        if part not in current_level:
            current_level[part] = {}
        current_level = current_level[part]

    current_level[path_parts[-1]] = parameter_value

    # Write the updated user_config_data to user_config.json
    try:
        with open(user_config_file_path, 'w') as user_config_file:
            json.dump(user_config_data, user_config_file, indent=4)
        return True
    except Exception as e:
        print(f"Error writing user_config.json: {e}")
        return False


def get_scriptsstudio_directory():
    # Get the current working directory
    project_directory = os.getcwd()

    # Get the absolute path of the current directory
    abs_path = os.path.abspath(project_directory)

    write_config_parameter("options.file_management.scriptsstudio_directory", abs_path)

    return abs_path


def ensure_user_config():
    config_path = 'data/config.json'
    user_config_path = 'data/user_config.json'

    # Check if user_config.json exists
    if not os.path.exists(user_config_path):
        # Open config.json in read mode and create user_config.json in write mode
        with open(config_path, 'r') as config_file:
            with open(user_config_path, 'w') as user_config_file:
                # Read from config.json and write to user_config.json
                user_config_file.write(config_file.read())
        #  print(f"Copied {config_path} to {user_config_path}")
    else:
        #  print(f"{user_config_path} already exists, doing nothing.")
        pass


def load_theme_setting():
    theme = read_config_parameter("options.theme_appearance.theme")
    if theme is None:
        theme = 'cosmo'  # Replace 'default' with your actual default theme
    return theme