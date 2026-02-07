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
            if not self.storage.exists(self.metrics_path):
                self._init_metrics()
            content = self.storage.read(self.metrics_path)
            metrics = json.loads(content)
            return self._ensure_metrics_structure(metrics)
        except Exception as e:
            logger.error(f"Failed to load metrics: {e}")
            return self._ensure_metrics_structure({})

    def _ensure_metrics_structure(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures that the metrics dictionary has all required keys safely."""
        if not isinstance(metrics, dict):
            metrics = {}

        metrics.setdefault("schema_version", self.schema_version)

        # Robustly ensure tdd_loop is a dict
        if "tdd_loop" not in metrics or not isinstance(metrics["tdd_loop"], dict):
            metrics["tdd_loop"] = {}
        tdd = metrics["tdd_loop"]

        tdd.setdefault("total_iterations", 0)

        # Robustly ensure phase_breakdown is a dict
        if "phase_breakdown" not in tdd or not isinstance(tdd["phase_breakdown"], dict):
            tdd["phase_breakdown"] = {}
        pb = tdd["phase_breakdown"]

        pb.setdefault("red_cycles", 0)
        pb.setdefault("green_cycles", 0)
        pb.setdefault("refactor_cycles", 0)

        if "auto_fixes" not in tdd or not isinstance(tdd["auto_fixes"], list):
            tdd["auto_fixes"] = []

        if "pattern_recognition" not in tdd or not isinstance(tdd["pattern_recognition"], dict):
            tdd["pattern_recognition"] = {}
        pr = tdd["pattern_recognition"]

        pr.setdefault("common_failures", [])
        pr.setdefault("common_solutions", [])

        if "quality_progress" not in metrics or not isinstance(metrics["quality_progress"], dict):
            metrics["quality_progress"] = {}

        metrics.setdefault("last_updated", datetime.now().isoformat())
        return metrics

    def update(self, data: Dict[str, Any]):
        """Update metrics with new data."""
        metrics = self._load_metrics()

        # Merge logic here
        if "iteration_increment" in data:
            metrics["tdd_loop"]["total_iterations"] += 1

        if "phase" in data:
            phase = str(data["phase"]).lower()
            # pb is already ensured to be a dict by _ensure_metrics_structure in _load_metrics
            pb = metrics["tdd_loop"]["phase_breakdown"]
            if phase == "red":
                pb["red_cycles"] = pb.get("red_cycles", 0) + 1
            elif phase == "green":
                pb["green_cycles"] = pb.get("green_cycles", 0) + 1
            elif phase == "refactor":
                pb["refactor_cycles"] = pb.get("refactor_cycles", 0) + 1

        if "auto_fix" in data:
            metrics["tdd_loop"]["auto_fixes"].append(data["auto_fix"])

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
        # Pull data with safe fallbacks
        tech_stack = iteration_data.get('tech_stack') or "unknown"
        quality_bar = iteration_data.get('quality_standards') or "standard"
        iterations = iteration_data.get('iterations', 0)
        auto_deps = iteration_data.get('auto_detected', [])
        phase = iteration_data.get('phase', 'UNKNOWN')
        active_test = iteration_data.get('active_test', 'none')
        failure_pattern = iteration_data.get('failure_pattern', 'none')

        # Pull patterns from metrics if available
        metrics = iteration_data.get('metrics', {})
        tdd_loop = metrics.get('tdd_loop', {})
        patterns = tdd_loop.get('pattern_recognition', {})
        successful_fixes = patterns.get('common_solutions', [])

        warnings = iteration_data.get('warnings') or ["None"]
        if isinstance(warnings, list):
            warnings_str = "\n- ".join(str(w) for w in warnings)
        else:
            warnings_str = str(warnings)

        context = [
            "# 🧠 Active Development Context",
            f"\n## 🏗️ Architecture Snapshot",
            f"- Tech Stack: {tech_stack}",
            f"- Quality Bar: {quality_bar}",

            f"\n## 📊 Performance Insights",
            f"- Plan iterations: {iterations}",
            f"- Auto-detected deps: {auto_deps}",

            f"\n## 🔄 TDD Phase Context",
            f"### Current: {phase}",
            f"- Active test: {active_test}",
            f"- Failure pattern: {failure_pattern}",

            f"\n## 💡 Learned Patterns",
            f"- Successful fixes: {successful_fixes[:5]}",

            f"\n## 🚨 Active Warnings",
            f"- {warnings_str}"
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
