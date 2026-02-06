from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class SecurityConfig(BaseModel):
    safe_packages: List[str] = Field(default_factory=lambda: [
        "selenium", "beautifulsoup4", "lxml", "pytest", "requests", "pillow"
    ])
    package_name_pattern: str = r"^[a-z0-9][a-z0-9._-]*$"
    max_package_name_length: int = 100
    pip_install_timeout: int = 30
    regex_timeout: int = 1
    audit_log_path: str = ".nia/security_audit.log"
    max_log_bytes: int = 10485760 # 10MB
    backup_count: int = 7

class IntelligenceConfig(BaseModel):
    ram_context_path: str = ".nia/ram_context.md"
    metrics_path: str = "nia_metrics.json"
    patterns_path: str = ".nia/patterns.json"
    max_ram_size_kb: int = 100
    max_metrics_size_bytes: int = 1048576 # 1MB
    max_patterns: int = 100
    schema_version: str = "1.0.0"

class FeedbackConfig(BaseModel):
    telemetry_enabled: bool = True
    max_events_per_second: int = 10

class AppConfig(BaseModel):
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    intelligence: IntelligenceConfig = Field(default_factory=IntelligenceConfig)
    feedback: FeedbackConfig = Field(default_factory=FeedbackConfig)
