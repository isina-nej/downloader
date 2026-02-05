"""Rate limiting and throttling utilities."""

import asyncio
import time
from typing import Dict
from collections import defaultdict


class RateLimiter:
    """Simple in-memory rate limiter using sliding window."""

    def __init__(self, max_requests: int, window_seconds: int = 60):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in the window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)

    async def is_allowed(self, key: str) -> bool:
        """
        Check if a request is allowed for the given key.

        Args:
            key: Unique identifier (e.g., user_id)

        Returns:
            True if request is allowed, False otherwise
        """
        now = time.time()
        cutoff_time = now - self.window_seconds

        # Clean old requests
        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > cutoff_time]

        # Check if limit exceeded
        if len(self.requests[key]) >= self.max_requests:
            return False

        # Add new request
        self.requests[key].append(now)
        return True

    def get_remaining(self, key: str) -> int:
        """Get remaining requests for the key."""
        now = time.time()
        cutoff_time = now - self.window_seconds
        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > cutoff_time]
        return max(0, self.max_requests - len(self.requests[key]))

    def cleanup(self):
        """Remove expired entries."""
        now = time.time()
        cutoff_time = now - self.window_seconds
        for key in list(self.requests.keys()):
            self.requests[key] = [req_time for req_time in self.requests[key] if req_time > cutoff_time]
            if not self.requests[key]:
                del self.requests[key]


# Global rate limiter instance
rate_limiter = RateLimiter(
    max_requests=config.RATE_LIMIT_PER_MINUTE,
    window_seconds=60,
)

# Import at end to avoid circular dependency
from src.config import config
