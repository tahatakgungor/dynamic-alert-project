from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from threading import Lock
import time


@dataclass(slots=True)
class RateLimitResult:
    allowed: bool
    retry_after_seconds: int


class FixedWindowRateLimiter:
    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = {}
        self._lock = Lock()

    def check(self, key: str, *, limit: int, window_seconds: int) -> RateLimitResult:
        now = time.time()
        window_start = now - float(window_seconds)
        with self._lock:
            queue = self._events.setdefault(key, deque())
            while queue and queue[0] < window_start:
                queue.popleft()
            if len(queue) >= limit:
                retry_after = max(1, int(queue[0] + window_seconds - now))
                return RateLimitResult(allowed=False, retry_after_seconds=retry_after)
            queue.append(now)
            return RateLimitResult(allowed=True, retry_after_seconds=0)


edge_endpoint_limiter = FixedWindowRateLimiter()
