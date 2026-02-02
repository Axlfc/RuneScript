from pydantic import BaseModel
from pathlib import Path
from typing import Literal, List
import re
import logging
from src.utils.path_utils import clean_filename, clean_markdown

logger = logging.getLogger(__name__)

class Task(BaseModel):
    """Represents a single task in the implementation plan."""
    status: Literal["pending", "completed", "blocked"]
    description: str
    phase: str
    line_number: int

class PlanParser:
    """Parse and manipulate IMPLEMENTATION_PLAN.md files."""

    def parse(self, plan_path: Path) -> List[Task]:
        """
        Parse plan file into list of tasks.

        Format:
        - [ ] Task description  → pending
        - [x] Task description  → completed
        - [?] Task description  → blocked
        """
        try:
            if not plan_path.exists():
                logger.error(f"Plan file not found: {plan_path}")
                return []

            content = plan_path.read_text(encoding='utf-8')
            if not content.strip():
                logger.warning("Plan file is empty")
                return []

            tasks = []
            current_phase = "Unknown"

            for line_num, line in enumerate(content.split('\n'), 1):
                # Detect phase headers
                if line.startswith('## PHASE'):
                    current_phase = line.replace('## PHASE', '').strip()
                    continue

                # Parse task
                if '- [ ]' in line:
                    tasks.append(Task(
                        status="pending",
                        description=clean_markdown(line.replace('- [ ]', '').strip()),
                        phase=current_phase,
                        line_number=line_num
                    ))
                elif '- [x]' in line:
                    tasks.append(Task(
                        status="completed",
                        description=clean_markdown(line.replace('- [x]', '').strip()),
                        phase=current_phase,
                        line_number=line_num
                    ))
                elif '- [?]' in line:
                    tasks.append(Task(
                        status="blocked",
                        description=clean_markdown(line.replace('- [?]', '').strip()),
                        phase=current_phase,
                        line_number=line_num
                    ))

            return tasks
        except Exception as e:
            logger.error(f"Error parsing plan: {e}")
            return []

    def find_next_pending(self, tasks: List[Task]) -> Task | None:
        """Return first pending task or None if all complete."""
        for task in tasks:
            if task.status == "pending":
                return task
        return None

    def get_statistics(self, tasks: List[Task]) -> dict:
        """Calculate progress statistics."""
        total = len(tasks)
        completed = len([t for t in tasks if t.status == "completed"])
        blocked = len([t for t in tasks if t.status == "blocked"])
        remaining = total - completed - blocked

        return {
            "total": total,
            "completed": completed,
            "blocked": blocked,
            "remaining": remaining,
            "percent": (completed / total * 100) if total > 0 else 0
        }
