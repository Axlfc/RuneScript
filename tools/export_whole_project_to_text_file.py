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
directory_path = 'X:\\Documents\\Python Projects\\ScriptsEditor'
output_file = 'exported_scripts.txt'
export_python_scripts_to_txt(directory_path, output_file)
