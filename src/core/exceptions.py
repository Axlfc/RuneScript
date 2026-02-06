
class nIAException(Exception):
    """Base exception for nIA system."""
    pass

class QuotaExhaustedError(nIAException):
    """Raised when LLM API quota is exhausted."""
    def __init__(self, message: str, retry_after: str = "unknown"):
        super().__init__(message)
        self.retry_after = retry_after

class ParsingError(nIAException):
    """Raised when LLM response parsing fails."""
    pass
