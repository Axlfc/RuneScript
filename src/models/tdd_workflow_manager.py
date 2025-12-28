from src.agents.test_generation_agent import TestGenerationAgent
from src.utils.test_runner import run_pytest
import os
import re

class TDDWorkflowManager:
    """
    Manages the intelligent, AI-assisted TDD workflow, orchestrating
    the UI, AI agents, and test runner.
    """

    def __init__(self, ui_panel, project_path):
        self.ui = ui_panel
        self.project_path = project_path
        self.test_generation_agent = TestGenerationAgent(self) # Simplified for now

        # In-memory storage for generated files until commit
        self.temp_test_code = None
        self.temp_impl_code = None
        self.temp_impl_file_path = os.path.join(self.project_path, "temp_implementation.py")
        self.test_file_path = os.path.join(self.project_path, "temp_test_suite.py")
        self._after_id = None

    def start_red_phase(self, user_intent: str):
        """
        Kicks off the TDD cycle by generating a failing test from user intent.
        """
        if not user_intent:
            print("User intent cannot be empty.")
            return

        self.temp_test_code = self._mock_generate_test(user_intent)
        self.ui.test_code_text.config(state="normal")
        self.ui.test_code_text.delete("1.0", "end")
        self.ui.test_code_text.insert("1.0", self.temp_test_code)
        self.ui.test_code_text.config(state="disabled")

        with open(self.test_file_path, "w") as f:
            f.write(self.temp_test_code)

        test_result = run_pytest(self.project_path)
        output = test_result.stdout + "\n" + test_result.stderr

        if not test_result.success:
            self.ui.set_state("RED", test_output=output)
            # Start the live feedback loop
            self.start_live_feedback_loop()
        else:
            self.ui.set_state("GREEN", test_output="Warning: Generated test passed immediately.\n" + output)

    def start_live_feedback_loop(self):
        """Starts the timer to continuously check the implementation code."""
        # Cancel any existing loop
        if self._after_id:
            self.ui.after_cancel(self._after_id)

        self.check_implementation()

    def check_implementation(self):
        """Periodically checks the implementation code against the test."""
        current_impl_code = self.ui.impl_code_text.get("1.0", "end-1c")

        # Only re-run if the code has changed
        if current_impl_code != self.temp_impl_code:
            self.temp_impl_code = current_impl_code

            # Write the implementation code to a temporary file
            # This is a simplified approach. A real IDE would handle this more robustly.
            with open(self.temp_impl_file_path, "w") as f:
                # We need to prepend the implementation to the test file for the test to see it.
                # This is a hacky way to ensure the test can import the code.
                f.write(self.temp_impl_code)

            # Now, run the test
            test_result = run_pytest(self.project_path)

            if test_result.success:
                output = test_result.stdout + "\n" + test_result.stderr
                self.ui.set_state("GREEN", test_output="Tests passed!\n" + output)
                # Stop the loop
                if self._after_id:
                    self.ui.after_cancel(self._after_id)
                self._after_id = None
                return # Stop checking

        # Schedule the next check
        self._after_id = self.ui.after(2000, self.check_implementation) # Check every 2 seconds

    def start_refactor_phase(self):
        """
        Initiates the refactoring process on the current 'green' code.
        """
        if not self.temp_impl_code:
            print("No implementation code to refactor.")
            return

        # 1. Update UI state
        self.ui.set_state("REFACTORING")

        # 2. Get refactoring suggestions from the AI agent (mocked for now)
        suggestions_diff = self._mock_refactor_agent(self.temp_impl_code)

        # 3. Display the suggestions in the UI
        # (The UI panel will need a method to handle this)
        self.ui.display_refactor_suggestions(suggestions_diff)

    def apply_refactoring(self, new_code: str):
        """
        Applies a refactoring suggestion and runs the safety net check.
        """
        original_code = self.temp_impl_code
        self.temp_impl_code = new_code

        # Apply the change to the UI and the temp file
        self.ui.impl_code_text.delete("1.0", "end")
        self.ui.impl_code_text.insert("1.0", new_code)
        with open(self.temp_impl_file_path, "w") as f:
            f.write(new_code)

        # --- THE SAFETY NET ---
        test_result = run_pytest(self.project_path)

        if test_result.success:
            # The refactoring is safe! Keep the code.
            self.ui.set_state("GREEN", test_output="Refactor successful! Tests are still passing.")
        else:
            # The refactoring broke the code! Revert it.
            self.temp_impl_code = original_code
            self.ui.impl_code_text.delete("1.0", "end")
            self.ui.impl_code_text.insert("1.0", original_code)
            with open(self.temp_impl_file_path, "w") as f:
                f.write(original_code)

            output = "Refactor failed and was reverted. Tests are no longer passing.\n\n" + test_result.stderr
            self.ui.set_state("RED", test_output=output)


    def _mock_generate_test(self, intent: str) -> str:
        """
        A mock function to simulate the TestGenerationAgent.
        In the real implementation, this will call the actual agent.
        """
        # A simple heuristic to generate a plausible-looking test
        function_name_match = [word for word in intent.split() if re.match(r'\w+\(\)', word)]
        if function_name_match:
            function_name = function_name_match[0].replace('()', '')
        else:
            # Fallback for simple intents
            function_name = intent.split(" ")[-1]

        test_function_name = "test_" + function_name
        class_name = "Test" + function_name.capitalize()


        return f\"\"\"
import unittest
from temp_implementation import *

# Test generated from intent: '{intent}'

class {class_name}(unittest.TestCase):
    def {function_name}(self):
        # This test will fail until the feature is implemented
        self.fail("🔴 RED: Test not implemented yet.")

if __name__ == '__main__':
    unittest.main()
\"\"\"

    def _mock_refactor_agent(self, code: str) -> str:
        """
        A mock function to simulate the RefactoringAgent.
        Returns a git-style diff.
        """
        # Simple suggestion: add a docstring and type hints
        original_lines = code.split('\n')

        # Assume the function def is the first line
        if not original_lines or not original_lines[0].strip().startswith("def"):
            return "# No suggestion available"

        func_definition = original_lines[0]
        # A crude way to add type hints for this example
        refactored_func = func_definition.replace("(", "(a: int, b: int) -> int", 1)

        # Build the refactored code with a docstring
        refactored_lines = [
            refactored_func,
            '    """This function was refactored to include a docstring and type hints."""',
        ] + original_lines[1:]

        refactored_code = "\n".join(refactored_lines)

        # Create a basic diff for demonstration
        import difflib
        diff = difflib.unified_diff(
            original_lines, refactored_lines,
            fromfile='original', tofile='refactored', lineterm=''
        )
        return '\n'.join(diff)
