import time
from src.utils.telemetry import RateLimitedTelemetry

def test_rate_limited_telemetry():
    events = []
    def callback(t, d):
        events.append((t, d))

    telemetry = RateLimitedTelemetry(callback, max_events_per_second=2)

    # Send 5 events quickly
    for i in range(5):
        telemetry.emit("test", i)

    # Should only have 2 (or 3 depending on timing, but definitely not 5)
    assert len(events) < 5
    assert len(events) >= 2
