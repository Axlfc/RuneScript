import pytest
from src.core.quality import QualityChecker

class TestQualityChecker:

    def test_validate_passes_standard(self):
        """Test cuando archivos cumplen el estándar."""
        checker = QualityChecker()
        valid_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Test</title></head>
        <body>
        """ + "\n".join([f"<div>Line {i}</div>" for i in range(20)]) + """
        </body>
        </html>
        """
        files = {
            "index.html": valid_html
        }
        tech_config = {
            "quality_standards": {
                "html": {"min_lines": 15}
            }
        }

        issues = checker.validate(files, tech_config)
        assert len(issues) == 0

    def test_validate_fails_standard(self):
        """Test cuando archivo no cumple mínimo."""
        checker = QualityChecker()
        files = {
            "styles.css": "body { color: red; }\n.header { height: 10px; }\n.footer { width: 100%; }"
        }
        tech_config = {
            "quality_standards": {
                "css": {"min_lines": 50}
            }
        }

        issues = checker.validate(files, tech_config)
        # Should have standard line count issue, but NOT complexity issue since it has 3 rules
        assert len(issues) == 1
        assert "styles.css tiene 3 líneas de código" in issues[0]

    def test_ignores_files_without_standards(self):
        """Test que ignora archivos sin standards definidos."""
        checker = QualityChecker()
        files = {
            "README.md": "# Short readme"
        }
        tech_config = {
            "quality_standards": {
                "html": {"min_lines": 100}
            }
        }

        issues = checker.validate(files, tech_config)
        assert len(issues) == 0

    def test_counts_only_non_empty_lines(self):
        """Test que solo cuenta líneas con contenido."""
        checker = QualityChecker()
        files = {
            "app.js": """

            function test() {
                console.log("test");
            }


            """  # 3 líneas con contenido real
        }
        tech_config = {
            "quality_standards": {
                "js": {"min_lines": 5}
            }
        }

        issues = checker.validate(files, tech_config)
        assert len(issues) == 1  # Debería fallar (3 < 5)

    def test_generate_feedback(self):
        """Test generación de feedback estructurado."""
        checker = QualityChecker()
        issues = [
            "index.html tiene 10 líneas, requiere 150",
            "styles.css tiene 5 líneas, requiere 200"
        ]

        feedback = checker.generate_feedback(issues)
        assert "QUALITY CHECK FAILED" in feedback
        assert "index.html" in feedback
        assert "styles.css" in feedback
        assert "production-ready" in feedback
