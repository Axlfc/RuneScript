class TDDWorkflowManager:
    """
    Manages the TDD workflow state and transitions between red-green-refactor phases
    """

    def __init__(self, project_io, ui_manager):
        self.phases = ["RED", "GREEN", "REFACTOR"]
        self.current_phase = "RED"
        self.project_io = project_io
        self.ui_manager = ui_manager
        self.test_status = None

    def start_new_cycle(self):
        """Start a new TDD cycle"""
        self.transition_to_phase("RED")

    def transition_to_phase(self, phase):
        """Transition to the specified phase"""
        if phase not in self.phases:
            raise ValueError(f"Invalid phase: {phase}")

        self.current_phase = phase
        self.ui_manager.update_phase_ui(phase, self.test_status)

    def run_tests(self):
        """Run tests and determine next phase based on results"""
        success, stdout, stderr = self.project_io.run_tests()

        if success:
            self.test_status = "passed"
            if self.current_phase == "RED":
                # Tests unexpectedly passed in RED phase
                self.ui_manager.show_message(
                    "Test Already Passes",
                    "Your test already passes! Write a failing test first."
                )
            else:
                # Tests passed, move to REFACTOR phase
                self.transition_to_phase("REFACTOR")
        else:
            self.test_status = "failed"
            if self.current_phase == "RED":
                # Expected failure in RED phase, move to GREEN phase
                self.transition_to_phase("GREEN")
            else:
                # Unexpected failure in other phases
                self.ui_manager.show_message(
                    "Tests Failed",
                    "Your tests are failing. Fix your implementation."
                )

        # Update UI with test results
        self.ui_manager.update_test_results(success, stdout, stderr)
        return success

    def write_test(self):
        """Handle actions for the RED phase (writing tests)"""
        # If we're not already in RED phase, transition
        if self.current_phase != "RED":
            self.transition_to_phase("RED")

        # Focus on test editor
        self.ui_manager.focus_test_editor()

    def implement_code(self):
        """Handle actions for the GREEN phase (implementing code)"""
        # Focus on implementation editor
        self.ui_manager.focus_implementation_editor()

    def refactor_code(self):
        """Handle actions for the REFACTOR phase"""
        # No special action needed, just update phase
        if self.current_phase != "REFACTOR":
            self.transition_to_phase("REFACTOR")

        # We still need passing tests to be in refactor phase
        if self.test_status != "passed":
            self.ui_manager.show_message(
                "Cannot Refactor",
                "Tests must be passing before refactoring. Fix your implementation."
            )
            return False

        return True