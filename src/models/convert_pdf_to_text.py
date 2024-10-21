import PyPDF2
import sys
import os

def convert_pdf_to_text(file_path):
    text = ''
    if file_path:
        try:
            with open(file_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                num_pages = len(pdf_reader.pages)
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()
        except Exception as e:
            return f'Error: {e}'
    return text

def save_text_to_file(text, output_path):
    with open(output_path, 'a', encoding='utf-8') as file:
        file.write(text + '\n')
    print(f'Text saved to {output_path}')

def main():
    if len(sys.argv) < 2:
        print('Please provide the PDF file path as an argument.')
        sys.exit(1)
    file_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else '../../data/vault.txt'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    text = convert_pdf_to_text(file_path)
    save_text_to_file(text, output_path)
if __name__ == '__main__':
    main()