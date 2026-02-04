class SecurityException(Exception):
    """Base class for all security-related exceptions."""
    def __init__(self, message, category=None, severity='HIGH', **kwargs):
        super().__init__(message)
        self.category = category
        self.severity = severity
        self.details = kwargs

class PathValidationError(SecurityException):
    """Raised when a path fails validation."""
    def __init__(self, message, path=None, **kwargs):
        super().__init__(message, category='PATH_VALIDATION', path=path, **kwargs)

class CodeAnalysisError(SecurityException):
    """Raised when code fails security analysis."""
    def __init__(self, message, threats=None, **kwargs):
        super().__init__(message, category='CODE_ANALYSIS', threats=threats, **kwargs)

class SandboxExecutionError(SecurityException):
    """Raised when an error occurs during sandbox execution."""
    def __init__(self, message, **kwargs):
        super().__init__(message, category='SANDBOX_EXECUTION', **kwargs)

class PackageValidationError(SecurityException):
    """Raised when a package fails validation."""
    def __init__(self, message, package=None, version=None, **kwargs):
        super().__init__(message, category='PACKAGE_VALIDATION', package=package, version=version, **kwargs)

class AuditLogError(SecurityException):
    """Raised when an error occurs during audit logging."""
    def __init__(self, message, **kwargs):
        super().__init__(message, category='AUDIT_LOGGING', severity='MEDIUM', **kwargs)
