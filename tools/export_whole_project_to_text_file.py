import os


def export_python_scripts_to_txt(directory, output_filename):
    # Ensure the directory exists
    if not os.path.isdir(directory):
        print(f"The directory {directory} does not exist.")
        return

    try:
        with open(output_filename, 'w', encoding='utf-8') as output_file:
            # Iterate over all files in the directory
            for filename in os.listdir(directory):
                if filename.endswith('.py'):
                    filepath = os.path.join(directory, filename)
                    # Read the content of the Python file
                    with open(filepath, 'r', encoding='utf-8') as file:
                        content = file.read()
                        # Write the content to the output file in the desired format
                        output_file.write(f'{filename}:\n"""\n{content}\n"""\n\n')
            print(f"Exported Python scripts to {output_filename}")
    except Exception as e:
        print(f"An error occurred: {e}")


# Example usage
main_directory_path = 'X:\\Documents\\Python Projects\\ScriptsEditor\\src'
# main_directory_path = 'C:\\Users\\user\\Documents\\git\\ScriptsEditor\\src'

models = main_directory_path + "\\models"
models_output_file = 'exported_models.txt'

views = main_directory_path + "\\views"
views_output_file = 'exported_views.txt'

controllers = main_directory_path + "\\controllers"
controllers_output_file = 'exported_controllers.txt'


# export_python_scripts_to_txt(models, models_output_file)
# export_python_scripts_to_txt(views, views_output_file)
# export_python_scripts_to_txt(controllers, controllers_output_file)

def export_all_python_scripts_to_txt_from_mvc_project(main_directory_path, output_filename):
    # Define the sections for export
    sections = {
        "models": os.path.join(main_directory_path, "models"),
        "views": os.path.join(main_directory_path, "views"),
        "controllers": os.path.join(main_directory_path, "controllers"),
    }

    # Ensure the main directory exists
    if not os.path.isdir(main_directory_path):
        print(f"The main directory {main_directory_path} does not exist.")
        return

    try:
        with open(output_filename, 'w', encoding='utf-8') as output_file:
            # Process each section
            for section_name, directory in sections.items():
                output_file.write(f'{section_name}:\n```\n')
                # Ensure the section directory exists
                if not os.path.isdir(directory):
                    output_file.write(f"The directory for {section_name} does not exist.\n")
                    continue

                # Iterate over all files in the directory
                for filename in os.listdir(directory):
                    if filename.endswith('.py'):
                        filepath = os.path.join(directory, filename)
                        # Read the content of the Python file
                        with open(filepath, 'r', encoding='utf-8') as file:
                            content = file.read()
                            # Write the content to the output file in the desired format
                            output_file.write(f'{filename}:\n{content}\n\n')
                output_file.write('```\n\n')
            print(f"Exported all Python scripts to {output_filename}")
    except Exception as e:
        print(f"An error occurred: {e}")


# Example usage
main_directory_path = 'X:\\Documents\\Python Projects\\ScriptsEditor\\src'
output_filename = 'exported_mvc_scripts.txt'

#  TODO!: export to only one file like models : ```{models_content}``` views: ```{views_content}``` controllers: ```{controllers_content}```
export_all_python_scripts_to_txt_from_mvc_project(main_directory_path, output_filename)
