from tkinter import Menu
from src.controllers.script_tasks import render_markdown_to_html, generate_html_from_markdown, render_markdown_to_latex, run_javascript_analysis, analyze_generic_text_data, render_latex_to_pdf, generate_latex_pdf, change_interpreter, run_python_script, analyze_csv_data
from src.views.tk_utils import local_python_var

def create_submenu(parent_menu, title, entries):
    submenu = Menu(parent_menu, tearoff=0)
    parent_menu.add_cascade(label=title, menu=submenu)
    for label, command in entries.items():
        submenu.add_command(label=label, command=command)

def create_csv_menu(parent_menu):
    entries = {'Analyze Data': analyze_csv_data}
    create_submenu(parent_menu, 'CSV', entries)

def create_bash_menu(parent_menu):
    parent_menu.add_command(label='Analyze Data')

def create_powershell_menu(parent_menu):
    parent_menu.add_command(label='Analyze Data')

def create_markdown_menu(parent_menu):
    entries = {'Render HTML': render_markdown_to_html, 'Generate HTML': generate_html_from_markdown, 'Render LaTeX PDF': render_markdown_to_latex}
    create_submenu(parent_menu, 'Markdown', entries)

def create_javascript_menu(parent_menu):
    entries = {'Analyze Data': run_javascript_analysis}
    create_submenu(parent_menu, 'JavaScript', entries)

def create_html_menu(parent_menu):
    parent_menu.add_command(label='Analyze Data')

def create_css_menu(parent_menu):
    parent_menu.add_command(label='Analyze Data')

def create_java_menu(parent_menu):
    parent_menu.add_command(label='Analyze Data')

def create_cpp_menu(parent_menu):
    parent_menu.add_command(label='Analyze Data')

def create_generic_text_menu(parent_menu):
    entries = {'Analyze Data': analyze_generic_text_data}
    create_submenu(parent_menu, 'Text', entries)

def create_latex_menu(parent_menu):
    entries = {'Render PDF': render_latex_to_pdf, 'Generate PDF': generate_latex_pdf}
    create_submenu(parent_menu, 'LaTeX', entries)

def create_python_menu(parent_menu):
    entries = {'Create Virtual Environment': change_interpreter, 'Manage pip packages': change_interpreter, 'Change Interpreter': change_interpreter}
    parent_menu.add_checkbutton(label='ScriptsEditor Local Python 3', variable=local_python_var, command=run_python_script)
    create_submenu(parent_menu, 'Interpreter', entries)