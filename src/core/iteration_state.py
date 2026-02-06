
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class IterationState:
    """
    Maintains state across retry attempts within a single iteration.
    Ensures consistency and prevents context loss.
    """

    def __init__(self, task_description: str):
        self.task_description = task_description
        self.test_file: Optional[str] = None  # Lock this in on first attempt
        self.test_name: Optional[str] = None
        self.attempt_number = 0
        self.generated_files_history: List[Dict[str, str]] = []
        self.tests_passed_history: List[bool] = []

    def register_attempt(self, files_generated: Dict[str, str], tests_passed: bool = False, test_file: str = None, test_name: str = None):
        """Record what was generated in this attempt."""
        self.attempt_number += 1
        self.generated_files_history.append(files_generated)
        self.tests_passed_history.append(tests_passed)

        # Lock in test file on first attempt or if not already set
        if not self.test_file and test_file:
            self.test_file = test_file
            self.test_name = test_name
            logger.info(f"Locked in test file for this iteration: {self.test_file}")

    def update_attempt_status(self, attempt_idx: int, tests_passed: bool):
        """Updates the status of a specific attempt."""
        if 0 <= attempt_idx < len(self.tests_passed_history):
            self.tests_passed_history[attempt_idx] = tests_passed
        else:
            logger.warning(f"Attempt to update status for invalid attempt index: {attempt_idx}")

    def validate_retry_attempt(self, proposed_files: Dict[str, str], proposed_test_file: str = None) -> Tuple[bool, Optional[str]]:
        """
        Ensure retry attempts maintain consistency.
        Returns: (is_valid, error_message)
        """
        if not self.test_file:
            return True, None

        if proposed_test_file and proposed_test_file != self.test_file:
            return False, (
                f"Test file changed from {self.test_file} to "
                f"{proposed_test_file}. Retries must use the same test file."
            )

        # Also check if a test file exists in proposed_files that is different from locked one
        new_test_files = [f for f in proposed_files if f.startswith('tests/') and f.endswith('.py')]
        if new_test_files and self.test_file not in new_test_files:
             return False, (
                f"Original test file {self.test_file} missing from response. "
                f"AI proposed new test files: {new_test_files}. Consistency required."
            )

        return True, None

    def get_last_successful_files(self) -> Optional[Dict[str, str]]:
        """Returns the files from the last attempt where tests passed."""
        for i in range(len(self.tests_passed_history) - 1, -1, -1):
            if self.tests_passed_history[i]:
                return self.generated_files_history[i]
        return None
