import os

def export_python_scripts_to_txt(directory, output_filename):
    if not os.path.isdir(directory):
        print(f'The directory {directory} does not exist.')
        return
    try:
        with open(output_filename, 'w', encoding='utf-8') as output_file:
            for filename in os.listdir(directory):
                if filename.endswith('.py'):
                    filepath = os.path.join(directory, filename)
                    with open(filepath, 'r', encoding='utf-8') as file:
                        content = file.read()
                        output_file.write(f'{filename}:\n\n\n')
            print(f'Exported Python scripts to {output_filename}')
    except Exception as e:
        print(f'An error occurred: {e}')
main_directory_path = 'X:\\Documents\\Python Projects\\ScriptsEditor\\src'
models = main_directory_path + '\\models'
models_output_file = 'exported_models.txt'
views = main_directory_path + '\\views'
views_output_file = 'exported_views.txt'
controllers = main_directory_path + '\\controllers'
controllers_output_file = 'exported_controllers.txt'

def export_all_python_scripts_to_txt_from_mvc_project(main_directory_path, output_filename):
    sections = {'models': os.path.join(main_directory_path, 'models'), 'views': os.path.join(main_directory_path, 'views'), 'controllers': os.path.join(main_directory_path, 'controllers')}
    if not os.path.isdir(main_directory_path):
        print(f'The main directory {main_directory_path} does not exist.')
        return
    try:
        with open(output_filename, 'w', encoding='utf-8') as output_file:
            for section_name, directory in sections.items():
                output_file.write(f'{section_name}:\n```\n')
                if not os.path.isdir(directory):
                    output_file.write(f'The directory for {section_name} does not exist.\n')
                    continue
                for filename in os.listdir(directory):
                    if filename.endswith('.py'):
                        filepath = os.path.join(directory, filename)
                        with open(filepath, 'r', encoding='utf-8') as file:
                            content = file.read()
                            output_file.write(f'{filename}:\n{content}\n\n')
                output_file.write('```\n\n')
            print(f'Exported all Python scripts to {output_filename}')
    except Exception as e:
        print(f'An error occurred: {e}')
main_directory_path = 'X:\\Documents\\Python Projects\\ScriptsEditor\\src'
output_filename = 'exported_mvc_scripts.txt'
export_all_python_scripts_to_txt_from_mvc_project(main_directory_path, output_filename)