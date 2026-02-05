import os
import git
import json
import logging
try:
    from lib.git import git_icons
except ImportError:
    git_icons = {}
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class GitBasedFileManager:
    """
    Manages project files using Git as the source of truth for change detection.
    Implements a Patch System for physical, exportable history.
    """

    def __init__(self, project_path: str):
        self.project_path = os.path.abspath(project_path)
        try:
            self.repo = git.Repo(self.project_path)
        except git.InvalidGitRepositoryError:
            self.repo = git.Repo.init(self.project_path)

        self.nia_dir = os.path.join(self.project_path, '.nia')
        self.patches_dir = os.path.join(self.nia_dir, 'patches')
        self.diffs_dir = os.path.join(self.nia_dir, 'diffs')
        self.logs_dir = os.path.join(self.nia_dir, 'logs')
        self.manifest_path = os.path.join(self.nia_dir, 'manifest.json')

        # Create required directories
        os.makedirs(self.patches_dir, exist_ok=True)
        os.makedirs(self.diffs_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

        self._ensure_manifest_exists()
        self._ensure_gitignore()
        self.security_auditor = None

    def set_security_auditor(self, auditor):
        self.security_auditor = auditor

    def _ensure_gitignore(self):
        """Add .nia/security/ to .gitignore automatically."""
        gitignore_path = os.path.join(self.project_path, '.gitignore')

        required_entries = [
            '.nia/security/',
            '*.jsonl',
            '__pycache__/',
            '.venv/',
        ]

        content = ""
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                content = f.read()

        original_content = content
        for entry in required_entries:
            if entry not in content:
                if content and not content.endswith('\n'):
                    content += '\n'
                content += f'{entry}\n'

        if content != original_content:
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write(content)

    def _ensure_manifest_exists(self):
        """Initializes manifest.json if it doesn't exist."""
        if not os.path.exists(self.manifest_path):
            manifest = {
                "project_name": os.path.basename(self.project_path),
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "total_patches": 0,
                "patches": [],
                "project_stats": {
                    "total_files": 0,
                    "total_lines": 0,
                    "successful_iterations": 0,
                    "failed_iterations": 0
                }
            }
            self._save_manifest(manifest)

    def _load_manifest(self) -> Dict[str, Any]:
        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_manifest(self, manifest: Dict[str, Any]):
        with open(self.manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)

    def create_checkpoint(self, message: str = "Pre-LLM checkpoint") -> str:
        """
        Ensures current state is committed and returns the commit hash.
        """
        try:
            if self.repo.is_dirty(untracked_files=True):
                self.repo.git.add(A=True)
                commit = self.repo.index.commit(message)
                return commit.hexsha
            return self.repo.head.commit.hexsha
        except (git.BadName, git.InvalidGitRepositoryError):
            # Probably initial commit
            self.repo.git.add(A=True)
            commit = self.repo.index.commit("Initial commit")
            return commit.hexsha

    def get_changes_since(self, commit_sha: str) -> Dict[str, List[Any]]:
        """
        Detects exactly which files changed since commit_sha.
        """
        diff = self.repo.git.diff(commit_sha, '--name-status')

        changes = {
            'added': [],
            'modified': [],
            'deleted': [],
            'renamed': []
        }

        if not diff:
            return changes

        for line in diff.split('\n'):
            if not line:
                continue

            parts = line.split('\t')
            status = parts[0]

            if status == 'A':
                changes['added'].append(parts[1])
            elif status == 'M':
                changes['modified'].append(parts[1])
            elif status == 'D':
                changes['deleted'].append(parts[1])
            elif status.startswith('R'):
                changes['renamed'].append((parts[1], parts[2]))

        return changes

    def generate_patch(self, from_commit: str, task_description: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Generates a .patch and a .diff file for the changes since from_commit.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        task_slug = "".join(c if c.isalnum() else "-" for c in task_description.lower())[:50]

        base_name = f"{timestamp}_{task_slug}"
        patch_path = os.path.join(self.patches_dir, f"{base_name}.patch")
        diff_path = os.path.join(self.diffs_dir, f"{base_name}.diff")

        try:
            # Check if there are changes
            if from_commit == self.repo.head.commit.hexsha:
                logger.info("No changes since checkpoint - skipping patch generation")
                return None, None

            # Generate format-patch (contains commit metadata)
            # Use range from_commit..HEAD to capture all commits in between
            patch_content = self.repo.git.format_patch(f"{from_commit}..HEAD", '--stdout')

            if not patch_content:
                logger.info("No patch content generated.")
                return None, None

            with open(patch_path, 'w', encoding='utf-8') as f:
                f.write(patch_content)

            # Generate readable diff with stats
            diff_content = self.repo.git.diff(from_commit, 'HEAD', '--stat', '--patch')
            with open(diff_path, 'w', encoding='utf-8') as f:
                f.write(diff_content)

            return patch_path, diff_path
        except Exception as e:
            logger.error(f"Error generating patch: {e}")
            return None, None

    def _get_icon(self, key: str, default: str = "") -> str:
        return git_icons.get(key, default)

    def generate_patch_log(self, patch_path: str, task_description: str, changes: Dict[str, Any], validation_result: Any) -> str:
        """
        Creates a detailed JSON log for the patch.
        """
        patch_filename = os.path.basename(patch_path)
        log_filename = patch_filename.replace('.patch', '.json')
        log_path = os.path.join(self.logs_dir, log_filename)

        log_data = {
            'timestamp': datetime.now().isoformat(),
            'patch_file': patch_filename,
            'commit_hash': self.repo.head.commit.hexsha,
            'task_description': task_description,
            'changes': changes,
            'validation': {
                'is_valid': getattr(validation_result, 'success', True),
                'message': getattr(validation_result, 'message', ""),
                'errors': getattr(validation_result, 'errors', []),
                'warnings': getattr(validation_result, 'warnings', [])
            },
            'files_modified': len(changes.get('modified', [])),
            'files_added': len(changes.get('added', [])),
            'files_deleted': len(changes.get('deleted', [])),
            'total_lines_changed': self._count_lines_changed(changes)
        }

        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        return log_path

    def generate_error_log(self, task_description: str, phase: str, error_message: str, test_output: str, files_generated: List[str], attempt: int) -> str:
        """
        Generates a detailed error log in .nia/logs/
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        task_slug = "".join(c if c.isalnum() else "-" for c in task_description.lower())[:50]

        log_filename = f"{timestamp}_FAILED_{task_slug}.json"
        log_path = os.path.join(self.logs_dir, log_filename)

        log_data = {
            'timestamp': datetime.now().isoformat(),
            'task': task_description,
            'status': 'FAILED',
            'phase': phase,
            'error': error_message,
            'test_output': test_output,
            'files_generated': files_generated,
            'attempt': attempt,
            'commit_hash': self.repo.head.commit.hexsha if hasattr(self.repo.head, 'commit') else None
        }

        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        return log_path

    def update_manifest(self, patch_info: Dict[str, Any]):
        """Updates the master manifest with the new patch info."""
        manifest = self._load_manifest()

        manifest['patches'].append(patch_info)
        manifest['total_patches'] = len(manifest['patches'])
        manifest['last_updated'] = datetime.now().isoformat()

        # Update stats
        manifest['project_stats']['successful_iterations'] += 1
        manifest['project_stats']['total_files'] = self._count_total_files()

        lines_changed = patch_info.get('lines_changed', 0)
        manifest['project_stats']['total_lines'] += lines_changed

        self._save_manifest(manifest)

    def record_failed_iteration(self):
        """Increments the failed iterations counter in the manifest."""
        manifest = self._load_manifest()
        manifest['project_stats']['failed_iterations'] += 1
        manifest['last_updated'] = datetime.now().isoformat()
        self._save_manifest(manifest)

    def rollback_to(self, commit_sha: str) -> bool:
        """
        Safe rollback that works on Windows by closing handles and using fallback strategies.
        """
        import gc
        import time

        # 1. Close SecurityAuditor handles if available
        if self.security_auditor:
            try:
                self.security_auditor.close_handles()
            except Exception as e:
                logger.warning(f"Error closing security auditor handles: {e}")

        # 2. Force GC and wait
        gc.collect()
        time.sleep(0.5)

        try:
            # 3. Attempt hard reset
            self.repo.git.reset('--hard', commit_sha)
            self.repo.git.clean('-fd')
            return True
        except Exception as e:
            logger.warning(f"Git reset --hard failed: {e}. Attempting fallback to checkout...")
            try:
                # 4. Fallback to checkout --force
                self.repo.git.checkout(commit_sha, force=True)
                self.repo.git.clean('-fd')
                return True
            except Exception as e2:
                logger.error(f"Rollback failed completely: {e2}")
                return False

    def _count_lines_changed(self, changes: Dict[str, Any]) -> int:
        total = 0
        all_files = changes['added'] + changes['modified']
        for filepath in all_files:
            try:
                # Use git show to get stats of the last change for this file
                stat = self.repo.git.show('--numstat', 'HEAD', filepath)
                if stat:
                    # format: added \t deleted \t filename
                    lines = stat.split('\n')
                    for line in lines:
                        if line and '\t' in line:
                            parts = line.split('\t')
                            if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                                total += int(parts[0]) + int(parts[1])
            except Exception:
                pass
        return total

    def _count_total_files(self) -> int:
        count = 0
        for root, dirs, files in os.walk(self.project_path):
            if '.git' in dirs: dirs.remove('.git')
            if '.nia' in dirs: dirs.remove('.nia')
            count += len(files)
        return count
