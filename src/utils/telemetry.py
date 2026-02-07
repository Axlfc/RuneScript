import time
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

class RateLimitedTelemetry:
    """Manages telemetry events with rate limiting to prevent flooding."""

    def __init__(self, callback: Callable[[str, Any], None], max_events_per_second: int = 10):
        self.callback = callback
        self.max_events_per_second = max_events_per_second
        self.tokens = float(max_events_per_second)
        self.last_update = time.monotonic()

    def _consume_token(self) -> bool:
        now = time.monotonic()
        delta = now - self.last_update
        self.tokens = min(float(self.max_events_per_second), self.tokens + delta * self.max_events_per_second)
        self.last_update = now

        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False

    def emit(self, event_type: str, data: Any):
        if self._consume_token():
            try:
                self.callback(event_type, data)
            except Exception as e:
                logger.error(f"Error emitting telemetry {event_type}: {e}")
        else:
            logger.debug(f"Telemetry {event_type} dropped due to rate limit.")
