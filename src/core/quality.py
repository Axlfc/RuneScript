"""
Quality Checker para validar estándares de código.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class QualityChecker:
    """Valida que archivos cumplan quality standards del tech stack."""

    def validate(self, files: Dict[str, str], tech_config: dict) -> List[str]:
        """
        Valida archivos contra quality_standards y detecta placeholders.

        Args:
            files: Dict de {filename: content}
            tech_config: Config del tech stack con quality_standards

        Returns:
            Lista de issues encontrados (vacía si todo OK)
        """
        issues = []

        # 1. Detectar Placeholders (Migrado de LoopOrchestrator y mejorado)
        placeholder_file = self.check_placeholders(files)
        if placeholder_file:
            issues.append(f"Placeholder or incomplete code found in {placeholder_file}")

        # 2. Quality Standards (Líneas mínimas)
        standards = tech_config.get("quality_standards", {})
        if standards:
            for filename, content in files.items():
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

        # 3. Semantic Checks
        for filename, content in files.items():
            if filename.endswith('.html'):
                html_issues = self.check_html_completeness(content)
                if html_issues:
                    issues.extend([f"{filename}: {issue}" for issue in html_issues])
            elif filename.endswith('.css'):
                 css_issues = self.check_css_completeness(content)
                 if css_issues:
                     issues.extend([f"{filename}: {issue}" for issue in css_issues])

        return issues

    def check_placeholders(self, files: Dict[str, str]) -> Optional[str]:
        """Check for real placeholders in implementation files, ignoring false positives."""

        # Patterns de placeholders REALES
        real_placeholders = [
            r'TODO:',
            r'FIXME:',
            r'PLACEHOLDER',
            r'\/\/\s*Add\s+.+\s+here',
            r'#\s*Add\s+.+\s+here',
            r'Content here',
            r'#\s*Your code here',
            r'<!--\s*TODO',
            r'\(\.\.\.\)',
            r'\[\.\.\.\]',
            r'\/\/\s*rest\s+of\s+code',
            r'#\s*rest\s+of\s+code',
            r'\/\/\s*etc\.',
            r'#\s*etc\.'
        ]

        for filename, content in files.items():
            # SKIP test files
            if 'test' in filename.lower() or '/tests/' in filename:
                continue

            # Check for "..." or similar on its own line
            for line in content.splitlines():
                stripped = line.strip()
                # Matches "...", "// ...", "# ...", "/* ... */", "<!-- ... -->"
                if re.match(r'^(\.\.\.|# \.\.\.|\/\/ \.\.\.|\/\* \.\.\. \*\/|<!-- \.\.\. -->)$', stripped):
                    return filename

            # Check for real placeholders
            for pattern in real_placeholders:
                if re.search(pattern, content, re.IGNORECASE):
                    return filename

        return None

    def check_html_completeness(self, html: str) -> List[str]:
        """Valida estructura básica de HTML."""
        issues = []
        html_lower = html.lower()

        required = {
            '<!doctype html>': 'Missing DOCTYPE declaration',
            '<html': 'Missing <html> tag',
            '<head': 'Missing <head> section',
            '<body': 'Missing <body> section',
            '</html>': 'Missing closing </html> tag',
            '</body>': 'Missing closing </body> tag'
        }

        for snippet, msg in required.items():
            if snippet not in html_lower:
                issues.append(msg)

        return issues

    def check_css_completeness(self, css: str) -> List[str]:
        """Valida que el CSS tenga selectores y reglas reales."""
        issues = []
        # Buscar patrones de reglas CSS: selector { propiedad: valor; }
        rules = re.findall(r'[^{}]+\{[^{}]+\}', css)
        if len(rules) < 3: # Arbitrario, pero un CSS real debería tener varias reglas
            issues.append("CSS appears too simple or empty of actual rules")
        return issues

    def generate_feedback(self, issues: List[str]) -> str:
        """Genera feedback estructurado para la IA."""
        if not issues:
            return ""

        feedback = "╔══════════════════════════════════════════════════════════╗\n"
        feedback += "║ ⚠️ QUALITY STANDARDS NOT MET (IMPLEMENTATION REJECTED)  ║\n"
        feedback += "╚══════════════════════════════════════════════════════════╝\n\n"
        feedback += "The following issues were found in your implementation:\n"
        feedback += "\n".join(f"❌ {issue}" for issue in issues)
        feedback += "\n\nREQUIRED ACTION:\n"
        feedback += "1. RE-GENERATE the files with COMPLETE implementations. DO NOT TRUNCATE.\n"
        feedback += "2. REMOVE all placeholders like '...', '// rest of code', or 'TODO'.\n"
        feedback += "3. INCREASE CONTENT VOLUME significantly:\n"
        feedback += "   - HTML: Expand all sections (Navigation, Hero, Features, About, Portfolio, Contact, Footer).\n"
        feedback += "   - CSS: Add variables, layout rules, typography, responsive queries, and hover effects (min 200 lines).\n"
        feedback += "   - JS: Implement full interactivity, event listeners, and DOM manipulation (min 100 lines).\n"
        feedback += "\nYOUR RESPONSE MUST BE PRODUCTION-READY."

        return feedback
