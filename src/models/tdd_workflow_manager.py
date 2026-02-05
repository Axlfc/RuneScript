from src.views.tk_utils import PHASE_UI_LABELS, UI_TO_INTERNAL_PHASE


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

        self.last_test_output = None  # ðŸ†• Store last test result here

    def start_new_cycle(self):
        """Start a new TDD cycle"""
        self.transition_to_phase("RED")

    def transition_to_phase(self, phase: str):
        phase = UI_TO_INTERNAL_PHASE.get(phase, phase)
        if phase not in self.phases:
            raise ValueError(f"Invalid phase: {phase}")

        # Check for blocking issues before transition
        if hasattr(self.ui_manager, 'has_blocking_issues') and self.ui_manager.has_blocking_issues():
            self.ui_manager.show_message("Action Blocked",
                                          "You have CRITICAL issues that must be resolved before proceeding.")
            self.ui_manager.open_issue_manager()
            return False

        self.current_phase = phase
        ui_label = PHASE_UI_LABELS.get(phase, phase)
        self.ui_manager.update_phase_ui(ui_label, self.test_status)
        return True

    def rerun_last_test(self):
        """Re-run the previously executed test, if available."""
        if not self.last_test_output:
            self.ui_manager.show_message("Nothing to Re-run", "No test has been run yet.")
            return

        success, stdout, stderr = self.project_io.run_tests()
        self.last_test_output = (success, stdout, stderr)
        self.ui_manager.update_test_results(success, stdout, stderr)
        self.ui_manager.tdd_panel.update_last_result_label(success)
        self.ui_manager.tdd_panel.set_rerun_enabled(True, "Passed" if success else "Failed")

    def run_tests(self):
        """Run tests and determine next phase based on results"""
        success, stdout, stderr = self.project_io.run_tests()

        # Save last output for re-runs
        self.last_test_output = (success, stdout, stderr)

        # Show results in UI
        self.ui_manager.update_test_results(success, stdout, stderr)
        self.ui_manager.tdd_panel.update_last_result_label(success)

        # Always allow rerun after running tests
        if hasattr(self.ui_manager, "tdd_panel"):
            self.ui_manager.tdd_panel.set_rerun_enabled(True)
            self.ui_manager.tdd_panel.update_last_test_summary("passed" if success else "failed")

        if success:
            self.test_status = "passed"
            #
            if self.current_phase == "RED":
                self.ui_manager.show_message(
                    "Test Already Passes",
                    "Your test already passes! Write a failing test first."
                )
            else:
                self.transition_to_phase("REFACTOR")
        else:
            self.test_status = "failed"
            if self.current_phase == "RED":
                self.transition_to_phase("GREEN")
            else:
                self.ui_manager.show_message(
                    "Tests Failed",
                    "Your tests are failing. Fix your implementation."
                )

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
