import pytest
from src.core.robust_parser import RobustJSONParser, SpecSchema, PlanSchema

class TestRobustJSONParser:

    def test_extract_from_markdown(self):
        """Test extracción desde código markdown."""
        parser = RobustJSONParser()
        response = '''
        Aquí está tu plan:
        ```json
        {"total_tasks": 5, "phases": [{"name": "Setup", "tasks": [{"description": "Initialize project structure"}]}]}
        ```
        '''
        result = parser.extract_json(response)
        assert result is not None
        assert result["total_tasks"] == 5

    def test_extract_clean_json(self):
        """Test extracción de JSON limpio."""
        parser = RobustJSONParser()
        response = '{"total_tasks": 10, "phases": []}'
        result = parser.extract_json(response)
        assert result["total_tasks"] == 10

    def test_extract_with_explanation(self):
        """Test extracción cuando hay texto explicativo."""
        parser = RobustJSONParser()
        response = 'Claro, genero el plan: {"total_tasks": 3, "phases": []} - espero que ayude!'
        result = parser.extract_json(response)
        assert result["total_tasks"] == 3

    def test_extract_fails_gracefully(self):
        """Test cuando no hay JSON válido."""
        parser = RobustJSONParser()
        response = "Esta respuesta no contiene JSON, solo texto."
        result = parser.extract_json(response)
        assert result is None

    def test_parse_plan_validation(self):
        """Test validación de PlanSchema."""
        parser = RobustJSONParser()
        response = '''```json
        {
            "phases": [
                {"name": "Phase 1", "tasks": [{"description": "Task description longer than 15 chars"}]},
                {"name": "Phase 2", "tasks": [{"description": "Another task description"}]}
            ],
            "total_tasks": 2
        }
        ```'''

        plan = parser.parse_plan(response)
        assert isinstance(plan, PlanSchema)
        assert len(plan.phases) >= 2

    def test_parse_plan_fails_on_invalid(self):
        """Test que falla cuando el plan es inválido."""
        parser = RobustJSONParser()
        # Plan con solo 1 fase (debe tener min 2)
        response = '{"phases": [{"name": "Solo", "tasks": []}], "total_tasks": 0}'

        with pytest.raises(ValueError):
            parser.parse_plan(response)
