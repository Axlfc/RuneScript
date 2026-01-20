from typing import Dict
import logging
from src.utils.file_helpers import enrich_context_with_relevant_files

class RefactoringAgent:
    def __init__(self, agent):
        self.agent = agent

    def refactor_code(self, implementation_results: Dict):
        logging.info("Performing code refactoring")
        context = {
            "implementation_results": implementation_results
        }

        # Feed the AI some actual files, not just vibes
        context = enrich_context_with_relevant_files(context, self.agent.project_path)

        related_chunks = self.agent.get_relevant_rag_context(
            "What are best practices for refactoring Python code?")
        context["retrieved_context"] = related_chunks
        self.agent.process_prompt_with_ai("code_refactoring", context)
