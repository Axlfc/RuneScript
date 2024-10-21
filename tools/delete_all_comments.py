import os
import ast
import re
from typing import List


def read_file_with_fallback_encoding(file_path: str) -> str:
    
    encodings = ['utf-8', 'latin-1', 'ascii', 'cp1252']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                return file.read()
        except UnicodeDecodeError:
            continue
    raise ValueError(f'Unable to decode the file {file_path} with any of the attempted encodings.')


def remove_docstrings_and_comments(file_content: str) -> str:
    
    
    file_content_no_comments = re.sub(r'
    file_content_no_comments = re.sub(r'', '', file_content_no_comments, flags=re.DOTALL)
    file_content_no_comments = re.sub(r"", '', file_content_no_comments, flags=re.DOTALL)

    
    try:
        tree = ast.parse(file_content_no_comments)
    except SyntaxError:
        return file_content_no_comments  

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            if ast.get_docstring(node) is not None:
                node.body = [n for n in node.body if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Str))]

    return ast.unparse(tree)


def remove_comments_from_file(file_path: str) -> None:
    
    try:
        file_content = read_file_with_fallback_encoding(file_path)
        modified_content = remove_docstrings_and_comments(file_content)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
    except (ValueError, SyntaxError) as e:
        print(f'Error processing file {file_path}: {str(e)}')


def process_project(project_root: str, exclude_paths: List[str]) -> None:
    
    for root, _, files in os.walk(project_root):
        if any(exclude in root for exclude in exclude_paths):
            continue
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                print(f'Processing file: {file_path}')
                remove_comments_from_file(file_path)


def main():
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    exclude_paths = ['ai_docs', 'docs', 'icons', 'images', 'vectorstore',
                     'python_dependencies', 'venv']
    process_project(project_root, exclude_paths)
    print('Comment removal process completed.')


if __name__ == '__main__':
    main()
