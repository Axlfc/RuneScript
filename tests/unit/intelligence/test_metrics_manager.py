import json
import pytest
from pathlib import Path
from src.core.storage import FileSystemStorage
from src.core.context_intelligence import NIAMetricsManager

def test_metrics_manager_init(tmp_path):
    storage = FileSystemStorage(tmp_path)
    metrics_path = "metrics.json"
    manager = NIAMetricsManager(storage, metrics_path)

    assert storage.exists(metrics_path)
    metrics = manager.get_metrics()
    assert metrics["schema_version"] == "1.0.0"
    assert "tdd_loop" in metrics

def test_metrics_manager_update(tmp_path):
    storage = FileSystemStorage(tmp_path)
    metrics_path = "metrics.json"
    manager = NIAMetricsManager(storage, metrics_path)

    manager.update({"iteration_increment": True, "phase": "RED"})
    metrics = manager.get_metrics()
    assert metrics["tdd_loop"]["total_iterations"] == 1
    assert metrics["tdd_loop"]["phase_breakdown"]["red_cycles"] == 1
