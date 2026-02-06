import pytest
from src.core.storage import FileSystemStorage
from src.core.patterns import PatternTracker

def test_pattern_tracker_analyze(tmp_path):
    storage = FileSystemStorage(tmp_path)
    patterns_path = "patterns.json"
    tracker = PatternTracker(storage, patterns_path)

    tracker.analyze({"failure_type": "Responsive_CSS", "solution_attempted": "flexbox", "success": True})
    patterns = tracker.get_top_patterns()
    assert len(patterns) == 1
    assert patterns[0]["name"] == "failure:Responsive_CSS"
    assert patterns[0]["count"] == 1
    assert "flexbox" in patterns[0]["solutions_attempted"]
    assert patterns[0]["successful_solution"] == "flexbox"
