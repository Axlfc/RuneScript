import json
import os
from src.security.audit import SecurityAuditor

def test_security_auditor_rotation(tmp_path):
    # Small max_bytes to trigger rotation quickly
    auditor = SecurityAuditor(log_dir=tmp_path, max_bytes=100, backup_count=2)

    # Log enough events to trigger rotation
    for i in range(10):
        auditor.log_security_violation("MEDIUM", "TEST", f"Test message {i}")

    # Check if multiple files exist
    log_files = list(tmp_path.glob("security_violations.jsonl*"))
    assert len(log_files) > 1
