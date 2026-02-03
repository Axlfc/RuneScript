import os
import json
import shutil
import git
import tarfile
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class ProjectReconstructor:
    """
    Rebuilds a project by applying patches in chronological order.
    Also handles history exports and reports.
    """

    def __init__(self, project_path: str):
        self.project_path = os.path.abspath(project_path)
        self.nia_dir = os.path.join(self.project_path, '.nia')
        self.patches_dir = os.path.join(self.nia_dir, 'patches')
        self.manifest_path = os.path.join(self.nia_dir, 'manifest.json')

    def rebuild_from_patches(self, output_path: str) -> bool:
        """
        Creates a new directory and applies all patches from the manifest.
        """
        if not os.path.exists(self.manifest_path):
            logger.error(f"Manifest not found at {self.manifest_path}")
            return False

        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        if os.path.exists(output_path):
            shutil.rmtree(output_path)

        os.makedirs(output_path)
        repo = git.Repo.init(output_path)

        # Configure a default user for reconstruction commits
        with repo.config_writer() as cw:
            cw.set_value("user", "name", "nIA Reconstructor")
            cw.set_value("user", "email", "nia@reconstructor.local")

        print(f"🏗️ Rebuilding project: {manifest.get('project_name', 'Unknown')}")
        print(f"📦 Total patches to apply: {len(manifest['patches'])}")

        for patch_info in manifest['patches']:
            patch_file = os.path.join(self.patches_dir, patch_info['patch_file'])

            if not os.path.exists(patch_file):
                print(f"❌ Patch file missing: {patch_info['patch_file']}")
                return False

            print(f"[{patch_info['sequence']}/{len(manifest['patches'])}] Applying: {patch_info['task']}")

            try:
                # Apply patch using git apply
                repo.git.apply(patch_file)

                # Commit the changes
                repo.git.add(A=True)
                repo.index.commit(f"✅ {patch_info['task']} (original: {patch_info['commit'][:7]})")

            except Exception as e:
                print(f"❌ Error applying patch {patch_info['patch_file']}: {e}")
                return False

        print(f"\n✅ Project successfully rebuilt at: {output_path}")
        return True

    def export_history(self, output_filename: str = 'project_history.tar.gz') -> str:
        """
        Compresses the .nia directory into a tar.gz file.
        """
        output_path = os.path.join(self.project_path, output_filename)
        with tarfile.open(output_path, "w:gz") as tar:
            tar.add(self.nia_dir, arcname='.nia')

        return output_path

    def generate_html_report(self) -> str:
        """
        Generates a visual HTML report of the build history.
        """
        if not os.path.exists(self.manifest_path):
            return ""

        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>nIA Project History: {project_name}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 20px; background-color: #f4f7f6; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .summary {{ background: #fff; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .patch-card {{ background: #fff; border-left: 5px solid #2ecc71; padding: 15px; margin-bottom: 15px; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: transform 0.2s; }}
        .patch-card:hover {{ transform: translateX(5px); }}
        .patch-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
        .patch-title {{ font-weight: bold; font-size: 1.1em; color: #2c3e50; }}
        .patch-seq {{ background: #2ecc71; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; }}
        .patch-meta {{ font-size: 0.85em; color: #7f8c8d; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-top: 10px; }}
        .stat-item {{ background: #ecf0f1; padding: 8px; border-radius: 4px; text-align: center; }}
        .stat-value {{ display: block; font-weight: bold; font-size: 1.2em; color: #2980b9; }}
        .stat-label {{ font-size: 0.75em; color: #7f8c8d; text-transform: uppercase; }}
    </style>
</head>
<body>
    <h1>🏗️ {project_name} - Build History</h1>

    <div class="summary">
        <h2>Project Summary</h2>
        <div class="stats-grid">
            <div class="stat-item"><span class="stat-value">{total_patches}</span><span class="stat-label">Patches</span></div>
            <div class="stat-item"><span class="stat-value">{total_files}</span><span class="stat-label">Total Files</span></div>
            <div class="stat-item"><span class="stat-value">{total_lines}</span><span class="stat-label">Total Lines Activity</span></div>
            <div class="stat-item"><span class="stat-value">{success_rate}%</span><span class="stat-label">Success Rate</span></div>
        </div>
        <p class="patch-meta">Created: {created_at} | Last Updated: {last_updated}</p>
    </div>

    <h2>Sequence of Changes</h2>
    {patches_html}
</body>
</html>
"""
        patch_template = """
    <div class="patch-card">
        <div class="patch-header">
            <span class="patch-title">{task}</span>
            <span class="patch-seq">#{sequence}</span>
        </div>
        <div class="patch-meta">
            <span>📅 {timestamp}</span> |
            <span>🆔 Commit: <code>{commit_short}</code></span> |
            <span>📄 {files_changed} files</span> |
            <span>📏 {lines_changed} lines</span>
        </div>
    </div>
"""

        patches_html = ""
        for p in manifest['patches']:
            patches_html += patch_template.format(
                task=p['task'],
                sequence=p['sequence'],
                timestamp=p['timestamp'],
                commit_short=p['commit'][:7],
                files_changed=p['files_changed'],
                lines_changed=p['lines_changed']
            )

        stats = manifest.get('project_stats', {})
        total_iterations = stats.get('successful_iterations', 0) + stats.get('failed_iterations', 0)
        success_rate = (stats.get('successful_iterations', 0) / total_iterations * 100) if total_iterations > 0 else 100

        full_html = html_template.format(
            project_name=manifest.get('project_name', 'Unnamed Project'),
            total_patches=manifest.get('total_patches', 0),
            total_files=stats.get('total_files', 0),
            total_lines=stats.get('total_lines', 0),
            success_rate=round(success_rate, 1),
            created_at=manifest.get('created_at', 'N/A'),
            last_updated=manifest.get('last_updated', 'N/A'),
            patches_html=patches_html
        )

        report_path = os.path.join(self.nia_dir, 'history_report.html')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(full_html)

        return report_path
