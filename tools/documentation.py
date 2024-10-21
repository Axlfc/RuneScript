import os
import ast
import lorem

def get_function_code(source, func_node):
    """Extracts the code of a function from the source code."""
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
    index_content = f"""
Welcome to {project_name} Documentation
{'=' * (len(project_name) + 25)}

{project_name} is a powerful tool for managing and editing scripts, with integrated AI assistance and various utility functions.

Project Structure
-----------------

.. code-block:: text

    {project_name}/
    ├── data/
    ├── icons/
    ├── images/
    ├── lib/
    ├── src/
    │   ├── controllers/
    │   ├── models/
    │   └── views/
    ├── test/
    └── tools/

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: Project Overview

   project_overview

.. toctree::
   :maxdepth: 2
   :caption: Main Components

   data/index
   icons/index
   images/index
   lib/index
   src/index
   test/index
   tools/index

.. toctree::
   :maxdepth: 2
   :caption: Developer Guide

   contributing
   license

Indices and Tables
------------------

* :ref:`genindex`
* :ref:`modindex`
"""
    with open(os.path.join(output_dir, 'index.rst'), 'w', encoding='utf-8') as f:
        f.write(index_content)

def create_project_overview(project_name, output_dir):
    overview_content = f"""
Project Overview
================

{project_name} is a comprehensive tool designed for efficient script management and editing. It integrates advanced AI assistance and a range of utility functions to enhance productivity and streamline workflow.

Key Features
------------

1. **Script Management**: Organize and manage your scripts effectively.
2. **AI-Assisted Editing**: Leverage AI capabilities for smarter code editing.
3. **Utility Functions**: Access a variety of tools to aid in development.
4. **User-Friendly Interface**: Intuitive design for ease of use.

Getting Started
---------------

To get started with {project_name}, follow these steps:

1. Installation
2. Configuration
3. Basic Usage

For more detailed information, refer to the respective sections in this documentation.
"""
    with open(os.path.join(output_dir, 'project_overview.rst'), 'w', encoding='utf-8') as f:
        f.write(overview_content)

def create_contributing_guide(output_dir):
    contributing_content = """
Contributing to ScriptsEditor
=============================

We welcome contributions to ScriptsEditor! This document provides guidelines for contributing to the project.

How to Contribute
-----------------

1. Fork the repository
2. Create a new branch for your feature or bugfix
3. Make your changes
4. Submit a pull request

Coding Standards
----------------

- Follow PEP 8 guidelines
- Write clear, commented code
- Include unit tests for new features

Reporting Issues
----------------

If you encounter any bugs or have feature requests, please open an issue on the GitHub repository.

Thank you for contributing to ScriptsEditor!
"""
    with open(os.path.join(output_dir, 'contributing.rst'), 'w', encoding='utf-8') as f:
        f.write(contributing_content)

def create_license_file(output_dir):
    license_content = """
License
=======

ScriptsEditor is released under the GNU General Public License, version 2.

Copyright (c) 2024 Axel Fernández Curros

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
"""
    with open(os.path.join(output_dir, 'license.rst'), 'w', encoding='utf-8') as f:
        f.write(license_content)

def create_conf_py(project_name, output_dir):
    conf_content = f"""
# Configuration file for the Sphinx documentation builder.

import os
import sys
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------

project = '{project_name}'
copyright = '2024, Your Name'
author = 'Your Name'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx_rtd_theme',
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# -- AutoDoc configuration ---------------------------------------------------

autodoc_default_options = {{
    'members': True,
    'undoc-members': True,
    'private-members': True,
    'special-members': '__init__',
    'show-inheritance': True,
}}

# -- Napoleon settings -------------------------------------------------------

napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# -- Intersphinx configuration -----------------------------------------------

intersphinx_mapping = {{'python': ('https://docs.python.org/3', None)}}
"""
    with open(os.path.join(output_dir, 'conf.py'), 'w', encoding='utf-8') as f:
        f.write(conf_content)

def setup_sphinx_project(project_name, project_root, output_dir):
    # Create necessary directories
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, '_static'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, '_templates'), exist_ok=True)

    # Create index.rst
    create_index_rst(project_name, output_dir)

    # Create project_overview.rst
    create_project_overview(project_name, output_dir)

    # Create contributing.rst
    create_contributing_guide(output_dir)

    # Create license.rst
    create_license_file(output_dir)

    # Create conf.py
    create_conf_py(project_name, output_dir)

    # Process project directories
    for dir_name in ["data", "icons", "images", "lib", "src", "test", "tools"]:
        dir_path = os.path.join(project_root, dir_name)
        if os.path.exists(dir_path):
            process_directory(dir_path, output_dir, project_root)

    print(f"Sphinx project has been set up in the '{output_dir}' directory.")

if __name__ == "__main__":
    project_name = "ScriptsEditor"  # Replace with your actual project name
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_root, "docs")

    setup_sphinx_project(project_name, project_root, output_dir)