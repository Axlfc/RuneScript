import os
import ast
import sys
import time
from typing import List
import astor
import black
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
from src.controllers.parameters import read_config_parameter
from src.models.ai_assistant import initialize_client

def read_file_with_fallback_encoding(file_path: str) -> str:
    encodings = ['utf-8', 'latin-1', 'ascii', 'cp1252']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                return file.read()
        except UnicodeDecodeError:
            continue
    raise ValueError(f'Unable to decode the file {file_path} with any of the attempted encodings.')

def process_chat_completions(client, history):
    try:
        response = client.chat.completions.create(model='local-model', messages=history, temperature=0.7, stream=True, max_tokens=150)
        assistant_response = ''
        for chunk in response:
            if chunk.choices[0].delta.content:
                assistant_response += chunk.choices[0].delta.content
                time.sleep(0.05)
        return assistant_response.strip()
    except Exception as e:
        print(f'Error during AI completion: {e}')
        raise

def ai_supervise_docstring(client, source_code: str, docstring: str) -> str:
    prompt = f
    try:
        history = [{'role': 'system', 'content': 'You are an expert Python developer and code reviewer.'}, {'role': 'user', 'content': prompt}]
        return process_chat_completions(client, history)
    except Exception as e:
        print(f'AI supervision failed: {e}')
        return docstring

def format_docstring(docstring: str, indent: int=4) -> str:
    indent_space = ' ' * indent
    formatted_docstring = f''
    return formatted_docstring

def create_docstring_node(docstring: str):
    if sys.version_info >= (3, 8):
        return ast.Expr(value=ast.Constant(value=docstring))
    else:
        return ast.Expr(value=ast.Str(s=docstring))

def process_node(node, source_lines, client):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        existing_docstring = ast.get_docstring(node, clean=False)
        start_line = node.lineno - 1
        end_line = node.end_lineno
        source_code = '\n'.join(source_lines[start_line:end_line])
        if existing_docstring:
            if not existing_docstring.startswith(''):
                formatted_docstring = format_docstring(existing_docstring)
                docstring_node = create_docstring_node(formatted_docstring)
                node.body[0] = docstring_node
                return True
        else:
            improved_docstring = ai_supervise_docstring(client, source_code, '')
            if improved_docstring:
                formatted_docstring = format_docstring(improved_docstring)
                docstring_node = create_docstring_node(formatted_docstring)
                node.body.insert(0, docstring_node)
                return True
        for child_node in node.body:
            if isinstance(child_node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                process_node(child_node, source_lines, client)
    return False

def add_comments_to_file(file_path: str, client) -> None:
    try:
        file_content = read_file_with_fallback_encoding(file_path)
        tree = ast.parse(file_content)
        source_lines = file_content.splitlines()
    except (ValueError, SyntaxError) as e:
        print(f'Error parsing file {file_path}: {str(e)}')
        return
    modified = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            node_modified = process_node(node, source_lines, client)
            if node_modified:
                modified = True
    if modified:
        try:
            modified_content = astor.to_source(tree)
        except Exception as e:
            print(f'Error unparsing AST for {file_path}: {e}')
            return
        modified_content = black.format_str(modified_content, mode=black.FileMode(line_length=88))
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        print(f'Updated docstrings in file: {file_path}')
    else:
        print(f'No changes needed for file: {file_path}')

def process_project(project_root: str, exclude_paths: List[str], client) -> None:
    exclude_paths = [os.path.abspath(os.path.join(project_root, path)) for path in exclude_paths]
    for root, _, files in os.walk(project_root):
        root_abs = os.path.abspath(root)
        if any((os.path.commonpath([root_abs, exclude]) == exclude for exclude in exclude_paths)):
            continue
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                print(f'Processing file: {file_path}')
                add_comments_to_file(file_path, client)

def main():
    client = initialize_client()
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    exclude_paths = ['ai_docs', 'docs', 'icons', 'images', 'vectorstore', 'python_dependencies', 'venv']
    process_project(project_root, exclude_paths, client)
    print('Docstring supervision process completed.')
if __name__ == '__main__':
    main()