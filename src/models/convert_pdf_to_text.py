import PyPDF2
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
            with open(file_path, "rb") as pdf_file:
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


def process_pdf_to_text(input_pdf, output_txt):
    """
    Process the input PDF and save the extracted text to the output path.

    Args:
        input_pdf (str): Path to the PDF file to convert.
        output_txt (str): Path where the extracted text will be saved.
    """
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_txt), exist_ok=True)

    # Convert the PDF to text
    text = convert_pdf_to_text(input_pdf)

    # Save the extracted text to the specified output file
    save_text_to_file(text, output_txt)