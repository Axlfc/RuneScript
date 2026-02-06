import os
import yaml
import logging
from pathlib import Path
from typing import Optional
from .schemas import AppConfig
from .defaults import DEFAULT_CONFIG

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages application configuration with validation and fallbacks."""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path("config")
        self.config = self._load_and_validate()

    def _load_and_validate(self) -> AppConfig:
        config_data = {}

        # 1. Load from environment variable if set
        env_path = os.getenv("JULES_CONFIG_PATH")
        if env_path:
            config_data = self._load_yaml(Path(env_path))

        # 2. Load from default config directory
        elif self.config_dir.exists():
            for yaml_file in self.config_dir.glob("*.yaml"):
                section_name = yaml_file.stem
                section_data = self._load_yaml(yaml_file)
                if section_data:
                    config_data[section_name] = section_data

        # 3. Validate and merge with defaults
        try:
            # We merge the loaded dict with DEFAULT_CONFIG's dict
            # For simplicity in this implementation, we just pass the dict to AppConfig
            # Pydantic will handle the validation and use defaults for missing fields
            return AppConfig(**config_data)
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}. Using defaults.")
            return DEFAULT_CONFIG

    def _load_yaml(self, path: Path) -> dict:
        if not path.exists():
            return {}
        try:
            with path.open('r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load config from {path}: {e}")
            return {}

    def get_security_config(self):
        return self.config.security

    def get_intelligence_config(self):
        return self.config.intelligence

    def get_feedback_config(self):
        return self.config.feedback
