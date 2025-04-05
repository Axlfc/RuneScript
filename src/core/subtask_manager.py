import logging
from datetime import datetime
from typing import Dict, Optional, Any, List


class SubtaskManager:
    def __init__(self, state, log_fn):
        self.subtasks: Dict[str, Dict] = {}
        self.active_subtasks = set()
        self.subtask_dependencies: Dict[str, List[str]] = {}
        self.subtask_results: Dict[str, Any] = {}
        self.state = state
        self.log = log_fn

    def create_subtask(self, task_id: str, description: str, context=None, dependencies=None) -> str:
        if task_id in self.subtasks:
            logging.warning(f"Subtask {task_id} already exists, overwriting")

        self.subtasks[task_id] = {
            "description": description,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "context": context or {},
        }

        if dependencies:
            self.subtask_dependencies[task_id] = dependencies

        self.log(f"Created subtask: {task_id}")
        return task_id

    def start_subtask(self, task_id: str) -> bool:
        if task_id not in self.subtasks:
            logging.error(f"Cannot start unknown subtask: {task_id}")
            return False

        dependencies = self.subtask_dependencies.get(task_id, [])
        for dep_id in dependencies:
            if self.subtasks.get(dep_id, {}).get("status") != "completed":
                logging.info(f"Cannot start {task_id}, dependency {dep_id} is not completed")
                return False

        self.subtasks[task_id]["status"] = "in_progress"
        self.subtasks[task_id]["updated_at"] = datetime.now().isoformat()
        self.subtasks[task_id]["started_at"] = datetime.now().isoformat()
        self.active_subtasks.add(task_id)

        self.log(f"Started subtask: {task_id}")
        return True

    def complete_subtask(self, task_id: str, result=None) -> bool:
        if task_id not in self.subtasks:
            logging.error(f"Cannot complete unknown subtask: {task_id}")
            return False

        self.subtasks[task_id]["status"] = "completed"
        self.subtasks[task_id]["updated_at"] = datetime.now().isoformat()
        self.subtasks[task_id]["completed_at"] = datetime.now().isoformat()

        if result is not None:
            self.subtask_results[task_id] = result

        self.active_subtasks.discard(task_id)
        self.log(f"Completed subtask: {task_id}")
        self._check_dependent_tasks(task_id)

        return True

    def fail_subtask(self, task_id: str, error_message: str) -> bool:
        if task_id not in self.subtasks:
            logging.error(f"Cannot fail unknown subtask: {task_id}")
            return False

        self.subtasks[task_id]["status"] = "failed"
        self.subtasks[task_id]["updated_at"] = datetime.now().isoformat()
        self.subtasks[task_id]["error"] = error_message
        self.active_subtasks.discard(task_id)

        self.state.log_error(f"Subtask failed: {task_id} - {error_message}")
        return True

    def get_subtask_status(self, task_id: str) -> Optional[Dict]:
        return self.subtasks.get(task_id)

    def get_subtask_result(self, task_id: str) -> Any:
        return self.subtask_results.get(task_id)

    def _check_dependent_tasks(self, completed_task_id: str):
        for task_id, deps in self.subtask_dependencies.items():
            if completed_task_id in deps:
                if all(
                    self.subtasks.get(dep, {}).get("status") == "completed"
                    for dep in deps
                ) and self.subtasks[task_id]["status"] == "pending":
                    self.start_subtask(task_id)
