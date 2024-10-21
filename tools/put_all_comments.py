import os
import ast
import re
from typing import List


def read_file_with_fallback_encoding(file_path: str) -> str:
    """
    Attempt to read a file with UTF-8 encoding, falling back to other encodings if necessary.

    Args:
    file_path (str): The path to the file to be read.

    Returns:
    str: The content of the file.

    Raises:
    ValueError: If the file cannot be decoded with any of the attempted encodings.
    """
    encodings = ['utf-8', 'latin-1', 'ascii', 'cp1252']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                return file.read()
        except UnicodeDecodeError:
            continue
    raise ValueError(f'Unable to decode the file {file_path} with any of the attempted encodings.')


def remove_inline_comments(file_content: str) -> str:
    """
    Remove inline comments from Python file content but preserve code on the same line.

    Args:
    file_content (str): The content of the Python file.

    Returns:
    str: The modified content with comments removed, preserving code.
    """
    # Use regular expression to remove inline comments
    pattern = re.compile(r'(?<!")#.*$', re.MULTILINE)  # Only remove comments that are not inside strings
    return re.sub(pattern, '', file_content)


def remove_docstrings(tree: ast.AST) -> ast.AST:
    """
    Remove all docstrings from an AST.

    Args:
    tree (ast.AST): The AST of the parsed Python code.

    Returns:
    ast.AST: The modified AST with docstrings removed.
    """
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            if ast.get_docstring(node) is not None:
                # Remove the docstring by removing the first statement (which is the docstring)
                node.body = [n for n in node.body if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Str))]
    return tree


def remove_comments_and_docstrings(file_content: str) -> str:
    """
    Remove all comments and docstrings from Python file content.

    Args:
    file_content (str): The content of the Python file.

    Returns:
    str: The modified content with docstrings and comments removed.
    """
    # Step 1: Remove inline comments while preserving code
    file_content_no_comments = remove_inline_comments(file_content)

    # Step 2: Parse the AST to remove docstrings
    try:
        tree = ast.parse(file_content_no_comments)
        tree = remove_docstrings(tree)
        modified_content = ast.unparse(tree)
    except SyntaxError:
        return file_content_no_comments  # Return the content as-is if it can't be parsed

    return modified_content


def remove_comments_from_file(file_path: str) -> None:
    """
    Remove all comments and docstrings from a Python file.

    Args:
    file_path (str): The path to the Python file to be processed.

    Returns:
    None
    """
    try:
        file_content = read_file_with_fallback_encoding(file_path)
        modified_content = remove_comments_and_docstrings(file_content)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
    except (ValueError, SyntaxError) as e:
        print(f'Error processing file {file_path}: {str(e)}')


def process_project(project_root: str, exclude_paths: List[str]) -> None:
    """
    Process all Python files in the project, removing comments and docstrings.

    Args:
    project_root (str): The root directory of the project.
    exclude_paths (List[str]): List of paths to exclude from processing.

    Returns:
    None
    """
    for root, _, files in os.walk(project_root):
        if any(exclude in root for exclude in exclude_paths):
            continue
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                print(f'Processing file: {file_path}')
                remove_comments_from_file(file_path)


def main():
    """
    Main function to run the script.

    Args:
    None

    Returns:
    None
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    exclude_paths = ['ai_docs', 'docs', 'icons', 'images', 'vectorstore',
                     'python_dependencies', 'venv']
    process_project(project_root, exclude_paths)
    print('Comment removal process completed.')


if __name__ == '__main__':
    main()
