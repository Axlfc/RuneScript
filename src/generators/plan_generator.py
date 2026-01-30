import json
from pathlib import Path
from src.models.ai_assistant import AIAssistant
from jinja2 import Environment, FileSystemLoader

class PlanGenerator:
    def __init__(self, templates_dir: Path = Path("src/templates")):
        self.ai = AIAssistant()
        self.env = Environment(loader=FileSystemLoader(str(templates_dir)))

    def generate(self, spec_content: str) -> str:
        """
        Generate a detailed IMPLEMENTATION_PLAN.md content from SPEC.md.
        """
        system_prompt = """
        You are an elite developer.
        Given a project specification, generate a detailed implementation plan in JSON format.
        Break it down into PHASES. Each phase should have a list of tasks.
        Each task should be specific and follow TDD principles (Test: description).
        JSON format:
        {
            "phases": [
                {
                    "name": "Phase Name",
                    "tasks": [{"description": "Task description"}]
                }
            ],
            "total_tasks": 0,
            "completed_tasks": 0,
            "remaining_tasks": 0,
            "blocked_tasks": []
        }
        """

        response = self.ai.generate(f"{system_prompt}\n\nSPECIFICATION:\n{spec_content}")

        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            data = json.loads(response[start:end])

            # Recalculate counters
            total = 0
            for phase in data.get("phases", []):
                total += len(phase.get("tasks", []))
            data["total_tasks"] = total
            data["remaining_tasks"] = total
        except Exception:
            data = {
                "phases": [{"name": "Initial", "tasks": [{"description": "Setup project"}]}],
                "total_tasks": 1,
                "completed_tasks": 0,
                "remaining_tasks": 1,
                "blocked_tasks": []
            }

        template = self.env.get_template("IMPLEMENTATION_PLAN.md.jinja2")
        return template.render(**data)
