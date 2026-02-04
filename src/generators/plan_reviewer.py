import json
import logging
from src.models.ai_assistant import AIAssistant
from src.prompts.templates import get_reviewer_prompt
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

logger = logging.getLogger(__name__)

class PlanReviewer:
    def __init__(self, ai_client=None, max_iterations=2):
        self.ai = ai_client or AIAssistant()
        self.max_iterations = max_iterations
        # Cargar entorno de templates
        templates_dir = Path("src/templates")
        self.env = Environment(loader=FileSystemLoader(str(templates_dir)))

    def review_and_improve(self, spec_content, plan_content, user_request, tech_stack="unknown"):
        """
        Reviews the implementation plan and suggests improvements if needed.
        Returns: (approved, critique, improved_plan_data, iteration_count)
        """
        iteration = 0
        approved = False
        critique = ""
        improved_plan_data = None
        current_plan_to_review = plan_content

        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"Plan Review Iteration {iteration}/{self.max_iterations}")

            prompt = get_reviewer_prompt(user_request, spec_content, current_plan_to_review, tech_stack=tech_stack)
            response = self.ai.generate(prompt)

            try:
                # Clean response if it contains markdown markers
                start = response.find('{')
                end = response.rfind('}') + 1
                data = json.loads(response[start:end])

                approved = data.get("approved", False)
                issues = data.get("issues_found", [])
                missing = data.get("missing_requirements", [])
                critique = f"Issues: {', '.join(issues)}. Missing: {', '.join(missing)}"

                if approved:
                    logger.info("Plan approved by AI reviewer.")
                    improved_plan_data = data.get("improved_plan")
                    break
                else:
                    logger.warning(f"Plan rejected by AI reviewer. Critique: {critique}")
                    improved_plan_data = data.get("improved_plan")

                    # FIX: Renderizar el plan mejorado de vuelta a markdown
                    # para la siguiente iteración
                    if improved_plan_data:
                        template = self.env.get_template("IMPLEMENTATION_PLAN.md.jinja2")
                        # Ensure all needed fields for template are present
                        if "tech_stack" not in improved_plan_data:
                            improved_plan_data["tech_stack"] = tech_stack
                        if "total_tasks" not in improved_plan_data:
                            total = sum(len(phase.get("tasks", [])) for phase in improved_plan_data.get("phases", []))
                            improved_plan_data["total_tasks"] = total
                        if "completed_tasks" not in improved_plan_data:
                            improved_plan_data["completed_tasks"] = 0
                        if "remaining_tasks" not in improved_plan_data:
                            improved_plan_data["remaining_tasks"] = improved_plan_data.get("total_tasks", 0)
                        if "blocked_tasks" not in improved_plan_data:
                            improved_plan_data["blocked_tasks"] = []

                        current_plan_to_review = template.render(**improved_plan_data)
                        logger.debug("Improved plan rendered back to Markdown for next iteration")
                    else:
                        logger.warning("No improved plan returned by reviewer")
                        break

            except Exception as e:
                logger.error(f"Error parsing PlanReviewer response: {e}")
                critique = f"Error parsing AI response: {str(e)}"
                # If we can't parse, we don't have an improved plan to use
                break

        # Ensure counters are correct if we have improved plan data
        if improved_plan_data:
            total = 0
            for phase in improved_plan_data.get("phases", []):
                total += len(phase.get("tasks", []))
            improved_plan_data["total_tasks"] = total
            improved_plan_data["completed_tasks"] = 0
            improved_plan_data["remaining_tasks"] = total
            improved_plan_data["blocked_tasks"] = []

        return approved, critique, improved_plan_data, iteration
