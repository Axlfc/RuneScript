"""
Quality Checker para validar estándares de código.
"""

import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

class QualityChecker:
    """Valida que archivos cumplan quality standards del tech stack."""

    def validate(self, files: Dict[str, str], tech_config: dict) -> List[str]:
        """
        Valida archivos contra quality_standards.

        Args:
            files: Dict de {filename: content}
            tech_config: Config del tech stack con quality_standards

        Returns:
            Lista de issues encontrados (vacía si todo OK)
        """
        standards = tech_config.get("quality_standards", {})
        if not standards:
            logger.debug("No quality standards defined for this tech stack")
            return []

        issues = []

        for filename, content in files.items():
            # Obtener extensión sin punto
            ext = Path(filename).suffix.lstrip('.')

            if ext not in standards:
                continue

            min_lines = standards[ext].get('min_lines', 0)
            if min_lines == 0:
                continue

            # Contar solo líneas no vacías (ignorar whitespace)
            actual_lines = len([line for line in content.splitlines() if line.strip()])

            if actual_lines < min_lines:
                issue = (
                    f"{filename} tiene {actual_lines} líneas de código, "
                    f"requiere mínimo {min_lines} líneas según quality standards"
                )
                issues.append(issue)
                logger.warning(issue)

        return issues

    def generate_feedback(self, issues: List[str]) -> str:
        """
        Genera feedback estructurado para la IA cuando falla quality check.

        Args:
            issues: Lista de problemas de calidad

        Returns:
            String de feedback para incluir en el prompt de retry
        """
        if not issues:
            return ""

        feedback = "QUALITY CHECK FAILED:\n"
        feedback += "\n".join(f"- {issue}" for issue in issues)
        feedback += "\n\nPor favor, genera implementaciones más completas y detalladas "
        feedback += "que cumplan con los estándares de calidad profesional. "
        feedback += "No uses placeholders, stubs, o código mínimo. "
        feedback += "Implementa todas las funcionalidades mencionadas en la tarea con código production-ready."

        return feedback
