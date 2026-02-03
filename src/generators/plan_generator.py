import json
import logging
from pathlib import Path
from src.models.ai_assistant import AIAssistant
from jinja2 import Environment, FileSystemLoader
from src.prompts.templates import get_plan_system_prompt

class PlanGenerator:
    def __init__(self, templates_dir: Path = Path("src/templates")):
        self.ai = AIAssistant()
        self.env = Environment(loader=FileSystemLoader(str(templates_dir)))

    @staticmethod
    def detect_complexity(spec: str) -> str:
        """Detect project complexity from spec."""
        spec_lower = spec.lower()
        # Count approximate features (bullet points in Features section)
        feature_count = spec_lower.count('\n- ')

        complexity_keywords = {
            'very_complex': ['microservices', 'real-time', 'admin panel', 'multi-tenant', 'enterprise'],
            'complex': ['dashboard', 'auth', 'api', 'database', 'crud', 'backend'],
            'medium': ['portfolio', 'blog', 'gallery', 'form', 'interactive']
        }

        for level, keywords in complexity_keywords.items():
            if any(kw in spec_lower for kw in keywords):
                return level

        if feature_count > 12: return 'very_complex'
        if feature_count > 7: return 'complex'
        if feature_count > 4: return 'medium'
        return 'simple'

    @staticmethod
    def validate_plan(plan_content: str, complexity: str = 'simple') -> bool:
        """
        Validate that the plan has a minimum number of tasks based on complexity.
        """
        min_tasks_map = {
            'simple': 5,
            'medium': 10,
            'complex': 15,
            'very_complex': 20
        }
        min_tasks = min_tasks_map.get(complexity, 5)

        # Count tasks matching the pattern [ ]
        task_count = plan_content.count('[ ]')

        # 1. Task count check
        if task_count < min_tasks:
            logging.warning(f"Plan validation failed: Only {task_count} tasks found, need {min_tasks} for {complexity} complexity.")
            return False

        # 2. Phase count check
        phase_count = plan_content.upper().count('## PHASE')
        if phase_count < 2:
            logging.warning(f"Plan validation failed: Only {phase_count} phases found, need at least 2.")
            return False

        # 3. Truncation check
        truncation_markers = ["...", "(remaining", "(rest of", "(to be continued)", "(etc.)"]
        for marker in truncation_markers:
            if marker in plan_content:
                logging.warning(f"Plan validation failed: Truncation marker '{marker}' found.")
                return False

        # 4. Task description length check
        task_lines = [line for line in plan_content.split('\n') if '- [ ]' in line]
        for line in task_lines:
            desc = line.replace('- [ ]', '').strip()
            if len(desc) < 20:
                logging.warning(f"Plan validation failed: Task description too short: '{desc}'")
                return False

        return True

    def generate(self, spec_content: str, tech_config: dict = None, complexity: str = 'medium') -> str:
        """
        Generate a detailed IMPLEMENTATION_PLAN.md content from SPEC.md.
        """
        tech_info_str = json.dumps(tech_config, indent=2) if tech_config else ""
        system_prompt = get_plan_system_prompt(tech_info_str, complexity=complexity)

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
