from typing import Dict
import logging

from src.utils.parser_utils import AIResponseParser


class ArchitectureAgent:
    def __init__(self, agent):
        self.agent = agent

    def design(self, project_scope: Dict) -> Dict:
        logging.info("Designing project architecture")
        related_chunks = self.agent.get_relevant_rag_context(
            f"What architectures are recommended for projects like: {project_scope.get('project_name')}"
        )

        context = {
            "project_scope": project_scope,
            "default_structure": [
                "src/",
                "tests/",
                "docs/",
                "README.md"
            ],
            "retrieved_context": related_chunks
        }
        ai_response = self.agent.process_prompt_with_ai("architecture_design", context)
        architecture = AIResponseParser.parse_ai_response(ai_response)
        if not architecture:
            architecture = {
                "project_name": project_scope.get("project_name", "Unnamed Project"),
                "directory_structure": context["default_structure"],
                "initial_modules": [],
                "testing_framework": "pytest"
            }
        return architecture