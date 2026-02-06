"""
Quality Checker para validar estándares de código.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class QualityIssue:
    def __init__(self, filename: str, message: str, severity: str = "ERROR", type: str = "GENERAL"):
        self.filename = filename
        self.message = message
        self.severity = severity  # "ERROR" or "WARNING"
        self.type = type

    def __str__(self):
        prefix = "❌" if self.severity == "ERROR" else "⚠️"
        return f"{prefix} {self.filename}: {self.message}"

class QualityChecker:
    """Valida que archivos cumplan quality standards del tech stack."""

    ALLOWED_PATTERNS = {
        'html': [
            r'<[^>]+\s+placeholder="[^"]*"',           # placeholder attribute
            r'alt="[^"]*placeholder[^"]*"',            # alt text with placeholder
            r'src="[^"]*placeholder[^"]*"',            # src with placeholder word
            r'<div[^>]+>Project \d+</div>',            # demo content
            r'<div[^>]+>Coming Soon</div>',            # temporal content
            r'src="https://via\.placeholder\.com',     # placeholder.com
            r'<!-- TODO: Add real images -->',         # business TODOs
        ],
        'python': [
            r'# TODO:.*after.*approval',               # explicit business TODO
            r'# Placeholder for future',               # documented placeholder
            r'""".*TODO.*"""',                          # docstring TODO
        ],
        'javascript': [
            r'// TODO: Implement.*Phase \d+',         # phased implementation
            r'console\.log\(["\']TODO',                # debug TODOs
            r'\/\/\s*Example\s+usage:',                # examples in comments
        ],
        'css': [
            r'/\*.*placeholder.*\*/',                  # CSS comments
            r'content:\s*["\']\.\.\.["\']',            # CSS content property
            r'text-overflow:\s*ellipsis',              # ellipsis is NOT a placeholder
        ]
    }

    FORBIDDEN_PATTERNS = {
        'python': [
            r'def\s+\w+\([^)]*\):\s*(\.\.\.|\bpass\b)\s*$',  # función stub
            r'[A-Z_]+\s*=\s*["\']YOUR_\w+_HERE["\']',       # API keys placeholder
        ],
        'javascript': [
            r'function\s+\w+\([^)]*\)\s*{\s*}\s*$',         # función vacía
        ],
        'all': [
            r'TODO:\s*implement',                            # TODO genérico
            r'PLACEHOLDER',
            r'Content here',
            r'Your code here',
            r'rest of code',
            r'etc\.'
        ]
    }

    def validate(self, files: Dict[str, str], tech_config: dict) -> List[QualityIssue]:
        """
        Valida archivos contra quality_standards y detecta placeholders.

        Args:
            files: Dict de {filename: content}
            tech_config: Config del tech stack con quality_standards

        Returns:
            Lista de QualityIssue encontrados (vacía si todo OK)
        """
        issues = []

        # 1. Detectar Placeholders
        for filename, content in files.items():
            placeholder_detected = self.check_placeholders({filename: content})
            if placeholder_detected:
                issues.append(QualityIssue(
                    filename=filename,
                    message="Placeholder or incomplete code found (e.g. '...', 'TODO: implement')",
                    severity="ERROR",
                    type="PLACEHOLDER"
                ))

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
                    # DA-002: Hard line count failures -> Warnings if difference is minimal
                    diff = min_lines - actual_lines
                    # If less than 10% or less than 5 lines short, it's just a warning
                    is_trivial = diff < 5 or diff < (min_lines * 0.1)

                    severity = "WARNING" if is_trivial else "ERROR"

                    issues.append(QualityIssue(
                        filename=filename,
                        message=f"File has {actual_lines} lines, requires minimum {min_lines} lines",
                        severity=severity,
                        type="LINE_COUNT"
                    ))
                    logger.warning(f"Quality {severity} for {filename}: {actual_lines}/{min_lines} lines")

        # 3. Semantic Checks
        for filename, content in files.items():
            if filename.endswith('.html'):
                html_msgs = self.check_html_completeness(content)
                for msg in html_msgs:
                    issues.append(QualityIssue(filename, msg, "ERROR", "HTML_STRUCTURE"))

            elif filename.endswith('.js'):
                js_issues = self.check_js_completeness(content)
                for msg in js_issues:
                    # JS completeness issues are warnings for now
                    issues.append(QualityIssue(filename, msg, "WARNING", "JS_COMPLETENESS"))

                # Best practice: placeholders without TODO
                if 'placeholder' in content.lower() and 'TODO' not in content.upper():
                    issues.append(QualityIssue(filename, "Contains 'placeholder' text without a corresponding TODO marker", "WARNING", "BEST_PRACTICE"))

            elif filename.endswith('.css'):
                css_msgs = self.check_css_completeness(content)
                for msg in css_msgs:
                    issues.append(QualityIssue(filename, msg, "WARNING", "CSS_COMPLETENESS"))

        return issues

    def check_placeholders(self, files: Dict[str, str]) -> Optional[str]:
        """Check for real placeholders in implementation files, ignoring false positives."""

        documentation_extensions = ['md', 'txt', 'rst', 'adoc']
        documentation_names = ['README', 'CHANGELOG', 'CONTRIBUTING', 'LICENSE', 'IMPLEMENTATION_PLAN']

        for filename, content in files.items():
            # SKIP test files
            if 'test' in filename.lower() or '/tests/' in filename:
                continue

            path_obj = Path(filename)
            ext = path_obj.suffix.lstrip('.').lower()
            name = path_obj.stem.upper()

            # SKIP documentation files
            if ext in documentation_extensions or name in documentation_names:
                continue

            lang = 'all'
            if ext in ['html', 'htm']: lang = 'html'
            elif ext == 'py': lang = 'python'
            elif ext in ['js', 'jsx', 'ts', 'tsx']: lang = 'javascript'
            elif ext == 'css': lang = 'css'

            # 1. First, check and Remove ALLOWED patterns to avoid false positives
            clean_content = content
            if lang in self.ALLOWED_PATTERNS:
                for pattern in self.ALLOWED_PATTERNS[lang]:
                    clean_content = re.sub(pattern, "SAFE_CONTENT", clean_content, flags=re.IGNORECASE)

            # 2. Check for "..." or similar on its own line (Ellipsis)
            # Be careful with CSS ellipsis or Python ellipsis in arguments
            for line in clean_content.splitlines():
                stripped = line.strip()
                # Matches "...", "// ...", "# ...", "/* ... */", "<!-- ... -->"
                # Exclude markdown checkboxes [ ] or [x] which might be in strings or comments if not already cleaned
                if re.match(r'^(\.\.\.|# \.\.\.|\/\/ \.\.\.|\/\* \.\.\. \*\/|<!-- \.\.\. -->)$', stripped):
                    # Check if it's a false positive like Python def func(...):
                    if lang == 'python' and 'def ' in line:
                         continue
                    logger.debug(f"Placeholder detected in {filename}: {stripped}")
                    return filename

            # 3. Check for FORBIDDEN patterns in specific language
            forbidden = self.FORBIDDEN_PATTERNS.get(lang, []) + self.FORBIDDEN_PATTERNS.get('all', [])
            for pattern in forbidden:
                match = re.search(pattern, clean_content, re.IGNORECASE)
                if match:
                    # Special check for common TODO: to allow them if they were already whitelisted in step 1
                    # (but step 1 replaced them with SAFE_CONTENT)
                    logger.debug(f"Forbidden pattern '{pattern}' detected in {filename}: {match.group(0)}")
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

    def check_js_completeness(self, js: str) -> List[str]:
        """Valida que el JS tenga interactividad básica."""
        issues = []
        required = {
            'DOMContentLoaded': 'Missing DOMContentLoaded event listener',
            'addEventListener': 'Missing event listeners (interactivity)',
            'function': 'Missing functions',
        }
        for snippet, msg in required.items():
            if snippet not in js:
                issues.append(msg)
        return issues

    def check_css_completeness(self, css: str) -> List[str]:
        """Valida que el CSS tenga selectores y reglas reales."""
        issues = []

        if ':root' not in css:
            issues.append("Missing CSS variables in :root")
        if '@media' not in css:
            issues.append("Missing responsive breakpoints (@media)")

        # Buscar patrones de reglas CSS: selector { propiedad: valor; }
        rules = re.findall(r'[^{}]+\{[^{}]+\}', css)
        if len(rules) < 3:
            issues.append("CSS appears too simple or empty of actual rules")
        return issues

    def generate_feedback(self, issues: List[QualityIssue]) -> str:
        """Genera feedback estructurado para la IA."""
        if not issues:
            return ""

        feedback = "╔══════════════════════════════════════════════════════════╗\n"
        feedback += "║ ⚠️ QUALITY STANDARDS NOT MET (IMPLEMENTATION REJECTED)  ║\n"
        feedback += "╚══════════════════════════════════════════════════════════╝\n\n"
        feedback += "The following issues were found in your implementation:\n"
        feedback += "\n".join(str(issue) for issue in issues)
        feedback += "\n\nREQUIRED ACTION:\n"
        feedback += "1. RE-GENERATE the files with COMPLETE implementations. DO NOT TRUNCATE.\n"
        feedback += "2. REMOVE all placeholders like '...', '// rest of code', or 'TODO'.\n"
        feedback += "3. INCREASE CONTENT VOLUME significantly:\n"
        feedback += "   - HTML: Expand all sections (Navigation, Hero, Features, About, Portfolio, Contact, Footer).\n"
        feedback += "   - CSS: Add variables, layout rules, typography, responsive queries, and hover effects (min 200 lines).\n"
        feedback += "   - JS: Implement full interactivity, event listeners, and DOM manipulation (min 100 lines).\n"
        feedback += "\nYOUR RESPONSE MUST BE PRODUCTION-READY."

        return feedback
