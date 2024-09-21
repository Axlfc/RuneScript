import PyPDF2
import sys
import os


def convert_pdf_to_text(file_path):
    """
    Convert a PDF file to text and return the extracted content.

    Args:
        file_path (str): The path to the PDF file.

    Returns:
        str: The extracted text from the PDF.
    """
    text = ""
    if file_path:
        try:
            with open(file_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                num_pages = len(pdf_reader.pages)
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()
        except Exception as e:
            return f"Error: {e}"
    return text


def save_text_to_file(text, output_path):
    """
    Save the extracted text to a file.

    Args:
        text (str): The text to save.
        output_path (str): The path where the text will be saved.
    """
    with open(output_path, "a", encoding="utf-8") as file:
        file.write(text + "\n")
    print(f"Text saved to {output_path}")


def main():
    """
    Main function for handling command-line input.
    Expects a file path as an argument and an optional output path.
    """
    if len(sys.argv) < 2:
        print("Please provide the PDF file path as an argument.")
        sys.exit(1)

    # Get the PDF file path
    file_path = sys.argv[1]

    # Get the optional output path, or default to "vault.txt"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "../../data/vault.txt"

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Convert PDF to text
    text = convert_pdf_to_text(file_path)

    # Save the text to the specified output file
    save_text_to_file(text, output_path)


# Allow the script to be used both as a module and as a standalone script
if __name__ == '__main__':
    main()
