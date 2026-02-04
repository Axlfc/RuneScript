import pytest
from unittest.mock import MagicMock, patch
from src.generators.plan_reviewer import PlanReviewer

class TestPlanReviewer:

    @patch('src.models.ai_assistant.AIAssistant')
    def test_first_iteration_uses_original_markdown(self, mock_ai_class):
        """Test que primera iteración recibe el plan en markdown."""
        mock_ai = mock_ai_class.return_value
        mock_ai.generate.return_value = '''
        {
            "approved": false,
            "issues_found": ["Too generic"],
            "improved_plan": {
                "phases": [
                    {"name": "Phase 1", "tasks": [{"description": "Detailed task description"}]},
                    {"name": "Phase 2", "tasks": [{"description": "Another detailed task"}]}
                ]
            }
        }
        '''

        reviewer = PlanReviewer(ai_client=mock_ai)
        original_plan = "## IMPLEMENTATION PLAN\n[x] Task 1"

        approved, critique, improved, iterations = reviewer.review_and_improve(
            spec_content="spec",
            plan_content=original_plan,
            user_request="Build a website",
            tech_stack="frontend_web"
        )

        # Verificar que el primer generate recibió markdown
        call_args = mock_ai.generate.call_args_list[0][0][0]
        assert "## IMPLEMENTATION PLAN" in call_args or "original plan" in call_args or original_plan in call_args

    @patch('src.models.ai_assistant.AIAssistant')
    def test_second_iteration_uses_rendered_markdown(self, mock_ai_class):
        """Test que segunda iteración recibe plan renderizado en markdown."""
        mock_ai = mock_ai_class.return_value

        # Primera llamada: rechaza y devuelve plan mejorado
        # Segunda llamada: aprueba
        mock_ai.generate.side_effect = [
            '''{"approved": false, "issues_found": ["Issue 1"], "improved_plan": {"phases": [{"name": "P1", "tasks": [{"description": "Task desc longer than 15"}]}, {"name": "P2", "tasks": [{"description": "Another task description"}]}]}}''',
            '''{"approved": true, "issues_found": [], "improved_plan": null}'''
        ]

        reviewer = PlanReviewer(ai_client=mock_ai, max_iterations=2)

        approved, critique, improved, iterations = reviewer.review_and_improve(
            spec_content="spec",
            plan_content="original plan",
            user_request="request",
            tech_stack="python_backend"
        )

        # Verificar que hubo 2 llamadas
        assert mock_ai.generate.call_count == 2

        # Verificar que segunda llamada recibió markdown renderizado (no JSON)
        second_call_arg = mock_ai.generate.call_args_list[1][0][0]
        assert "## PHASE" in second_call_arg.upper() or "Phase" in second_call_arg
        assert '{"phases"' not in second_call_arg  # No debe ser JSON crudo
