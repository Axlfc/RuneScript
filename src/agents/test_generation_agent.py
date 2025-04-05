import logging
from typing import Dict, List

from src.models.tdd_manager import TDDStage
from src.utils.parser_utils import AIResponseParser


class TestGenerationAgent:
    def __init__(self, agent):
        self.agent = agent
        self.tdd = agent.tdd

    def generate_tests(self, architecture: Dict) -> List[Dict]:
        logging.info("Generating RED-phase test cases")
        # Skip tests if project looks purely visual
        if any(k in str(architecture).lower() for k in ["html", "css", "web", "landing", "portfolio"]):
            logging.info("Skipping test generation — visual/static project.")
            return []

        context = {"architecture": architecture}
        related_chunks = self.agent.get_relevant_rag_context(
            f"What kinds of tests are common for systems like: {architecture.get('project_name')}")
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

            # test_code = self._generate_red_test(name, description)

            # Track the full TDD cycle from RED
            cycle_id = self.tdd.start_cycle(name)

            test_code = self.tdd.get_test_content(cycle_id)
            context = {
                "test_name": test["name"],
                "test_code": test_code,
                "requirements": self.project_scope or {},
            }

            self.tdd.add_test_content(cycle_id, test_code)
            self.tdd.set_stage(cycle_id, TDDStage.RED)

            valid_tests.append({
                "name": name,
                "description": description,
                "module": module,
                "content": test_code,
                "cycle_id": cycle_id
            })

        return valid_tests

    def _generate_red_test(self, name: str, description: str) -> str:
        class_name = name.replace("test_", "Test").title().replace("_", "")
        return f'''# {name}
# {description}

import unittest

class {class_name}(unittest.TestCase):
    def test_unimplemented(self):
        self.fail("🔴 RED: This test is intentionally failing until the feature is implemented.")

if __name__ == '__main__':
    unittest.main()
'''