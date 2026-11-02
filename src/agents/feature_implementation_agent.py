from src.utils.parser_utils import AIResponseParser
from typing import List, Dict
import logging


class FeatureImplementationAgent:
    def __init__(self, agent):
        self.agent = agent

    def implement_features(self, tests: List[Dict]) -> Dict:
        logging.info("Implementing features")

        existing_files = []
        code_files = self.agent.state.state.get("code_files", {})
        if isinstance(code_files, dict):
            for filename, content in list(code_files.items())[-20:]:
                existing_files.append({
                    "filename": filename,
                    "content": content[:20000] if isinstance(content, str) else str(content)
                })

        bootstrap = getattr(self.agent, "bootstrap_metadata", {}) or {}
        project_scope = getattr(self.agent, "project_scope", None)
        architecture = getattr(self.agent, "architecture", None)
        iteration_goal = getattr(self.agent, "current_iteration_goal", None)
        previous_feedback = getattr(self.agent, "feedback_buffer", None)

        context = {
            "project_name": bootstrap.get("project_name"),
            "project_description": bootstrap.get("project_description"),
            "iteration_goal": iteration_goal,
            "project_scope": project_scope,
            "architecture": architecture,
            "tests": tests,
            "existing_files": existing_files,
            "previous_feedback": previous_feedback,
            "instruction": (
                "Implement the current iteration goal for this project. "
                "Preserve compatibility with existing public imports and tests. "
                "When modifying an existing module, return the complete updated file. "
                "Do not invent a different project/package identity."
            )
        }

        related_chunks = self.agent.get_relevant_rag_context(
            f"How should {bootstrap.get('project_name', 'this project')} implement: "
            f"{iteration_goal or 'the current tested feature'}?"
        )
        context["retrieved_context"] = related_chunks

        ai_response = self.agent.process_prompt_with_ai("feature_implementation", context)
        implementation_results = AIResponseParser.parse_ai_response(ai_response)
        if not implementation_results:
            implementation_results = {
                "implemented_modules": [],
                "test_coverage": {}
            }
        return implementation_results
