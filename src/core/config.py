from pydantic import BaseModel, Field
from pathlib import Path
from typing import Optional
import yaml

class Config(BaseModel):
    """nIA configuration."""

    max_iterations: int = Field(
        default=20,
        description="Maximum loop iterations (20 for testing, 50 for overnight)"
    )

    cost_limit: Optional[float] = Field(
        default=None,
        description="Max cost in USD (None = unlimited)"
    )

    sandbox_enabled: bool = Field(
        default=True,
        description="Run in isolated directory"
    )

    auto_commit: bool = Field(
        default=True,
        description="Automatically commit completed tasks"
    )

    @classmethod
    def load(cls, path: Path = Path(".rgr/config.yaml")):
        """Load config from file or use defaults."""
        if not path.exists():
            # Create default config and save it if possible
            config = cls()
            try:
                config.save(path)
            except Exception:
                # If we can't save (e.g. read-only filesystem), just return defaults
                pass
            return config

        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return cls(**data)

    def save(self, path: Path):
        """Save config to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)
