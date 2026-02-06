
import logging
import re
from typing import List, Optional

logger = logging.getLogger(__name__)

class PlanValidator:
    """
    Validates the integrity of IMPLEMENTATION_PLAN.md to prevent corruption.
    """

    FORBIDDEN_PATTERNS = [
        r"\.\.\.\[Rest of plan remains same\]\.\.\.",
        r"\.\.\.\[Resto del plan permanece igual\]\.\.\.",
        r"\[TODO\]",
        r"\[PLACEHOLDER\]",
        r"\.\.\.\s*$", # Truncation at the end
        r"^\s*\.\.\.",  # Truncation at the beginning
    ]

    def __init__(self, min_tasks: int = 5):
        self.min_tasks = min_tasks

    def validate(self, content: str, expected_phases: Optional[List[str]] = None) -> bool:
        """
        Performs multiple checks on the plan content.
        Returns True if valid, False otherwise.
        """
        if not content or len(content.strip()) < 100:
            logger.error("Plan validation failed: Content is too short or empty.")
            return False

        # 1. Check for forbidden patterns (placeholders)
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                logger.error(f"Plan validation failed: Forbidden pattern detected: {pattern}")
                return False

        # 2. Check task count
        # Support various markers: [ ], [x], [/], [?]
        task_markers = [r"\[ \]", r"\[x\]", r"\[/\]", r"\[\?\]"]
        task_count = 0
        for marker in task_markers:
            task_count += len(re.findall(marker, content))

        if task_count < self.min_tasks:
            logger.error(f"Plan validation failed: Task count ({task_count}) is below minimum ({self.min_tasks}).")
            return False

        # 3. Check for phases
        phases = re.findall(r"## PHASE \d+:", content, re.IGNORECASE)
        if not phases:
            # Try a more generic phase detection if the specific one fails
            phases = re.findall(r"^#+.*PHASE", content, re.IGNORECASE | re.MULTILINE)

        if not phases:
            logger.error("Plan validation failed: No phases detected.")
            return False

        # 4. Optional: Check for specific required phases if provided
        if expected_phases:
            for phase in expected_phases:
                if phase not in content:
                    logger.error(f"Plan validation failed: Missing required phase: {phase}")
                    return False

        # 5. Check for basic Markdown structure
        if not content.startswith("# "):
            logger.warning("Plan validation warning: Plan does not start with a H1 title.")

        logger.info(f"Plan validation successful. Detected {task_count} tasks and {len(phases)} phases.")
        return True

    @staticmethod
    def extract_phases(content: str) -> List[str]:
        """Extracts phase titles for future validation."""
        return re.findall(r"(## PHASE \d+:.*)", content, re.IGNORECASE)
