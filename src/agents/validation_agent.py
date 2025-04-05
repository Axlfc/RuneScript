from typing import Dict
import logging


class ValidationAgent:
    def __init__(self, agent):
        self.agent = agent

    def validate_project(self) -> Dict:
        logging.info("Validating project")
        validation_results = {
            "test_success_rate": self.agent._run_tests(),
            "code_quality_score": self.agent._analyze_code_quality()
        }
        return validation_results
