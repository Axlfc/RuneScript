import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from .storage import StorageProvider

logger = logging.getLogger(__name__)

class PatternTracker:
    """Tracks frequency of failures and successes to identify patterns."""

    def __init__(self, storage: StorageProvider, patterns_path: str, max_patterns: int = 100):
        self.storage = storage
        self.patterns_path = patterns_path
        self.max_patterns = max_patterns
        self._init_patterns()

    def _init_patterns(self):
        if not self.storage.exists(self.patterns_path):
            data = {
                "patterns": {},
                "last_updated": datetime.now().isoformat()
            }
            self.storage.write_atomic(self.patterns_path, json.dumps(data, indent=2))

    def _load_patterns(self) -> Dict[str, Any]:
        try:
            content = self.storage.read(self.patterns_path)
            return json.loads(content)
        except Exception as e:
            logger.error(f"Failed to load patterns: {e}")
            return {"patterns": {}}

    def analyze(self, iteration_data: Dict[str, Any]):
        """Analyzes iteration data to update pattern counts."""
        data = self._load_patterns()
        patterns = data.get("patterns", {})

        failure = iteration_data.get("failure_type")
        if failure:
            pattern_key = f"failure:{failure}"
            p = patterns.setdefault(pattern_key, {
                "count": 0,
                "last_seen": "",
                "solutions_attempted": [],
                "successful_solution": None
            })
            p["count"] += 1
            p["last_seen"] = datetime.now().isoformat()

            solution = iteration_data.get("solution_attempted")
            if solution and solution not in p["solutions_attempted"]:
                p["solutions_attempted"].append(solution)

            if iteration_data.get("success"):
                p["successful_solution"] = solution

        # Pruning: Keep only max_patterns by sorting by last_seen or count
        if len(patterns) > self.max_patterns:
            sorted_keys = sorted(patterns.keys(), key=lambda k: patterns[k].get("last_seen", ""), reverse=True)
            patterns = {k: patterns[k] for k in sorted_keys[:self.max_patterns]}

        data["patterns"] = patterns
        data["last_updated"] = datetime.now().isoformat()
        self.storage.write_atomic(self.patterns_path, json.dumps(data, indent=2))

    def get_top_patterns(self, limit: int = 5) -> List[Dict[str, Any]]:
        data = self._load_patterns()
        patterns = data.get("patterns", {})
        sorted_patterns = sorted(
            [{"name": k, **v} for k, v in patterns.items()],
            key=lambda x: x["count"],
            reverse=True
        )
        return sorted_patterns[:limit]
