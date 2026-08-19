# services/rate_limiter.py — Sliding Window Rate Limiter

import time
import threading
from typing import Dict, List, Tuple


class RateLimiter:
    """Thread-safe in-memory sliding window rate limiter."""

    def __init__(self, default_limit: int = 10, window_seconds: int = 60):
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}
        self.lock = threading.Lock()

    def is_allowed(self, key: str, limit: int = None) -> Tuple[bool, int]:
        """
        Checks if request for key is allowed under sliding window limit.
        Returns: (is_allowed: bool, retry_after_seconds: int)
        """
        now = time.time()
        max_limit = limit if limit is not None else self.default_limit
        window_start = now - self.window_seconds

        with self.lock:
            if key not in self.requests:
                self.requests[key] = []

            # Filter out timestamps outside the sliding window
            self.requests[key] = [ts for ts in self.requests[key] if ts > window_start]

            if len(self.requests[key]) >= max_limit:
                oldest_timestamp = self.requests[key][0]
                retry_after = max(1, int(oldest_timestamp + self.window_seconds - now))
                return False, retry_after

            # Record this request
            self.requests[key].append(now)
            return True, 0

    def reset(self):
        """Clears all rate limit state (useful for tests)."""
        with self.lock:
            self.requests.clear()
