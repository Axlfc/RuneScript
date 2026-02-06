import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from .storage import StorageProvider

logger = logging.getLogger(__name__)

class NIAMetricsManager:
    """Manages project metrics with schema versioning and size limits."""

    def __init__(self, storage: StorageProvider, metrics_path: str, max_size_bytes: int = 1048576):
        self.storage = storage
        self.metrics_path = metrics_path
        self.max_size_bytes = max_size_bytes
        self.schema_version = "1.0.0"
        self._init_metrics()

    def _init_metrics(self):
        if not self.storage.exists(self.metrics_path):
            metrics = {
                "schema_version": self.schema_version,
                "tdd_loop": {
                    "total_iterations": 0,
                    "phase_breakdown": {
                        "red_cycles": 0,
                        "green_cycles": 0,
                        "refactor_cycles": 0
                    },
                    "auto_fixes": [],
                    "pattern_recognition": {
                        "common_failures": [],
                        "common_solutions": []
                    }
                },
                "quality_progress": {},
                "last_updated": datetime.now().isoformat()
            }
            self.storage.write_atomic(self.metrics_path, json.dumps(metrics, indent=2))

    def _load_metrics(self) -> Dict[str, Any]:
        try:
            content = self.storage.read(self.metrics_path)
            return json.loads(content)
        except Exception as e:
            logger.error(f"Failed to load metrics: {e}")
            # Return basic structure if loading fails
            return {"schema_version": self.schema_version, "tdd_loop": {}}

    def update(self, data: Dict[str, Any]):
        """Update metrics with new data."""
        metrics = self._load_metrics()

        # Merge logic here
        if "iteration_increment" in data:
            metrics["tdd_loop"]["total_iterations"] = metrics["tdd_loop"].get("total_iterations", 0) + 1

        if "phase" in data:
            phase = data["phase"].lower()
            if phase == "red":
                metrics["tdd_loop"]["phase_breakdown"]["red_cycles"] += 1
            elif phase == "green":
                metrics["tdd_loop"]["phase_breakdown"]["green_cycles"] += 1
            elif phase == "refactor":
                metrics["tdd_loop"]["phase_breakdown"]["refactor_cycles"] += 1

        if "auto_fix" in data:
            metrics["tdd_loop"].setdefault("auto_fixes", []).append(data["auto_fix"])

        if "quality_update" in data:
            metrics["quality_progress"].update(data["quality_update"])

        metrics["last_updated"] = datetime.now().isoformat()

        # Validate size before writing
        json_content = json.dumps(metrics, indent=2)
        if len(json_content.encode('utf-8')) > self.max_size_bytes:
            logger.warning("Metrics file exceeding max size, pruning auto_fixes...")
            if len(metrics["tdd_loop"].get("auto_fixes", [])) > 10:
                metrics["tdd_loop"]["auto_fixes"] = metrics["tdd_loop"]["auto_fixes"][-10:]
            json_content = json.dumps(metrics, indent=2)

        self.storage.write_atomic(self.metrics_path, json_content)

    def get_metrics(self) -> Dict[str, Any]:
        return self._load_metrics()

class RAMContextManager:
    """Manages the active development context (RAM) file."""

    def __init__(self, storage: StorageProvider, ram_path: str, max_size_kb: int = 100):
        self.storage = storage
        self.ram_path = ram_path
        self.max_size_kb = max_size_kb

    def refresh(self, iteration_data: Dict[str, Any]):
        """Regenerates the RAM context file based on latest data."""
        # In a real implementation, this would pull from metrics, config, and current state
        # For now, we'll implement a basic structure

        context = [
            "# 🧠 Active Development Context",
            f"\n## 🏗️ Architecture Snapshot",
            f"- Tech Stack: {iteration_data.get('tech_stack', 'unknown')}",
            f"- Quality Bar: {iteration_data.get('quality_standards', 'standard')}",

            f"\n## 📊 Performance Insights",
            f"- Plan iterations: {iteration_data.get('iterations', 0)}",
            f"- Auto-detected deps: {iteration_data.get('auto_detected', [])}",

            f"\n## 🔄 TDD Phase Context",
            f"### Current: {iteration_data.get('phase', 'UNKNOWN')}",
            f"- Active test: {iteration_data.get('active_test', 'none')}",
            f"- Failure pattern: {iteration_data.get('failure_pattern', 'none')}",

            f"\n## 💡 Learned Patterns",
            f"- Successful fixes: {iteration_data.get('successful_fixes', [])[:5]}",

            f"\n## 🚨 Active Warnings",
            f"- {iteration_data.get('warnings', ['None'])}"
        ]

        content = "\n".join(context)

        # Pruning logic if needed (e.g. if content too long)
        if len(content.encode('utf-8')) > self.max_size_kb * 1024:
            content = content[:self.max_size_kb * 1024]

        self.storage.write_atomic(self.ram_path, content)

    def get_sanitized_content(self) -> str:
        if self.storage.exists(self.ram_path):
            return self.storage.read(self.ram_path)
        return "No active context available."
