import logging
from typing import Dict, List

from src.utils.parser_utils import AIResponseParser


class TestGenerationAgent:
    def __init__(self, agent):
        self.agent = agent
        self.tdd = agent.tdd

    def generate_tests(self, architecture: Dict) -> List[Dict]:
        logging.info("Generating RED-phase test cases")

        # Only skip tests when the architecture explicitly declares a
        # design-only/static project. Merely containing frontend, web, SSE or
        # WebSocket components must never disable TDD for a full-stack system.
        project_type = str(architecture.get("project_type", "")).strip().lower()
        testing_framework = str(architecture.get("testing_framework", "")).strip().lower()
        if project_type in {"design_only", "static_visual"} and testing_framework in {"", "none", "manual"}:
            logging.info("Skipping test generation for explicitly design-only/static project.")
            return []

        context = {
            "architecture": architecture,
            "project_scope": getattr(self.agent, "project_scope", None),
            "bootstrap_metadata": getattr(self.agent, "bootstrap_metadata", {}) or {},
            "iteration_goal": getattr(self.agent, "current_iteration_goal", None),
            "previous_feedback": getattr(self.agent, "feedback_buffer", None),
        }
        related_chunks = self.agent.get_relevant_rag_context(
            f"What kinds of tests are common for systems like: {architecture.get('project_name')}"
        )
        context["retrieved_context"] = related_chunks
        ai_response = self.agent.process_prompt_with_ai("test_generation", context)
        parsed = AIResponseParser.parse_ai_response(ai_response)

        if not isinstance(parsed, list):
            logging.warning("Invalid test format, using fallback.")
            parsed = [{
                "name": "test_project_initialization",
                "description": "Verify project initializes correctly",
                "module": "test_core.py"
            }]

        valid_tests = []
        for test in parsed:
            if not isinstance(test, dict) or "name" not in test:
                continue

            name = test["name"]
            description = test.get("description", "No description provided")
            module = test.get("module", "test_misc.py")
            test_code = test.get("content") or self._generate_red_test(name, description)

            valid_tests.append({
                "name": name,
                "description": description,
                "module": module,
                "content": test_code
            })

        return valid_tests

    def _generate_red_test(self, name: str, description: str) -> str:
        class_name = name.replace("test_", "Test").title().replace("_", "")
        return f'''# {name}
# {description}

import unittest

class {class_name}(unittest.TestCase):
    def test_unimplemented(self):
        self.fail("ðŸ”´ RED: This test is intentionally failing until the feature is implemented.")

if __name__ == '__main__':
    unittest.main()
'''
