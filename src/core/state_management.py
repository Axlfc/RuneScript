from datetime import datetime
from typing import Optional
import logging
import os


class StateManagementSystem:
    def __init__(self, project_path):
        self.project_path = project_path  # Store project path
        self.state = {
            "tasks": [],
            "completed_tasks": [],
            "code_files": {},  # Dictionary to track file content
            "test_results": {},
            "errors": [],
            "dependencies": [],
            "last_updated": datetime.now().isoformat()
        }

        # Create observers list for real-time notification
        self.observers = []

        # Ensure project directory exists
        os.makedirs(project_path, exist_ok=True)

        # Create a visible TODO.md right away to show activity
        self._create_initial_todo()

    def register_observer(self, callback_fn):
        """Register a function to be called when state changes"""
        self.observers.append(callback_fn)

    def _notify_observers(self, event_type, data=None):
        """Notify all observers of state change"""
        for observer in self.observers:
            try:
                observer(event_type, data)
            except Exception as e:
                logging.error(f"Observer notification failed: {e}")

    def _create_initial_todo(self):
        """Create initial TODO.md to show system is active"""
        todo_content = "# Project Development TODO\n\n## Initialization\n- [x] System started\n- [ ] Analyzing requirements\n\n_Last updated: {}".format(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        todo_path = os.path.join(self.project_path, "TODO.md")
        with open(todo_path, 'w', encoding='utf-8') as f:
            f.write(todo_content)
        logging.info(f"Created initial TODO.md at {todo_path}")

    def log_task(self, task):
        """Add a task and update TODO.md"""
        self.state["tasks"].append(task)
        self.state["last_updated"] = datetime.now().isoformat()
        self._update_todo_file()
        self._notify_observers("task_added", task)

    def complete_task(self, task):
        """Mark task as completed and update TODO.md"""
        if task in self.state["tasks"]:
            self.state["tasks"].remove(task)
        self.state["completed_tasks"].append(task)
        self.state["last_updated"] = datetime.now().isoformat()
        self._update_todo_file()
        self._notify_observers("task_completed", task)

    def add_code_file(self, filename, content):
        """Add a code file to the state and write it to disk."""
        self.state["code_files"][filename] = content
        self.state["last_updated"] = datetime.now().isoformat()

        # Write the file to disk
        try:
            # Create necessary directories
            file_path = os.path.join(self.project_path, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Write the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logging.info(f"Successfully wrote file to disk: {filename}")
            self._notify_observers("file_created", filename)
        except Exception as e:
            error_msg = f"Failed to write file {filename} to disk: {e}"
            logging.error(error_msg)
            self.log_error(error_msg)

    def add_test_result(self, test_name, result):
        self.state["test_results"][test_name] = result
        self.state["last_updated"] = datetime.now().isoformat()
        self._notify_observers("test_result", (test_name, result))

    def log_error(self, error):
        self.state["errors"].append(str(error))
        self.state["last_updated"] = datetime.now().isoformat()
        self._notify_observers("error", error)

    def add_dependency(self, dependency):
        if dependency not in self.state["dependencies"]:
            self.state["dependencies"].append(dependency)
            self.state["last_updated"] = datetime.now().isoformat()
            self._notify_observers("dependency_added", dependency)

    def _update_todo_file(self):
        """Update the TODO.md file with current tasks"""
        todo_path = os.path.join(self.project_path, "TODO.md")

        # Build content
        content = "# Project Development TODO\n\n"

        # Add active tasks
        if self.state["tasks"]:
            content += "## Active Tasks\n"
            for task in self.state["tasks"]:
                content += f"- [ ] {task}\n"
            content += "\n"

        # Add completed tasks
        if self.state["completed_tasks"]:
            content += "## Completed\n"
            for task in self.state["completed_tasks"]:
                content += f"- [x] {task}\n"
            content += "\n"

        # Add errors if any
        if self.state["errors"]:
            content += "## Issues\n"
            for error in self.state["errors"][-5:]:  # Show only last 5 errors
                content += f"- âš ï¸ {error}\n"
            content += "\n"

        # Add timestamp
        content += f"\n_Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"

        try:
            with open(todo_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logging.error(f"Failed to update TODO.md: {e}")

    def export_state(self, path: Optional[str] = None, keep_versions: int = 10):
        """
        Export the current state to a versioned file.

        Args:
            path (str): Optional custom path. If not provided, uses default inside project_path.
            keep_versions (int): How many historical versions to retain.
        """
        import json
        from glob import glob

        try:
            if not path:
                state_dir = self.project_path
                base_name = "project_state"
                versioned_files = sorted(
                    glob(os.path.join(state_dir, f"{base_name}_v*.json")),
                    key=lambda x: os.path.getmtime(x)
                )

                next_version = len(versioned_files) + 1
                versioned_filename = os.path.join(state_dir, f"{base_name}_v{next_version}.json")
                latest_path = os.path.join(state_dir, f"{base_name}_latest.json")

            else:
                versioned_filename = path
                latest_path = os.path.join(self.project_path, "project_state_latest.json")

            # Save new version
            with open(versioned_filename, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=4)

            # Save a convenient "latest" copy
            with open(latest_path, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=4)

            logging.info(f"State exported to: {versioned_filename}")
            self._notify_observers("state_exported", versioned_filename)

            # Clean up old versions
            if not path:
                versioned_files = sorted(
                    glob(os.path.join(state_dir, f"{base_name}_v*.json")),
                    key=lambda x: os.path.getmtime(x)
                )
                while len(versioned_files) > keep_versions:
                    oldest = versioned_files.pop(0)
                    os.remove(oldest)
                    logging.info(f"Deleted old checkpoint: {oldest}")

        except Exception as e:
            logging.error(f"Failed to export state: {e}")

    def load_state(self, path):
        import json
        with open(path, 'r', encoding='utf-8') as f:
            self.state = json.load(f)
        self._notify_observers("state_loaded", path)

