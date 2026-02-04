import logging
import json
import os
import hashlib
from datetime import datetime
from pathlib import Path

class SecurityAuditor:
    """Comprehensive security event logging for nIA."""

    def __init__(self, log_dir=None):
        if log_dir is None:
            # Default to a .nia/security directory in the current working directory
            # or use a system-wide one if appropriate.
            # In this environment, /home/claude/.nia/security is good.
            log_dir = os.path.join(os.path.expanduser("~"), ".nia", "security")

        self.log_dir = Path(log_dir)
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # If we can't create the log dir, we might have to log to stderr or a temp dir
            import sys
            print(f"CRITICAL: Failed to create security log directory {log_dir}: {e}", file=sys.stderr)
            self.log_dir = Path("/tmp/nia-security")
            self.log_dir.mkdir(parents=True, exist_ok=True)

        self.loggers = {
            'file_access': self._setup_logger('file_access'),
            'code_execution': self._setup_logger('code_execution'),
            'security_violations': self._setup_logger('security_violations'),
            'package_install': self._setup_logger('package_install'),
        }

    def _setup_logger(self, name):
        logger = logging.getLogger(f'nia.security.{name}')
        logger.setLevel(logging.INFO)
        # Prevent propagation to root logger to avoid double logging
        logger.propagate = False

        log_file = self.log_dir / f'{name}.jsonl'
        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)
        return logger

    def _log_event(self, logger_name, event_type, **kwargs):
        event = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'event_type': event_type,
            **kwargs
        }
        self.loggers[logger_name].info(json.dumps(event))

        # If it's a critical security violation, also print to stderr for immediate visibility
        if logger_name == 'security_violations' and kwargs.get('severity') == 'CRITICAL':
            import sys
            print(f"\n🚨 SECURITY ALERT [{kwargs.get('category')}]: {kwargs.get('description')}", file=sys.stderr)

    def log_file_access(self, operation, path, approved, **kwargs):
        self._log_event('file_access', 'file_access',
                        operation=operation,
                        path=str(path),
                        approved=approved,
                        path_hash=hashlib.sha256(str(path).encode()).hexdigest(),
                        **kwargs)

    def log_code_execution(self, code, source, approved, result=None, **kwargs):
        self._log_event('code_execution', 'code_execution',
                        source=source,
                        approved=approved,
                        code_hash=hashlib.sha256(code.encode()).hexdigest(),
                        code_length=len(code),
                        result=result,
                        **kwargs)

    def log_security_violation(self, severity, category, description, **kwargs):
        self._log_event('security_violations', 'security_violation',
                        severity=severity,
                        category=category,
                        description=description,
                        **kwargs)

    def log_package_install(self, package, version, approved, **kwargs):
        self._log_event('package_install', 'package_install',
                        package=package,
                        version=version,
                        approved=approved,
                        **kwargs)
