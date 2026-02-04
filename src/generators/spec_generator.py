import json
import logging
from pathlib import Path
from src.models.ai_assistant import AIAssistant
from jinja2 import Environment, FileSystemLoader
from src.utils.tool_detector import detect_available_tools
from src.prompts.templates import get_spec_system_prompt
from src.core.robust_parser import RobustJSONParser

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

        # Usar parser robusto
        parser = RobustJSONParser()
        try:
            spec_schema = parser.parse_spec(response)
            data = spec_schema.model_dump()
        except ValueError as e:
            logging.error(f"JSON extraction failed: {e}. Using fallback.")
            data = self._fallback_spec_from_prompt(prompt)
        except Exception as e:
            logging.error(f"Spec validation failed: {e}. Using fallback.")
            data = self._fallback_spec_from_prompt(prompt)

        template = self.env.get_template("SPEC.md.jinja2")
        return template.render(**data)

    def _fallback_spec_from_prompt(self, prompt: str) -> dict:
        """Genera spec básico desde prompt cuando parsing falla."""
        return {
            "project_name": "New Project",
            "objective": prompt,
            "features": ["Core functionality based on prompt"],
            "language": "Python",
            "framework": "None",
            "database": "None",
            "testing_framework": "pytest",
            "success_criteria": ["Project meets the basic objective"],
            "out_of_scope": ["External integrations", "Advanced UI"]
        }
