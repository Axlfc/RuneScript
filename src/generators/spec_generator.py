import json
from pathlib import Path
from src.models.ai_assistant import AIAssistant
from jinja2 import Environment, FileSystemLoader
from src.utils.tool_detector import detect_available_tools

class SpecGenerator:
    def __init__(self, templates_dir: Path = Path("src/templates")):
        self.ai = AIAssistant()
        self.env = Environment(loader=FileSystemLoader(str(templates_dir)))

    def generate(self, prompt: str) -> str:
        """
        Generate a detailed SPEC.md content from a single sentence prompt.
        """
        tools = detect_available_tools()

        system_prompt = f"""
        You are an expert system architect.
        Given a project idea, generate a structured project specification in JSON format.
        Include: project_name, objective, features (list), language, framework, database, testing_framework, success_criteria (list), out_of_scope (list).

        System Context:
        - Python is available: {tools['python']} (at {tools['python_path']})
        - Node.js is available: {tools['node']}
        - npm is available: {tools['npm']}

        Guidelines for Tech Stack Selection:
        1. If it is a frontend project (HTML/CSS/JS) and Node.js is NOT available, use 'Python scripts (BeautifulSoup, lxml)' for testing_framework and 'HTML/CSS/JavaScript' for language.
        2. If it is a Python project, use 'pytest' for testing_framework.
        3. If it is a Node.js project and npm is available, use 'jest' or 'mocha'.
        4. Always prefer tools that are marked as available in the System Context.
        """

        user_input = f"Project Idea: {prompt}"

        response = self.ai.generate(f"{system_prompt}\n\n{user_input}")

        # Try to parse JSON from AI response
        try:
            # Simple extraction in case AI adds text around JSON
            start = response.find('{')
            end = response.rfind('}') + 1
            data = json.loads(response[start:end])
        except Exception:
            # Fallback if parsing fails
            data = {
                "project_name": "New Project",
                "objective": prompt,
                "features": ["Feature 1"],
                "language": "Python",
                "framework": "None",
                "database": "None",
                "testing_framework": "pytest",
                "success_criteria": ["Works as expected"],
                "out_of_scope": ["Everything else"]
            }

        template = self.env.get_template("SPEC.md.jinja2")
        return template.render(**data)
