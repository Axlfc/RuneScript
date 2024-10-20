import os
import ast
import lorem


def get_function_code(source, func_node):
    """Extracts the code of a function from the source code."""
    lines = source.splitlines()
    return "\n".join(lines[func_node.lineno - 1 : func_node.end_lineno])


def create_rst_file(module_path, output_dir, relative_path):
    """
    create_rst_file

    Args:
        module_path (Any): Description of module_path.
        output_dir (Any): Description of output_dir.
        relative_path (Any): Description of relative_path.

    Returns:
        None: Description of return value.
    """
    module_name = os.path.splitext(os.path.basename(module_path))[0]
    package_path = os.path.dirname(relative_path).replace(os.sep, ".")
    full_name = f"{package_path}.{module_name}" if package_path else module_name
    with open(module_path, "r", encoding="utf-8") as file:
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
                    rst_content += (
                        "      " + method_code.replace("\n", "\n      ") + "\n\n"
                    )
    os.makedirs(os.path.dirname(os.path.join(output_dir, relative_path)), exist_ok=True)
    with open(
        os.path.join(output_dir, f"{relative_path}.rst"), "w", encoding="utf-8"
    ) as f:
        f.write(rst_content)


def create_package_rst(package_path, output_dir, relative_path):
    """
    create_package_rst

    Args:
        package_path (Any): Description of package_path.
        output_dir (Any): Description of output_dir.
        relative_path (Any): Description of relative_path.

    Returns:
        None: Description of return value.
    """
    package_name = os.path.basename(package_path)
    full_package_name = relative_path.replace(os.sep, ".")
    rst_content = f"{full_package_name}\n{'=' * len(full_package_name)}\n\n"
    rst_content += f".. automodule:: {full_package_name}\n   :members:\n   :undoc-members:\n   :show-inheritance:\n\n"
    rst_content += ".. toctree::\n   :maxdepth: 1\n\n"
    for item in sorted(os.listdir(package_path)):
        item_path = os.path.join(package_path, item)
        if (
            os.path.isfile(item_path)
            and item.endswith(".py")
            and (item != "__init__.py")
        ):
            module_name = os.path.splitext(item)[0]
            rst_content += f"   {module_name}\n"
        elif os.path.isdir(item_path) and (not item.startswith("__")):
            subpackage_name = item
            rst_content += f"   {subpackage_name}/index\n"
    os.makedirs(os.path.dirname(os.path.join(output_dir, relative_path)), exist_ok=True)
    with open(
        os.path.join(output_dir, f"{relative_path}.rst"), "w", encoding="utf-8"
    ) as f:
        f.write(rst_content)


def process_directory(directory, output_dir, base_dir):
    """
    process_directory

    Args:
        directory (Any): Description of directory.
        output_dir (Any): Description of output_dir.
        base_dir (Any): Description of base_dir.

    Returns:
        None: Description of return value.
    """
    for root, dirs, files in os.walk(directory):
        relative_path = os.path.relpath(root, base_dir)
        if "__init__.py" in files:
            create_package_rst(root, output_dir, relative_path)
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                file_path = os.path.join(root, file)
                file_relative_path = os.path.relpath(file_path, base_dir)
                create_rst_file(
                    file_path, output_dir, os.path.splitext(file_relative_path)[0]
                )
        dirs[:] = [d for d in dirs if not d.startswith("__")]


def create_index_rst(project_name, output_dir):
    """
    create_index_rst

    Args:
        project_name (Any): Description of project_name.
        output_dir (Any): Description of output_dir.

    Returns:
        None: Description of return value.
    """
    index_content = f"\nWelcome to {project_name} Documentation\n{'=' * (len(project_name) + 25)}\n\n{project_name} is a powerful tool for managing and editing scripts, with integrated AI assistance and various utility functions.\n\nProject Structure\n-----------------\n\n.. code-block:: text\n\n    {project_name}/\n    ├── data/\n    ├── icons/\n    ├── images/\n    ├── lib/\n    ├── src/\n    │   ├── controllers/\n    │   ├── models/\n    │   └── views/\n    ├── test/\n    └── tools/\n\nContents\n--------\n\n.. toctree::\n   :maxdepth: 2\n   :caption: Project Overview\n\n   project_overview\n\n.. toctree::\n   :maxdepth: 2\n   :caption: Main Components\n\n   data/index\n   icons/index\n   images/index\n   lib/index\n   src/index\n   test/index\n   tools/index\n\n.. toctree::\n   :maxdepth: 2\n   :caption: Developer Guide\n\n   contributing\n   license\n\nIndices and Tables\n------------------\n\n* :ref:`genindex`\n* :ref:`modindex`\n"
    with open(os.path.join(output_dir, "index.rst"), "w", encoding="utf-8") as f:
        f.write(index_content)


def create_project_overview(project_name, output_dir):
    """
    create_project_overview

    Args:
        project_name (Any): Description of project_name.
        output_dir (Any): Description of output_dir.

    Returns:
        None: Description of return value.
    """
    overview_content = f"\nProject Overview\n================\n\n{project_name} is a comprehensive tool designed for efficient script management and editing. It integrates advanced AI assistance and a range of utility functions to enhance productivity and streamline workflow.\n\nKey Features\n------------\n\n1. **Script Management**: Organize and manage your scripts effectively.\n2. **AI-Assisted Editing**: Leverage AI capabilities for smarter code editing.\n3. **Utility Functions**: Access a variety of tools to aid in development.\n4. **User-Friendly Interface**: Intuitive design for ease of use.\n\nGetting Started\n---------------\n\nTo get started with {project_name}, follow these steps:\n\n1. Installation\n2. Configuration\n3. Basic Usage\n\nFor more detailed information, refer to the respective sections in this documentation.\n"
    with open(
        os.path.join(output_dir, "project_overview.rst"), "w", encoding="utf-8"
    ) as f:
        f.write(overview_content)


def create_contributing_guide(output_dir):
    """
    create_contributing_guide

    Args:
        output_dir (Any): Description of output_dir.

    Returns:
        None: Description of return value.
    """
    contributing_content = "\nContributing to ScriptsEditor\n=============================\n\nWe welcome contributions to ScriptsEditor! This document provides guidelines for contributing to the project.\n\nHow to Contribute\n-----------------\n\n1. Fork the repository\n2. Create a new branch for your feature or bugfix\n3. Make your changes\n4. Submit a pull request\n\nCoding Standards\n----------------\n\n- Follow PEP 8 guidelines\n- Write clear, commented code\n- Include unit tests for new features\n\nReporting Issues\n----------------\n\nIf you encounter any bugs or have feature requests, please open an issue on the GitHub repository.\n\nThank you for contributing to ScriptsEditor!\n"
    with open(os.path.join(output_dir, "contributing.rst"), "w", encoding="utf-8") as f:
        f.write(contributing_content)


def create_license_file(output_dir):
    """
    create_license_file

    Args:
        output_dir (Any): Description of output_dir.

    Returns:
        None: Description of return value.
    """
    license_content = "\nLicense\n=======\n\nScriptsEditor is released under the GNU General Public License, version 2.\n\nCopyright (c) 2024 Axel Fernández Curros\n\nThis program is free software; you can redistribute it and/or modify\nit under the terms of the GNU General Public License as published by\nthe Free Software Foundation; either version 2 of the License, or\n(at your option) any later version.\n\nThis program is distributed in the hope that it will be useful,\nbut WITHOUT ANY WARRANTY; without even the implied warranty of\nMERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the\nGNU General Public License for more details.\n\nYou should have received a copy of the GNU General Public License\nalong with this program; if not, write to the Free Software Foundation, Inc.,\n51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.\n"
    with open(os.path.join(output_dir, "license.rst"), "w", encoding="utf-8") as f:
        f.write(license_content)


def create_conf_py(project_name, output_dir):
    """
    create_conf_py

    Args:
        project_name (Any): Description of project_name.
        output_dir (Any): Description of output_dir.

    Returns:
        None: Description of return value.
    """
    conf_content = f"\n# Configuration file for the Sphinx documentation builder.\n\nimport os\nimport sys\nsys.path.insert(0, os.path.abspath('..'))\n\n# -- Project information -----------------------------------------------------\n\nproject = '{project_name}'\ncopyright = '2024, Your Name'\nauthor = 'Your Name'\n\n# -- General configuration ---------------------------------------------------\n\nextensions = [\n    'sphinx.ext.autodoc',\n    'sphinx.ext.napoleon',\n    'sphinx.ext.viewcode',\n    'sphinx.ext.intersphinx',\n    'sphinx_rtd_theme',\n]\n\ntemplates_path = ['_templates']\nexclude_patterns = []\n\n# -- Options for HTML output -------------------------------------------------\n\nhtml_theme = 'sphinx_rtd_theme'\nhtml_static_path = ['_static']\n\n# -- AutoDoc configuration ---------------------------------------------------\n\nautodoc_default_options = {{\n    'members': True,\n    'undoc-members': True,\n    'private-members': True,\n    'special-members': '__init__',\n    'show-inheritance': True,\n}}\n\n# -- Napoleon settings -------------------------------------------------------\n\nnapoleon_google_docstring = True\nnapoleon_numpy_docstring = True\nnapoleon_include_init_with_doc = False\nnapoleon_include_private_with_doc = False\nnapoleon_include_special_with_doc = True\nnapoleon_use_admonition_for_examples = False\nnapoleon_use_admonition_for_notes = False\nnapoleon_use_admonition_for_references = False\nnapoleon_use_ivar = False\nnapoleon_use_param = True\nnapoleon_use_rtype = True\nnapoleon_preprocess_types = False\nnapoleon_type_aliases = None\nnapoleon_attr_annotations = True\n\n# -- Intersphinx configuration -----------------------------------------------\n\nintersphinx_mapping = {{'python': ('https://docs.python.org/3', None)}}\n"
    with open(os.path.join(output_dir, "conf.py"), "w", encoding="utf-8") as f:
        f.write(conf_content)


def setup_sphinx_project(project_name, project_root, output_dir):
    """
    setup_sphinx_project

    Args:
        project_name (Any): Description of project_name.
        project_root (Any): Description of project_root.
        output_dir (Any): Description of output_dir.

    Returns:
        None: Description of return value.
    """
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "_static"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "_templates"), exist_ok=True)
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
