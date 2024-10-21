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


def process_pdf_to_text(pdf_path):
    # Use a PDF processing library like PyPDF2 or pdfminer to extract text
    # This is a placeholder implementation
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text