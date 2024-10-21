import os
import ast
import csv
import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import fnmatch


def read_file_with_fallback_encoding(file_path: str) -> str:
    
    encodings = ["utf-8", "latin-1", "ascii", "cp1252"]
    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as file:
                return file.read()
        except UnicodeDecodeError:
            continue
    raise ValueError(
        f"Unable to decode the file {file_path} with any of the attempted encodings."
    )


def analyze_code(file_path: str) -> Dict[str, Any]:
    
    try:
        file_content = read_file_with_fallback_encoding(file_path)
        tree = ast.parse(file_content)
    except (ValueError, SyntaxError) as e:
        return {
            "imports": [],
            "functions": [],
            "classes": [],
            "potential_issues": [f"Error parsing file: {str(e)}"],
        }
    analysis = {"imports": [], "functions": [], "classes": [], "potential_issues": []}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            analysis["imports"].extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            analysis["imports"].append(f"{node.module}.{node.names[0].name}")
        elif isinstance(node, ast.FunctionDef):
            analysis["functions"].append(node.name)
        elif isinstance(node, ast.ClassDef):
            analysis["classes"].append(node.name)
    if len(analysis["functions"]) > 10:
        analysis["potential_issues"].append(
            "High number of functions, consider refactoring"
        )
    if not analysis["classes"]:
        analysis["potential_issues"].append(
            "No classes found, consider object-oriented design"
        )
    return analysis


def generate_mock_doc(
    analysis: Dict[str, Any], file_path: str, existing_doc: str
) -> str:
    
    file_name = os.path.basename(file_path)
    mock_doc = (
        f"AI-Enhanced Documentation for {file_name}\n{'=' * (len(file_name) + 28)}\n\n"
    )
    mock_doc += "Existing Documentation\n----------------------\n"
    mock_doc += existing_doc + "\n\n"
    mock_doc += "AI-Generated Insights\n---------------------\n"
    mock_doc += "Imports\n-------\n"
    for imp in analysis["imports"]:
        mock_doc += f"* {imp}\n"
    mock_doc += "\nFunctions\n---------\n"
    for func in analysis["functions"]:
        mock_doc += f"* {func}\n"
    mock_doc += "\nClasses\n-------\n"
    for cls in analysis["classes"]:
        mock_doc += f"* {cls}\n"
    mock_doc += "\nPotential Improvements\n----------------------\n"
    for issue in analysis["potential_issues"]:
        mock_doc += f".. warning:: {issue}\n"
    mock_doc += "\nAI-Assisted Suggestions\n------------------------\n"
    mock_doc += "1. Consider using type hints for better code readability and maintainability.\n"
    mock_doc += (
        "2. Implement unit tests for each function to ensure code reliability.\n"
    )
    mock_doc += "3. Use AI-powered code completion tools to speed up development.\n"
    mock_doc += 
    mock_doc += "5. Consider adding more examples and use cases in the documentation.\n"
    mock_doc += (
        "6. Implement consistent error handling and logging throughout the codebase.\n"
    )
    mock_doc += 
    mock_doc += 
    mock_doc += 
    mock_doc += 
    mock_doc += 
    return mock_doc


def analyze_project(
    project_root: str, exclude_paths: List[str]
) -> List[Dict[str, Any]]:
    
    project_analysis = []
    for root, _, files in os.walk(project_root):
        if any(exclude in root for exclude in exclude_paths):
            continue
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                analysis = analyze_code(file_path)
                project_analysis.append({"file_path": file_path, "analysis": analysis})
    return project_analysis


def generate_suggestions_csv(project_analysis: List[Dict[str, Any]], output_file: str):
    
    with open(output_file, "w", newline="") as csvfile:
        fieldnames = ["File", "Suggestion"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for file_analysis in project_analysis:
            file_path = file_analysis["file_path"]
            for issue in file_analysis["analysis"]["potential_issues"]:
                writer.writerow({"File": file_path, "Suggestion": issue})


def read_existing_documentation(build_dir: str, file_name: str) -> str:
    
    html_file = os.path.join(build_dir, file_name)
    try:
        with open(html_file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
            content = soup.find("div", class_="body")
            return content.get_text() if content else ""
    except FileNotFoundError:
        return "No existing documentation found."
    except Exception as e:
        return f"Error reading existing documentation: {str(e)}"


def read_gitignore(project_root: str) -> List[str]:
    
    gitignore_path = os.path.join(project_root, ".gitignore")
    if not os.path.exists(gitignore_path):
        return []
    with open(gitignore_path, "r") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("


def is_excluded(file_path: str, exclude_patterns: List[str]) -> bool:
    
    relative_path = os.path.normpath(file_path)
    for pattern in exclude_patterns:
        if pattern.endswith("/"):
            if fnmatch.fnmatch(relative_path + "/", pattern) or fnmatch.fnmatch(
                os.path.dirname(relative_path) + "/", pattern
            ):
                return True
        elif fnmatch.fnmatch(relative_path, pattern):
            return True
    return False


def main():
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_root, "ai_docs")
    build_dir = os.path.join(project_root, "build")
    os.makedirs(output_dir, exist_ok=True)
    exclude_paths = [
        "ai_docs",
        "docs",
        "icons",
        "images",
        "vectorstore",
        "python_dependencies",
        "venv",
    ]
    gitignore_patterns = read_gitignore(project_root)
    project_analysis = analyze_project(project_root, exclude_paths)
    for file_analysis in project_analysis:
        file_path = file_analysis["file_path"]
        if is_excluded(file_path, gitignore_patterns):
            continue
    analysis = file_analysis["analysis"]
    relative_path = os.path.relpath(file_path, project_root)
    existing_doc = read_existing_documentation(
        build_dir, relative_path.replace(".py", ".html")
    )
    mock_doc = generate_mock_doc(analysis, file_path, existing_doc)
    output_file = os.path.join(output_dir, f"{relative_path}.rst")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(mock_doc)
    except Exception as e:
        print(f"Error writing file {output_file}: {str(e)}")
    generate_suggestions_csv(
        project_analysis, os.path.join(output_dir, "suggestions.csv")
    )
    print(
        f"AI-enhanced documentation and analysis completed. Output saved in '{output_dir}'."
    )
    conf_path = os.path.join(project_root, "docs", "conf.py")
    with open(conf_path, "a", encoding="utf-8") as f:
        f.write("\n\n
        f.write("html_theme = 'sphinx_rtd_theme'\n")
        f.write("extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon']\n")
        f.write("autodoc_member_order = 'bysource'\n")
        f.write("autodoc_typehints = 'description'\n")


if __name__ == "__main__":
    main()
