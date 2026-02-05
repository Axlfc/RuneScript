import sqlite3
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

class IssueManager:
    """
    Intelligent Issue Management System for nIA.
    Handles auto-detection, tracking, and documentation of blocking errors.
    """

    # Categories
    CAT_GIT = "Git"
    CAT_TESTING = "Testing"
    CAT_QUALITY = "Quality"
    CAT_DEPENDENCIES = "Dependencies"
    CAT_SECURITY = "Security"
    CAT_AI = "AI"

    # Priorities
    PRIO_CRITICAL = "Critical"
    PRIO_HIGH = "High"
    PRIO_MEDIUM = "Medium"
    PRIO_LOW = "Low"

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.nia_dir = self.project_path / ".nia"
        self.db_path = self.nia_dir / "issues.db"
        self.wiki_dir = self.nia_dir / "wiki"

        # Ensure directories exist
        self.nia_dir.mkdir(parents=True, exist_ok=True)
        self.wiki_dir.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _init_db(self):
        """Initializes the SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Table for issues
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                description TEXT NOT NULL,
                task TEXT,
                stack_trace TEXT,
                commit_sha TEXT,
                files_affected TEXT,
                created_at DATETIME NOT NULL,
                resolved_at DATETIME,
                resolution TEXT,
                prevention TEXT
            )
        ''')

        # Table for resolution attempts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_id INTEGER NOT NULL,
                timestamp DATETIME NOT NULL,
                solution TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                FOREIGN KEY (issue_id) REFERENCES issues (id)
            )
        ''')

        conn.commit()
        conn.close()

    def resolve_issues_by_task(self, task_description: str, resolution: str, prevention: str = None):
        """Resolves all open issues related to a specific task."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        resolved_at = datetime.now().isoformat()

        cursor.execute('''
            UPDATE issues
            SET status = 'Resolved', resolution = ?, prevention = ?, resolved_at = ?
            WHERE task = ? AND status = 'Open'
        ''', (resolution, prevention, resolved_at, task_description))

        conn.commit()
        conn.close()

    def create_issue(self, category: str, priority: str, description: str,
                     task: str = None, stack_trace: str = None,
                     commit_sha: str = None, files_affected: List[str] = None) -> int:
        """Creates a new issue in the system."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        files_json = json.dumps(files_affected) if files_affected else "[]"
        now = datetime.now().isoformat()

        cursor.execute('''
            INSERT INTO issues (category, priority, status, description, task,
                                stack_trace, commit_sha, files_affected, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (category, priority, 'Open', description, task,
              stack_trace, commit_sha, files_json, now))

        issue_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return issue_id

    def update_issue(self, issue_id: int, status: str, resolution: str = None, prevention: str = None):
        """Updates an existing issue."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        resolved_at = datetime.now().isoformat() if status == 'Resolved' else None

        cursor.execute('''
            UPDATE issues
            SET status = ?, resolution = ?, prevention = ?, resolved_at = COALESCE(?, resolved_at)
            WHERE id = ?
        ''', (status, resolution, prevention, resolved_at, issue_id))

        conn.commit()
        conn.close()

    def add_attempt(self, issue_id: int, solution: str, success: bool):
        """Adds a resolution attempt to an issue."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute('''
            INSERT INTO attempts (issue_id, timestamp, solution, success)
            VALUES (?, ?, ?, ?)
        ''', (issue_id, now, solution, success))

        conn.commit()
        conn.close()

    def get_similar_issues(self, description: str) -> List[Dict[str, Any]]:
        """Finds resolved issues with similar descriptions."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Simple LIKE search for now. Could be improved with FTS or embeddings.
        search_term = f"%{description[:30]}%"
        cursor.execute('''
            SELECT * FROM issues
            WHERE status = 'Resolved' AND (description LIKE ? OR category LIKE ?)
            ORDER BY resolved_at DESC LIMIT 5
        ''', (search_term, search_term))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def format_suggestions(self, similar_issues: List[Dict[str, Any]]) -> str:
        """Formats similar issues for AI feedback."""
        if not similar_issues:
            return ""

        feedback = "\n\n### SIMILAR RESOLVED ISSUES FOUND:\n"
        for issue in similar_issues:
            feedback += f"- **Issue #{issue['id']}**: {issue['description']}\n"
            feedback += f"  - Resolution: {issue['resolution']}\n"
            if issue['prevention']:
                feedback += f"  - Prevention: {issue['prevention']}\n"
        return feedback

    def generate_wiki(self):
        """Generates GitHub-style Wiki documentation."""
        self._generate_troubleshooting_guide()
        self._generate_changelog()

    def _generate_troubleshooting_guide(self):
        """Generates a Troubleshooting.md file."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM issues WHERE status = 'Resolved' ORDER BY category, created_at DESC")
        issues = cursor.fetchall()

        content = "# Troubleshooting Guide\n\n"
        content += "This guide contains patterns of common failures and their documented solutions.\n\n"

        current_category = None
        for issue in issues:
            if issue['category'] != current_category:
                current_category = issue['category']
                content += f"## {current_category}\n\n"

            content += f"### {issue['description']}\n"
            content += f"**Priority:** {issue['priority']}  \n"
            content += f"**Task:** {issue['task']}  \n\n"
            content += "#### Resolution\n"
            content += f"{issue['resolution']}\n\n"
            if issue['prevention']:
                content += "#### Prevention\n"
                content += f"{issue['prevention']}\n\n"
            content += "---\n\n"

        with open(self.wiki_dir / "Troubleshooting.md", "w", encoding='utf-8') as f:
            f.write(content)
        conn.close()

    def _generate_changelog(self):
        """Generates a Changelog.md based on resolved issues."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM issues WHERE status = 'Resolved' ORDER BY resolved_at DESC")
        issues = cursor.fetchall()

        content = "# Changelog (Auto-documented Fixes)\n\n"

        current_date = None
        for issue in issues:
            date = issue['resolved_at'].split('T')[0]
            if date != current_date:
                current_date = date
                content += f"## {current_date}\n\n"

            content += f"- **[{issue['category']}]** {issue['description']} (Issue #{issue['id']})\n"

        with open(self.wiki_dir / "Changelog.md", "w", encoding='utf-8') as f:
            f.write(content)
        conn.close()
