import sqlite3
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from src.utils.event_system import EventSystem, Events

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
        self.event_system = EventSystem.get_instance()
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
                title TEXT,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                description TEXT NOT NULL,
                task TEXT,
                stack_trace TEXT,
                commit_sha TEXT,
                files_affected TEXT,
                context TEXT,
                auto_fixed BOOLEAN DEFAULT 0,
                suggestions TEXT,
                created_at DATETIME NOT NULL,
                resolved_at DATETIME,
                resolution TEXT,
                prevention TEXT
            )
        ''')

        # Migrations: Add new columns if they don't exist
        columns = [
            ("title", "TEXT"),
            ("context", "TEXT"),
            ("auto_fixed", "BOOLEAN DEFAULT 0"),
            ("suggestions", "TEXT")
        ]

        for col_name, col_type in columns:
            try:
                cursor.execute(f"ALTER TABLE issues ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError:
                # Column already exists
                pass

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
                     commit_sha: str = None, files_affected: List[str] = None,
                     title: str = None, context: Dict = None, auto_fixed: bool = False,
                     suggestions: List[str] = None) -> int:
        """Creates a new issue in the system with validation and defaults."""

        # 1. Validate & default TITLE
        if not title or not isinstance(title, str) or title.strip() == "":
            import logging
            logging.warning("Issue created with empty/invalid title, defaulting to 'Untitled Issue'")
            title = "Untitled Issue"
        title = str(title).strip()[:255]

        # 2. Validate & default CATEGORY
        valid_categories = [self.CAT_GIT, self.CAT_TESTING, self.CAT_QUALITY,
                           self.CAT_DEPENDENCIES, self.CAT_SECURITY, self.CAT_AI, "General", "FileStructure"]
        if not category or category not in valid_categories:
            import logging
            logging.warning(f"Invalid category '{category}', defaulting to 'General'")
            category = "General"

        # 3. Validate & default PRIORITY
        valid_priorities = [self.PRIO_CRITICAL, self.PRIO_HIGH, self.PRIO_MEDIUM, self.PRIO_LOW]
        if not priority or priority not in valid_priorities:
            import logging
            logging.warning(f"Invalid priority '{priority}', defaulting to 'Medium'")
            priority = self.PRIO_MEDIUM

        # 4. Validate & default DESCRIPTION
        if not description or not isinstance(description, str):
            description = "No description provided"
        description = str(description).strip()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        files_json = json.dumps(files_affected) if files_affected else "[]"
        suggestions_json = json.dumps(suggestions) if suggestions else "[]"

        # Merge existing fields into context for backwards compatibility
        full_context = context.copy() if context else {}
        if task: full_context['task'] = task
        if stack_trace: full_context['stack_trace'] = stack_trace
        if commit_sha: full_context['commit_sha'] = commit_sha
        if files_affected: full_context['files_affected'] = files_affected

        context_json = json.dumps(full_context)
        now = datetime.now().isoformat()
        status = 'Auto-Fixed' if auto_fixed else 'Open'

        cursor.execute('''
            INSERT INTO issues (title, category, priority, status, description, task,
                                stack_trace, commit_sha, files_affected, context,
                                auto_fixed, suggestions, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, category, priority, status, description, task,
              stack_trace, commit_sha, files_json, context_json,
              1 if auto_fixed else 0, suggestions_json, now))

        issue_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Publish update for UI
        import logging
        logging.info(f"✅ Issue #{issue_id} created: [{category}] {title}")
        self._notify_ui_update()

        return issue_id

    def get_issues(self, status: str = None) -> List[Dict[str, Any]]:
        """Retrieves issues filtered by status."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if status:
            cursor.execute("SELECT * FROM issues WHERE status = ?", (status,))
        else:
            cursor.execute("SELECT * FROM issues")

        results = [dict(row) for row in cursor.fetchall()]

        # Parse JSON fields
        for res in results:
            if res.get('files_affected'):
                try: res['files_affected'] = json.loads(res['files_affected'])
                except: res['files_affected'] = []
            if res.get('context'):
                try: res['context'] = json.loads(res['context'])
                except: res['context'] = {}
            if res.get('suggestions'):
                try: res['suggestions'] = json.loads(res['suggestions'])
                except: res['suggestions'] = []
            res['auto_fixed'] = bool(res.get('auto_fixed'))

        conn.close()
        return results

    def resolve_issue(self, issue_id: int, resolution: str, prevention: str = None):
        """Resolves a specific issue by ID."""
        self.update_issue(issue_id, 'Resolved', resolution, prevention)

    def add_suggestions(self, issue_id: int, suggestions: List[str]):
        """Adds or updates suggestions for an existing issue."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        suggestions_json = json.dumps(suggestions)

        cursor.execute('''
            UPDATE issues
            SET suggestions = ?
            WHERE id = ?
        ''', (suggestions_json, issue_id))

        conn.commit()
        conn.close()
        self._notify_ui_update()

    def get_suggestions(self, title: str) -> List[str]:
        """Returns resolution suggestions based on similar resolved issues."""
        similar = self.get_similar_issues(title)
        return [f"{issue['description']}: {issue['resolution']}" for issue in similar]

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

        # Publish update for UI
        self._notify_ui_update()

    def _notify_ui_update(self):
        """Fetch current issues and notify UI."""
        all_issues = self.get_issues()
        open_issues = [i for i in all_issues if i['status'] == 'Open']

        stats = {
            'critical': len([i for i in open_issues if i['priority'] == 'Critical']),
            'warning': len([i for i in open_issues if i['priority'] == 'High' or i['priority'] == 'Medium']),
            'resolved': len([i for i in all_issues if i['status'] == 'Resolved'])
        }

        self.event_system.publish("update_issue_counts", stats)
        self.event_system.publish("update_active_issues", open_issues)

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
            WHERE status = 'Resolved' AND (description LIKE ? OR category LIKE ? OR title LIKE ?)
            ORDER BY resolved_at DESC LIMIT 5
        ''', (search_term, search_term, search_term))

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
