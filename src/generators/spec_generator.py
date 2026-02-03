import json
from pathlib import Path
from src.models.ai_assistant import AIAssistant
from jinja2 import Environment, FileSystemLoader
from src.utils.tool_detector import detect_available_tools
from src.prompts.templates import get_spec_system_prompt

class SpecGenerator:
    def __init__(self, templates_dir: Path = Path("src/templates")):
        self.ai = AIAssistant()
        self.env = Environment(loader=FileSystemLoader(str(templates_dir)))

    def generate(self, prompt: str) -> str:
        """
        Generate a detailed SPEC.md content from a single sentence prompt.
        """
        tools = detect_available_tools()
        system_prompt = get_spec_system_prompt(tools)

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
