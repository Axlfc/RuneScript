from typing import Callable, Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class EventSystem:
    """
    A simple Pub/Sub event system to decouple UI components.
    """
    _instance = None
    _subscribers: Dict[str, List[Callable]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventSystem, cls).__new__(cls)
            cls._subscribers = {}
        return cls._instance

    @classmethod
    def get_instance(cls) -> 'EventSystem':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to an event."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)
            logger.debug(f"Subscribed to {event_type}: {callback.__name__ if hasattr(callback, '__name__') else callback}")

    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from an event."""
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)

    def publish(self, event_type: str, data: Any = None):
        """Publish an event to all subscribers."""
        if event_type in self._subscribers:
            logger.debug(f"Publishing event {event_type} with data: {data}")
            for callback in self._subscribers[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in subscriber for {event_type}: {e}", exc_info=True)

# Global events constants
class Events:
    ISSUE_CREATED = "issue_created"
    ISSUE_RESOLVED = "issue_resolved"
    PHASE_CHANGED = "phase_changed"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    LOG_MESSAGE = "log_message"
    FILE_MODIFIED = "file_modified"
    TEST_RESULTS = "test_results"
    TELEMETRY_UPDATE = "telemetry_update"
    UPDATE_TASKS = "update_tasks"
    UPDATE_ISSUE_COUNTS = "update_issue_counts"
    UPDATE_ACTIVE_ISSUES = "update_active_issues"
    OPEN_ISSUE_MANAGER = "open_issue_manager"
    APPLY_FIX = "apply_fix"
    TOGGLE_CONSOLE = "toggle_console"
    TOGGLE_RIGHT_PANEL = "toggle_right_panel"
    TOGGLE_LEFT_PANEL = "toggle_left_panel"
    TOGGLE_CONSOLE_EXPAND = "toggle_console_expand"
    OPEN_FILE = "open_file"
    MANUAL_FIX_ISSUE = "manual_fix_issue"
    SKIP_ISSUE = "skip_issue"
    IGNORE_ISSUE = "ignore_issue"
    UPDATE_METRICS = "update_metrics"
    AI_MESSAGE = "ai_message"
