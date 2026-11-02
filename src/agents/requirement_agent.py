import logging
from typing import Dict

from src.utils.parser_utils import AIResponseParser


class RequirementAgent:
    def __init__(self, agent):
        self.agent = agent

    def analyze(self, requirements: str) -> Dict:
        logging.info(f"Analyzing requirements: {requirements}")
        related_chunks = self.agent.get_relevant_rag_context(
            f"What are best practices for: {requirements}",
            top_k=3,
            as_context=True
        )

        bootstrap = getattr(self.agent, "bootstrap_metadata", {}) or {}
        project_name = bootstrap.get("project_name") or self.agent._generate_project_name()

        context = {
            "requirements": requirements,
            "project_name": project_name,
            "bootstrap_metadata": {
                "project_name": bootstrap.get("project_name"),
                "project_description": bootstrap.get("project_description"),
                "key_features": bootstrap.get("key_features", []),
                "project_tasks": bootstrap.get("project_tasks", []),
                "validation_notes": bootstrap.get("validation_notes", []),
            },
            "retrieved_context": related_chunks
        }
        ai_response = self.agent.process_prompt_with_ai("requirement_analysis", context)
        project_scope = AIResponseParser.parse_ai_response(ai_response)
        if not project_scope:
            project_scope = {
                "project_name": context["project_name"],
                "key_features": ["Core Functionality"],
                "constraints": []
            }
        return project_scope
