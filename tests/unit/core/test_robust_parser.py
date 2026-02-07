import pytest
from src.core.robust_parser import RobustJSONParser

def test_extract_json():
    data = RobustJSONParser.extract_json('{"a": 1}')
    assert data["a"] == 1
