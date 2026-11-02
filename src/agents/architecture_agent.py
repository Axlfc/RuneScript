from typing import Dict
import logging

from src.utils.parser_utils import AIResponseParser


class ArchitectureAgent:
    def __init__(self, agent):
        self.agent = agent

    def design(self, project_scope: Dict) -> Dict:
        logging.info("Designing project architecture")

        # Some callers provide a wrapper with project_scope/previous_feedback.
        # Normalize it so the authoritative project identity is never lost.
        wrapper = project_scope if isinstance(project_scope, dict) else {}
        scope = wrapper.get("project_scope", wrapper)
        bootstrap = getattr(self.agent, "bootstrap_metadata", {}) or {}
        project_name = (
            scope.get("project_name")
            or bootstrap.get("project_name")
            or "Unnamed Project"
        )

        related_chunks = self.agent.get_relevant_rag_context(
            f"What architectures are recommended for projects like: {project_name}"
        )

        context = {
            "project_scope": scope,
            "bootstrap_metadata": bootstrap,
            "iteration_goal": getattr(self.agent, "current_iteration_goal", None),
            "default_structure": [
                "src/",
                "tests/",
                "docs/",
                "README.md"
            ],
            "retrieved_context": related_chunks
        }
        if wrapper.get("previous_feedback"):
            context["previous_feedback"] = wrapper["previous_feedback"]
        ai_response = self.agent.process_prompt_with_ai("architecture_design", context)
        architecture = AIResponseParser.parse_ai_response(ai_response)
        if not architecture:
            architecture = {
                "project_name": project_name,
                "directory_structure": context["default_structure"],
                "initial_modules": [],
                "testing_framework": "pytest"
            }
        return architecture
