import json
import pytest
from pathlib import Path
from src.core.storage import FileSystemStorage
from src.core.context_intelligence import NIAMetricsManager, RAMContextManager

def test_metrics_manager_robustness(tmp_path):
    storage = FileSystemStorage(tmp_path)
    metrics_path = "metrics_broken.json"

    # Create a corrupted/incomplete metrics file
    corrupted_data = {
        "tdd_loop": None, # This should be a dict
        "quality_progress": "not a dict" # This should be a dict
    }
    storage.write(metrics_path, json.dumps(corrupted_data))

    manager = NIAMetricsManager(storage, metrics_path)

    # This should not raise an error and should fix the structure
    manager.update({"iteration_increment": True})

    metrics = manager.get_metrics()
    assert isinstance(metrics["tdd_loop"], dict)
    assert metrics["tdd_loop"]["total_iterations"] == 1
    assert isinstance(metrics["quality_progress"], dict)

def test_ram_manager_partial_data(tmp_path):
    storage = FileSystemStorage(tmp_path)
    ram_path = "ram.md"
    manager = RAMContextManager(storage, ram_path)

    # Test with very partial data
    manager.refresh({"phase": "RED"})
    content = manager.get_sanitized_content()
    assert "Current: RED" in content
    assert "Tech Stack: unknown" in content
