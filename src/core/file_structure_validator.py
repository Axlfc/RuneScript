import re
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

class FileStructureValidator:
    """
    Valida i auto-corregeix estructures de fitxers segons tech_stack.

    If no tech_stack is provided, it defaults to 'frontend_web'.
    """

    STRUCTURE_RULES = {
        "frontend_web": {
            "html": r"^(?!project/|src/|public/|assets/).*\.html$",  # Root level only, NO subdirectories including assets/
            "css": r"^css/.*\.css$",
            "js": r"^js/.*\.js$",
            "assets": r"^assets/.*"
        }
    }

    COMMON_PREFIXES_TO_STRIP = ["project/", "src/", "public/", "./"]

    def __init__(self, issue_manager=None):
        self.issue_manager = issue_manager

    def validate_and_fix(self, files: List[Dict], tech_stack: Optional[str] = None) -> Tuple[List[Dict], List[str]]:
        """
        Valida fitxers i intenta auto-corregir paths incorrectes.

        Returns:
            (fixed_files, warnings)
        """
        if not tech_stack:
            logger.warning("No tech_stack specified, defaulting to 'frontend_web'")
            tech_stack = "frontend_web"

        fixed_files = []
        warnings = []

        for file_info in files:
            original_path = file_info['path']
            fixed_path = self._auto_fix_path(original_path, tech_stack)

            if fixed_path != original_path:
                warning = f"Auto-fixed path: {original_path} → {fixed_path}"
                warnings.append(warning)

                # Crear issue si tenim IssueManager
                if self.issue_manager:
                    self.issue_manager.create_issue(
                        title=f"Invalid file path auto-corrected: {original_path}",
                        category="FileStructure",
                        priority="Medium",
                        description=f"LLM generated invalid path for {tech_stack}",
                        context={
                            "original_path": original_path,
                            "fixed_path": fixed_path,
                            "tech_stack": tech_stack
                        },
                        auto_fixed=True
                    )

            file_info['path'] = fixed_path
            fixed_files.append(file_info)

        return fixed_files, warnings

    def is_valid(self, path: str, tech_stack: str) -> bool:
        """Comprova si un path és vàlid per al tech_stack donat"""
        if tech_stack not in self.STRUCTURE_RULES:
            return True

        rules = self.STRUCTURE_RULES[tech_stack]

        if path.endswith('.html'):
            return bool(re.match(rules['html'], path))
        elif path.endswith('.css'):
            return bool(re.match(rules['css'], path))
        elif path.endswith('.js'):
            return bool(re.match(rules['js'], path))
        elif path.startswith('assets/'):
            return bool(re.match(rules['assets'], path))

        # Per defecte permetem fitxers a root que no siguin els anteriors (ex: README, package.json)
        if '/' not in path:
            return True

        return False

    def _auto_fix_path(self, path: str, tech_stack: str) -> str:
        """Intenta corregir automàticament paths comuns incorrectes"""
        # Strip common wrong prefixes
        for prefix in self.COMMON_PREFIXES_TO_STRIP:
            if path.startswith(prefix):
                path = path[len(prefix):]

        # Validar segons tech_stack
        if tech_stack == "frontend_web":
            # Assegurar que CSS va a css/
            if path.endswith('.css') and not path.startswith('css/'):
                path = f"css/{path}"

            # Assegurar que JS va a js/
            if path.endswith('.js') and not path.startswith('js/'):
                path = f"js/{path}"

            # Assegurar que HTML va a root (si estava en algun subfolder que hem stripat o si l'AI ho ha posat malament)
            if path.endswith('.html'):
                # Si encara té '/' vol dir que està en un subdir no stripat
                if '/' in path:
                    path = path.split('/')[-1]

        return path

    def generate_structure_guide(self, tech_stack: str) -> str:
        """Genera una guia clara d'estructura per incluir en prompts"""
        guides = {
            "frontend_web": """
## CRITICAL: Frontend Web Structure Rules

✅ CORRECT paths (use EXACTLY these):
- index.html (root level, NO subdirectories)
- css/style.css
- css/animations.css (any CSS file)
- js/app.js
- js/utils.js (any JS file)
- assets/img/photo.jpg
- assets/fonts/custom.ttf

❌ INVALID paths (will be AUTO-CORRECTED or REJECTED):
- project/index.html → Fixed to: index.html
- src/index.html → Fixed to: index.html
- public/index.html → Fixed to: index.html
- assets/index.html → Fixed to: index.html
- ./css/style.css → Fixed to: css/style.css
- style.css → Fixed to: css/style.css
- app.js → Fixed to: js/app.js

IMPORTANT:
1. HTML files ALWAYS at root level (no subdirs)
2. CSS files ALWAYS in css/ directory
3. JS files ALWAYS in js/ directory
4. Assets ALWAYS in assets/ subdirectories
"""
        }
        return guides.get(tech_stack, "")
