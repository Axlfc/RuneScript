import os
import ast
import lorem

def get_function_code(source, func_node):
    
    lines = source.splitlines()
    return "\n".join(lines[func_node.lineno - 1:func_node.end_lineno])

def create_rst_file(module_path, output_dir, relative_path):
    module_name = os.path.splitext(os.path.basename(module_path))[0]
    package_path = os.path.dirname(relative_path).replace(os.sep, '.')
    full_name = f"{package_path}.{module_name}" if package_path else module_name

    with open(module_path, 'r', encoding='utf-8') as file:
        source = file.read()
        node = ast.parse(source)

    functions = [n for n in node.body if isinstance(n, ast.FunctionDef)]
    classes = [n for n in node.body if isinstance(n, ast.ClassDef)]

    rst_content = f"{full_name}\n{'=' * len(full_name)}\n\n"
    rst_content += f".. automodule:: {full_name}\n   :members:\n   :undoc-members:\n   :show-inheritance:\n\n"

    if functions:
        rst_content += "Functions\n---------\n\n"
        for func_node in functions:
            func_name = func_node.name
            func_code = get_function_code(source, func_node)

            rst_content += f".. autofunction:: {full_name}.{func_name}\n\n"
            rst_content += f"**Description:**\n\n{lorem.paragraph()}\n\n"
            rst_content += f".. code-block:: python\n   :linenos:\n\n"
            rst_content += "   " + func_code.replace("\n", "\n   ") + "\n\n"

    if classes:
        rst_content += "Classes\n-------\n\n"
        for cls_node in classes:
            cls_name = cls_node.name

            rst_content += f".. autoclass:: {full_name}.{cls_name}\n   :members:\n   :undoc-members:\n   :show-inheritance:\n\n"
            rst_content += f"**Description:**\n\n{lorem.paragraph()}\n\n"

            methods = [n for n in cls_node.body if isinstance(n, ast.FunctionDef)]
            if methods:
                rst_content += "   Methods:\n\n"
                for method_node in methods:
                    method_name = method_node.name
                    method_code = get_function_code(source, method_node)

                    rst_content += f"   .. automethod:: {cls_name}.{method_name}\n\n"
                    rst_content += f"   **Description:**\n\n   {lorem.paragraph()}\n\n"
                    rst_content += f"   .. code-block:: python\n      :linenos:\n\n"
                    rst_content += "      " + method_code.replace("\n", "\n      ") + "\n\n"

    os.makedirs(os.path.dirname(os.path.join(output_dir, relative_path)), exist_ok=True)
    with open(os.path.join(output_dir, f"{relative_path}.rst"), 'w', encoding='utf-8') as f:
        f.write(rst_content)

def create_package_rst(package_path, output_dir, relative_path):
    package_name = os.path.basename(package_path)
    full_package_name = relative_path.replace(os.sep, '.')
    rst_content = f"{full_package_name}\n{'=' * len(full_package_name)}\n\n"
    rst_content += f".. automodule:: {full_package_name}\n   :members:\n   :undoc-members:\n   :show-inheritance:\n\n"
    rst_content += ".. toctree::\n   :maxdepth: 1\n\n"

    for item in sorted(os.listdir(package_path)):
        item_path = os.path.join(package_path, item)
        if os.path.isfile(item_path) and item.endswith('.py') and item != '__init__.py':
            module_name = os.path.splitext(item)[0]
            rst_content += f"   {module_name}\n"
        elif os.path.isdir(item_path) and not item.startswith('__'):
            subpackage_name = item
            rst_content += f"   {subpackage_name}/index\n"

    os.makedirs(os.path.dirname(os.path.join(output_dir, relative_path)), exist_ok=True)
    with open(os.path.join(output_dir, f"{relative_path}.rst"), 'w', encoding='utf-8') as f:
        f.write(rst_content)

def process_directory(directory, output_dir, base_dir):
    for root, dirs, files in os.walk(directory):
        relative_path = os.path.relpath(root, base_dir)
        if '__init__.py' in files:
            create_package_rst(root, output_dir, relative_path)

        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                file_path = os.path.join(root, file)
                file_relative_path = os.path.relpath(file_path, base_dir)
                create_rst_file(file_path, output_dir, os.path.splitext(file_relative_path)[0])

        dirs[:] = [d for d in dirs if not d.startswith('__')]

def create_index_rst(project_name, output_dir):
    index_content = f
    with open(os.path.join(output_dir, 'index.rst'), 'w', encoding='utf-8') as f:
        f.write(index_content)

def create_project_overview(project_name, output_dir):
    overview_content = f
    with open(os.path.join(output_dir, 'project_overview.rst'), 'w', encoding='utf-8') as f:
        f.write(overview_content)

def create_contributing_guide(output_dir):
    contributing_content = 
    with open(os.path.join(output_dir, 'contributing.rst'), 'w', encoding='utf-8') as f:
        f.write(contributing_content)

def create_license_file(output_dir):
    license_content = 
    with open(os.path.join(output_dir, 'license.rst'), 'w', encoding='utf-8') as f:
        f.write(license_content)

def create_conf_py(project_name, output_dir):
    conf_content = f
    with open(os.path.join(output_dir, 'conf.py'), 'w', encoding='utf-8') as f:
        f.write(conf_content)

def setup_sphinx_project(project_name, project_root, output_dir):
    
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, '_static'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, '_templates'), exist_ok=True)

    
    create_index_rst(project_name, output_dir)

    
    create_project_overview(project_name, output_dir)

    
    create_contributing_guide(output_dir)

    
    create_license_file(output_dir)

    
    create_conf_py(project_name, output_dir)

    
    for dir_name in ["data", "icons", "images", "lib", "src", "test", "tools"]:
        dir_path = os.path.join(project_root, dir_name)
        if os.path.exists(dir_path):
            process_directory(dir_path, output_dir, project_root)

    print(f"Sphinx project has been set up in the '{output_dir}' directory.")

if __name__ == "__main__":
    project_name = "ScriptsEditor"  
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_root, "docs")

    setup_sphinx_project(project_name, project_root, output_dir)