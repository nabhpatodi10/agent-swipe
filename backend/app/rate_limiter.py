from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
import time


class InMemoryRateLimiter:
    """Simple process-local limiter for MVP safety controls."""

    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        window_start = now - window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] < window_start:
                events.popleft()
            if len(events) >= limit:
                return False
            events.append(now)
            return True


rate_limiter = InMemoryRateLimiter()

