from src.utils.parser_utils import AIResponseParser
from typing import List, Dict
import logging


class FeatureImplementationAgent:
    def __init__(self, agent):
        self.agent = agent

    def implement_features(self, tests: List[Dict]) -> Dict:
        logging.info("Implementing features")
        context = {
            "tests": tests
        }
        related_chunks = self.agent.get_relevant_rag_context(
            "How are similar features typically implemented?")
        context["retrieved_context"] = related_chunks
        ai_response = self.agent.process_prompt_with_ai("feature_implementation", context)
        implementation_results = AIResponseParser.parse_ai_response(ai_response)
        if not implementation_results:
            implementation_results = {
                "implemented_modules": [],
                "test_coverage": {}
            }
        return implementation_results