import os
import ast
from typing import List, Union
import black

def read_file_with_fallback_encoding(file_path: str) -> str:
    encodings = ['utf-8', 'latin-1', 'ascii', 'cp1252']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                return file.read()
        except UnicodeDecodeError:
            continue
    raise ValueError(f'Unable to decode the file {file_path} with any of the attempted encodings.')

def generate_comment(node: Union[ast.FunctionDef, ast.ClassDef]) -> str:
    base_indent = ' ' * 4
    docstring_indent = base_indent
    content_indent = base_indent + ' ' * 4
    docstring_lines = []
    docstring_lines.append('')
    if isinstance(node, ast.FunctionDef):
        docstring_lines.append(f'{docstring_indent}{node.name}')
        docstring_lines.append('')
        docstring_lines.append(f'{docstring_indent}Args:')
        args = [arg.arg for arg in node.args.args]
        if args:
            for arg in args:
                docstring_lines.append(f'{content_indent}{arg} (Any): Description of {arg}.')
        else:
            docstring_lines.append(f'{content_indent}None')
        docstring_lines.append('')
        docstring_lines.append(f'{docstring_indent}Returns:')
        returns = 'None' if node.returns is None else 'Any'
        docstring_lines.append(f'{content_indent}{returns}: Description of return value.')
    elif isinstance(node, ast.ClassDef):
        docstring_lines.append(f'{docstring_indent}{node.name}')
        docstring_lines.append('')
        docstring_lines.append(f'{docstring_indent}Description of the class.')
    docstring_lines.append('')
    docstring = '\n'.join(docstring_lines)
    return docstring

def add_comments_to_file(file_path: str) -> None:
    try:
        file_content = read_file_with_fallback_encoding(file_path)
        tree = ast.parse(file_content)
    except (ValueError, SyntaxError) as e:
        print(f'Error parsing file {file_path}: {str(e)}')
        return
    modified = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and (not ast.get_docstring(node)):
            comment = generate_comment(node)
            docstring_node = ast.Expr(value=ast.Constant(value=comment))
            node.body.insert(0, docstring_node)
            modified = True
    if modified:
        try:
            modified_content = ast.unparse(tree)
        except AttributeError:
            print('ast.unparse is not available. Please use Python 3.9 or newer.')
            return
        modified_content = black.format_str(modified_content, mode=black.FileMode(line_length=88))
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
    else:
        print(f'No changes needed for file: {file_path}')

def process_project(project_root: str, exclude_paths: List[str]) -> None:
    for root, _, files in os.walk(project_root):
        if any((exclude in root for exclude in exclude_paths)):
            continue
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                print(f'Processing file: {file_path}')
                add_comments_to_file(file_path)

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    exclude_paths = ['ai_docs', 'docs', 'icons', 'images', 'vectorstore', 'python_dependencies', 'venv']
    process_project(project_root, exclude_paths)
    print('Comment addition process completed.')
if __name__ == '__main__':
    main()