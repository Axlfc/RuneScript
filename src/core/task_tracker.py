from pathlib import Path
from .plan_parser import Task, PlanParser

class TaskTracker:
    """Update IMPLEMENTATION_PLAN.md with task progress."""

    def mark_completed(self, plan_path: Path, task: Task):
        """Mark task as [x] completed."""
        content = plan_path.read_text()
        lines = content.split('\n')

        # Find and update the line
        for i, line in enumerate(lines):
            if i + 1 == task.line_number:
                # Ensure we only replace the checkbox
                if '[ ]' in line:
                    lines[i] = line.replace('[ ]', '[x]', 1)
                break

        # Update progress section if it exists
        new_content = '\n'.join(lines)
        updated_content = self._update_counters(new_content)

        plan_path.write_text(updated_content)

    def mark_blocked(self, plan_path: Path, task: Task, reason: str):
        """Mark task as [?] blocked with reason."""
        content = plan_path.read_text()
        lines = content.split('\n')

        for i, line in enumerate(lines):
            if i + 1 == task.line_number:
                if '[ ]' in line:
                    lines[i] = line.replace('[ ]', f'[?] BLOCKED: {reason}', 1)
                break

        new_content = '\n'.join(lines)
        updated_content = self._update_counters(new_content)

        plan_path.write_text(updated_content)

    def _update_counters(self, content: str) -> str:
        """Dynamically update the counters in the Progress section."""
        # Temporary file to use PlanParser
        temp_path = Path("temp_plan.md")
        temp_path.write_text(content)
        parser = PlanParser()
        tasks = parser.parse(temp_path)
        stats = parser.get_statistics(tasks)
        temp_path.unlink()

        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith("- Total Tasks:"):
                lines[i] = f"- Total Tasks: {stats['total']}"
            elif line.startswith("- Completed:"):
                lines[i] = f"- Completed: {stats['completed']}"
            elif line.startswith("- Remaining:"):
                lines[i] = f"- Remaining: {stats['remaining']}"
            elif line.startswith("- Blocked:"):
                lines[i] = f"- Blocked: {stats['blocked']}"

        return '\n'.join(lines)
