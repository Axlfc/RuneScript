from pathlib import Path
from .plan_parser import Task, PlanParser
import logging

logger = logging.getLogger(__name__)

class TaskTracker:
    """Update IMPLEMENTATION_PLAN.md with task progress."""

    def validate_integrity(self, content: str) -> bool:
        """Verify the plan is not truncated and has basic markers."""
        if not content or len(content) < 50:
            return False

        # Check for truncation markers if any (e.g. from AI)
        if "... (rest" in content or "(rest of the plan remains the same)" in content:
            return False

        # Must have phases
        if "## PHASE" not in content.upper():
            return False

        # Must have some task markers
        task_markers = ['[ ]', '[x]', '[/]', '[?]']
        if not any(marker in content for marker in task_markers):
            return False

        return True

    def mark_completed(self, plan_path: Path, task: Task):
        """Mark task as [x] completed."""
        try:
            content = plan_path.read_text(encoding='utf-8')
            lines = content.split('\n')

            # Find and update the line
            updated = False
            for i, line in enumerate(lines):
                if i + 1 == task.line_number:
                    # Ensure we only replace the checkbox
                    if '[ ]' in line:
                        lines[i] = line.replace('[ ]', '[x]', 1)
                        updated = True
                    break

            if not updated:
                logger.warning(f"Could not find pending task at line {task.line_number}")

            # Update progress section if it exists
            new_content = '\n'.join(lines)
            updated_content = self._update_counters(new_content)

            if self.validate_integrity(updated_content):
                plan_path.write_text(updated_content, encoding='utf-8')
                logger.info(f"Marked task as completed: {task.description}")
            else:
                logger.error("Integrity check failed before writing IMPLEMENTATION_PLAN.md. Aborting write.")
                raise ValueError("Plan integrity check failed")
        except Exception as e:
            logger.error(f"Error marking task complete: {e}")
            raise

    def mark_blocked(self, plan_path: Path, task: Task, reason: str):
        """Mark task as [?] blocked with reason."""
        try:
            content = plan_path.read_text(encoding='utf-8')
            lines = content.split('\n')

            updated = False
            for i, line in enumerate(lines):
                if i + 1 == task.line_number:
                    if '[ ]' in line:
                        lines[i] = line.replace('[ ]', f'[?] BLOCKED: {reason}', 1)
                        updated = True
                    elif '[?]' in line:
                        # Already blocked, maybe update reason?
                        if 'BLOCKED:' not in line:
                            lines[i] = line.replace('[?]', f'[?] BLOCKED: {reason}', 1)
                        updated = True
                    break

            if not updated:
                logger.warning(f"Could not find pending task at line {task.line_number}")

            new_content = '\n'.join(lines)
            updated_content = self._update_counters(new_content)

            if self.validate_integrity(updated_content):
                plan_path.write_text(updated_content, encoding='utf-8')
                logger.info(f"Marked task as blocked: {task.description} - {reason}")
            else:
                logger.error("Integrity check failed before writing IMPLEMENTATION_PLAN.md. Aborting write.")
                raise ValueError("Plan integrity check failed")
        except Exception as e:
            logger.error(f"Error marking task blocked: {e}")
            raise

    def _update_counters(self, content: str) -> str:
        """Dynamically update the counters in the Progress section."""
        try:
            # We can parse the content without a real file if we modify PlanParser
            # but for now let's use a temporary path or just a simple regex approach
            # Actually, let's just use a temporary file for now as it's already there
            # but more safely.
            import tempfile
            import os

            fd, temp_path_str = tempfile.mkstemp()
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as tmp:
                    tmp.write(content)

                parser = PlanParser()
                tasks = parser.parse(Path(temp_path_str))
                stats = parser.get_statistics(tasks)
            finally:
                os.remove(temp_path_str)

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
        except Exception as e:
            logger.error(f"Error updating counters: {e}")
            return content
