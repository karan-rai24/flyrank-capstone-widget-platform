"""
Rate limiting service for API endpoints.

Uses in-memory storage for simplicity.
For production, use Redis or similar.
"""
import time
import logging
from typing import Optional, Dict, Tuple
from collections import defaultdict
from dataclasses import dataclass, field
from fastapi import Request, HTTPException, status

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    max_requests: int = 10  # Maximum requests
    window_seconds: int = 60  # Time window in seconds


@dataclass
class RateLimitEntry:
    """Rate limit entry for tracking requests."""
    timestamps: list = field(default_factory=list)


class RateLimitService:
    """
    In-memory rate limiting service.

    Tracks requests by IP address and/or widget ID.
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self._requests: Dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)

    def _cleanup_old_entries(self, key: str) -> None:
        """Remove entries outside the time window."""
        cutoff = time.time() - self.config.window_seconds
        self._requests[key].timestamps = [
            ts for ts in self._requests[key].timestamps
            if ts > cutoff
        ]

    def check_rate_limit(self, key: str) -> bool:
        """
        Check if request is allowed under rate limit.
        Returns True if allowed, False if rate limited.
        """
        self._cleanup_old_entries(key)

        if len(self._requests[key].timestamps) >= self.config.max_requests:
            return False

        return True

    def record_request(self, key: str) -> None:
        """Record a request timestamp."""
        self._requests[key].timestamps.append(time.time())

    def get_remaining(self, key: str) -> int:
        """Get remaining requests in current window."""
        self._cleanup_old_entries(key)
        return max(0, self.config.max_requests - len(self._requests[key].timestamps))

    def get_reset_time(self, key: str) -> Optional[float]:
        """Get time until rate limit resets."""
        self._cleanup_old_entries(key)
        if not self._requests[key].timestamps:
            return None
        oldest = min(self._requests[key].timestamps)
        reset_time = oldest + self.config.window_seconds - time.time()
        return max(0, reset_time)


class RateLimitMiddleware:
    """
    FastAPI middleware for rate limiting.

    Usage:
        app.add_middleware(RateLimitMiddleware, config=RateLimitConfig(max_requests=10))
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self.service = RateLimitService(config)

    async def __call__(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Create rate limit key (IP-based)
        key = f"ip:{client_ip}"

        # Check rate limit
        if not self.service.check_rate_limit(key):
            remaining = self.service.get_remaining(key)
            reset_time = self.service.get_reset_time(key)

            logger.warning(f"Rate limit exceeded for {client_ip}")

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={
                    "X-RateLimit-Limit": str(self.config.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_time or self.config.window_seconds)),
                    "Retry-After": str(int(reset_time or self.config.window_seconds)),
                }
            )

        # Record request
        self.service.record_request(key)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = self.service.get_remaining(key)
        response.headers["X-RateLimit-Limit"] = str(self.config.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response


# Singleton instances for different endpoints
submission_rate_limiter = RateLimitService(
    RateLimitConfig(max_requests=10, window_seconds=60)  # 10 per minute
)
