from pydantic import BaseModel
from pathlib import Path
from typing import Literal, List
import re

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
        if not plan_path.exists():
            return []

        tasks = []
        content = plan_path.read_text()
        current_phase = "Unknown"

        for line_num, line in enumerate(content.split('\n'), 1):
            line = line.strip()
            # Detect phase headers
            if line.startswith('## PHASE'):
                current_phase = line.replace('## PHASE', '').strip()
                continue

            # Parse task
            if line.startswith('- [ ]'):
                tasks.append(Task(
                    status="pending",
                    description=line.replace('- [ ]', '').strip(),
                    phase=current_phase,
                    line_number=line_num
                ))
            elif line.startswith('- [x]'):
                tasks.append(Task(
                    status="completed",
                    description=line.replace('- [x]', '').strip(),
                    phase=current_phase,
                    line_number=line_num
                ))
            elif line.startswith('- [?]'):
                tasks.append(Task(
                    status="blocked",
                    description=line.replace('- [?]', '').strip(),
                    phase=current_phase,
                    line_number=line_num
                ))

        return tasks

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
