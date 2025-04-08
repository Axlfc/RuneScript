import os
import sys
import argparse
import glob

def convert_to_txt(input_file_path, output_file_path):
    """
    Converts the content of the input file to a text file.

    Args:
        input_file_path (str): Path to the input file.
        output_file_path (str): Path to the output .txt file.
    """
    try:
        with open(input_file_path, 'r', encoding='utf-8') as infile:
            content = infile.read()
        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            outfile.write(content)
        print(f"Successfully converted '{input_file_path}' to '{output_file_path}'")
        return True  # Indicate successful conversion
    except FileNotFoundError:
        print(f"Error: Input file '{input_file_path}' not found.")
        return False
    except UnicodeDecodeError:
        try:
            with open(input_file_path, 'r', encoding='latin-1') as infile:
                content = infile.read()
            with open(output_file_path, 'w', encoding='utf-8') as outfile:
                outfile.write(content)
            print(f"Successfully converted '{input_file_path}' (using latin-1 encoding) to '{output_file_path}'")
            return True
        except Exception as e:
            print(f"Error decoding '{input_file_path}': {e}")
            return False
    except Exception as e:
        print(f"Error processing '{input_file_path}': {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Convert text-based files to .txt files and replace the originals.")
    parser.add_argument('input_path', type=str, help='Path to the input file or directory.')

    args = parser.parse_args()

    input_path = args.input_path

    print("WARNING: This script will REPLACE your original files with their .txt versions.")
    confirmation = input("Do you want to proceed? (yes/no): ").lower()
    if confirmation != 'yes':
        print("Operation cancelled.")
        sys.exit(0)

    if os.path.isfile(input_path):
        output_file = generate_output_filename(input_path)
        if convert_to_txt(input_path, output_file):
            os.remove(input_path)
            print(f"Original file '{input_path}' has been replaced.")
    elif os.path.isdir(input_path):
        files_to_convert = glob.glob(os.path.join(input_path, '*'))
        for input_file in files_to_convert:
            if os.path.isfile(input_file):
                output_file = generate_output_filename(input_file)
                if convert_to_txt(input_file, output_file):
                    os.remove(input_file)
                    print(f"Original file '{input_file}' has been replaced.")
    else:
        print(f"Error: '{input_path}' is not a valid file or directory.")
        sys.exit(1)

def generate_output_filename(input_file):
    file_dir = os.path.dirname(input_file)
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_filename = f"{base_name}.txt"
    return os.path.join(file_dir, output_filename)

if __name__ == '__main__':
    main()