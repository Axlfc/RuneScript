
import logging
import shutil
import re
from pathlib import Path
from typing import List, Optional, Dict
from .plan_validator import PlanValidator
from .task_tracker import PlanVersionControl

logger = logging.getLogger(__name__)

class PlanRecovery:
    """
    Tools for recovering a corrupted IMPLEMENTATION_PLAN.md.
    """
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.plan_path = self.project_path / "IMPLEMENTATION_PLAN.md"
        self.validator = PlanValidator()
        self.pvc = PlanVersionControl(self.plan_path)

    def attempt_auto_repair(self) -> bool:
        """
        Tries to find the latest valid backup and restore it.
        """
        logger.info("🛠️ Attempting automatic plan repair from backups...")
        success = self.pvc.rollback_to_last_valid(self.validator)
        if success:
            logger.info("✅ Plan auto-repair successful.")
        else:
            logger.error("❌ Plan auto-repair failed: No valid backups found.")
        return success

    def list_backups(self) -> List[Dict]:
        """
        Returns a list of available backups with status info.
        """
        backup_info = []
        backups = sorted(self.pvc.backup_dir.glob("plan_*.md"), reverse=True)

        for b in backups:
            try:
                content = b.read_text(encoding='utf-8')
                valid = self.validator.validate(content)

                completed = len(re.findall(r"\[x\]", content))
                pending = len(re.findall(r"\[ \]", content))
                blocked = len(re.findall(r"\[\?\]", content))

                backup_info.append({
                    "filename": b.name,
                    "path": str(b),
                    "timestamp": b.stem.replace("plan_", ""),
                    "is_valid": valid,
                    "stats": {
                        "completed": completed,
                        "pending": pending,
                        "blocked": blocked,
                        "total": completed + pending + blocked
                    }
                })
            except Exception as e:
                logger.warning(f"Could not process backup {b.name}: {e}")

        return backup_info

    def recover_from_backup(self, backup_filename: str) -> bool:
        """
        Restores a specific backup by filename.
        """
        backup_path = self.pvc.backup_dir / backup_filename
        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_filename}")
            return False

        try:
            shutil.copy(backup_path, self.plan_path)
            logger.info(f"✅ Successfully restored plan from {backup_filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore backup {backup_filename}: {e}")
            return False
