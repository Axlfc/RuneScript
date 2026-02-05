import json
import logging
from pathlib import Path
from src.models.ai_assistant import AIAssistant
from jinja2 import Environment, FileSystemLoader
from src.prompts.templates import get_plan_system_prompt
from src.core.robust_parser import RobustJSONParser

class PlanGenerator:
    def __init__(self, templates_dir: Path = Path("src/templates")):
        self.ai = AIAssistant()
        self.env = Environment(loader=FileSystemLoader(str(templates_dir)))

    @staticmethod
    def detect_complexity(spec: str) -> str:
        """Detect project complexity from spec using a multi-factor scoring system."""
        spec_lower = spec.lower()
        # Count approximate features (bullet points in Features section)
        feature_count = spec_lower.count('\n- ')

        score = 0

        KEYWORD_WEIGHTS = {
            'very_complex': {
                'microservices': 10, 'real-time': 8, 'admin panel': 7, 'multi-tenant': 9,
                'rbac': 7, 'scaling': 8, 'distributed': 9, 'blockchain': 10,
                'machine learning': 10, 'ai integration': 8
            },
            'complex': {
                'dashboard': 5, 'auth': 4, 'api': 3, 'database': 4, 'crud': 4,
                'payment': 5, 'stripe': 5, 'websocket': 5, 'integration': 4,
                'concurrency': 5, 'encryption': 5
            },
            'medium': {
                'portfolio': 2, 'blog': 2, 'gallery': 2, 'form': 2, 'interactive': 2,
                'search': 2, 'filter': 2, 'animations': 2, 'responsive': 1
            }
        }

        # Factor 1: Keywords and weights
        for level, keywords in KEYWORD_WEIGHTS.items():
            for kw, weight in keywords.items():
                if kw in spec_lower:
                    score += weight

        # Factor 2: Feature count
        score += feature_count

        # Factor 3: Specification length
        if len(spec_lower) > 2000:
            score += 5
        elif len(spec_lower) > 1000:
            score += 2

        # Initial Classification
        if score >= 15: calculated_complexity = 'very_complex'
        elif score >= 8: calculated_complexity = 'complex'
        elif score >= 3: calculated_complexity = 'medium'
        else: calculated_complexity = 'simple'

        # Factor 4: Maximum complexity limits by project type
        MAX_COMPLEXITY_BY_TYPE = {
            'portfolio': 'medium',
            'landing page': 'medium',
            'blog': 'medium',
            'calculator': 'simple',
            'todo list': 'simple',
        }

        # Complexity hierarchy for comparison
        HIERARCHY = {'simple': 0, 'medium': 1, 'complex': 2, 'very_complex': 3}

        for project_type, max_allowed in MAX_COMPLEXITY_BY_TYPE.items():
            if project_type in spec_lower:
                # Special cases where high complexity is allowed even for restricted types
                if project_type == 'portfolio' and ('admin' in spec_lower or 'dashboard' in spec_lower):
                    continue

                if HIERARCHY[calculated_complexity] > HIERARCHY[max_allowed]:
                    logging.info(f"Capping complexity of {project_type} from {calculated_complexity} to {max_allowed}")
                    calculated_complexity = max_allowed
                    break

        return calculated_complexity

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
            # Remove "Test: " and "Implementation: " prefixes for length check if present
            clean_desc = line.replace('- [ ]', '').strip()
            clean_desc = clean_desc.replace('Test:', '').replace('Implementation:', '').strip()

            if len(clean_desc) < 15: # Slightly relaxed from 20 to 15
                logging.warning(f"Plan validation failed: Task description too short (min 15): '{clean_desc}'")
                return False

        return True

    def generate(self, spec_content: str, tech_config: dict = None, complexity: str = 'medium') -> str:
        """
        Generate a detailed IMPLEMENTATION_PLAN.md content from SPEC.md.
        """
        tech_info_str = json.dumps(tech_config, indent=2) if tech_config else ""
        system_prompt = get_plan_system_prompt(tech_info_str, complexity=complexity)

        response = self.ai.generate(f"{system_prompt}\n\nSPECIFICATION:\n{spec_content}")

        # Get tech name for display
        tech_name = tech_config.get("display_name", "Auto-detected") if tech_config else "Auto-detected"

        # Usar parser robusto
        parser = RobustJSONParser()
        try:
            plan_schema = parser.parse_plan(response)
            data = plan_schema.model_dump()
        except Exception as e:
            logging.error(f"Plan validation failed: {e}. Using fallback.")
            data = {
                "phases": [{"name": "Initial Setup Phase", "tasks": [{"description": "Initialize project structure and environment"}]}],
                "total_tasks": 1,
                "completed_tasks": 0,
                "remaining_tasks": 1,
                "blocked_tasks": []
            }

        data["tech_stack"] = tech_name
        template = self.env.get_template("IMPLEMENTATION_PLAN.md.jinja2")
        return template.render(**data)
