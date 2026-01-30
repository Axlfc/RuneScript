# tests/core/test_config.py
import pytest
from pathlib import Path
from src.core.config import Config
import yaml

def test_config_loads_defaults_when_file_missing(tmp_path, monkeypatch):
    """Config loads with defaults when file doesn't exist."""
    monkeypatch.chdir(tmp_path)

    # Use a non-existent path
    config_path = tmp_path / ".rgr" / "config.yaml"
    config = Config.load(config_path)

    assert config.max_iterations == 20
    assert config.cost_limit is None
    assert config.sandbox_enabled is True
    assert config.auto_commit is True

def test_config_creates_file_on_first_load(tmp_path, monkeypatch):
    """Config creates config file on first load."""
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / ".rgr" / "config.yaml"

    assert not config_path.exists()

    config = Config.load(config_path)

    assert config_path.exists()

def test_config_loads_from_existing_file(tmp_path, monkeypatch):
    """Config loads values from existing file."""
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / ".rgr" / "config.yaml"
    config_path.parent.mkdir(parents=True)

    config_path.write_text("""
max_iterations: 50
cost_limit: 100.0
sandbox_enabled: false
auto_commit: false
""")

    config = Config.load(config_path)

    assert config.max_iterations == 50
    assert config.cost_limit == 100.0
    assert config.sandbox_enabled is False
    assert config.auto_commit is False

def test_config_save_persists_changes(tmp_path, monkeypatch):
    """Config.save() persists changes to file."""
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / ".rgr" / "config.yaml"

    config = Config(max_iterations=100, cost_limit=50.0)
    config.save(config_path)

    # Load and verify
    with open(config_path) as f:
        data = yaml.safe_load(f)

    assert data['max_iterations'] == 100
    assert data['cost_limit'] == 50.0
