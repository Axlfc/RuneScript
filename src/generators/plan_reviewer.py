import json
import logging
from src.models.ai_assistant import AIAssistant

logger = logging.getLogger(__name__)

class PlanReviewer:
    def __init__(self, ai_client=None, max_iterations=2):
        self.ai = ai_client or AIAssistant()
        self.max_iterations = max_iterations

    def review_and_improve(self, spec_content, plan_content, user_request):
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

            prompt = f"""
Eres un arquitecto de software experto revisando un plan de implementación.

SOLICITUD ORIGINAL:
{user_request}

ESPECIFICACIÓN GENERADA:
{spec_content}

PLAN DE IMPLEMENTACIÓN PROPUESTO:
{current_plan_to_review}

TAREA: Realiza una revisión crítica respondiendo:

1. COMPLETITUD: ¿El plan cumple TODOS los requisitos? Lista lo que falta.
2. CALIDAD: ¿Las tareas generarán código profesional o solo stubs básicos?
3. GRANULARIDAD: ¿Las tareas son demasiado grandes o pequeñas?
4. ARCHIVOS: ¿Faltan requirements.txt, .gitignore u otros archivos esenciales?
5. TESTS: ¿Los tests verifican funcionalidad real o solo existencia de archivos?

Responde EXCLUSIVAMENTE en JSON con este formato:
{{
  "approved": true/false,
  "issues_found": ["issue1", "issue2"],
  "missing_requirements": ["req1", "req2"],
  "improved_plan": {{
      "phases": [
          {{
              "name": "Phase Name",
              "tasks": [{{ "description": "Task description" }}]
          }}
      ]
  }}
}}

Si approved=false, genera un improved_plan que resuelva todos los issues. El plan debe ser detallado y seguir principios TDD.
"""
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
                    # For the next iteration, we critique the improved plan
                    # We need to convert it back to some text representation for the prompt
                    current_plan_to_review = json.dumps(improved_plan_data, indent=2)

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
