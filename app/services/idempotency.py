"""
Idempotency service for preventing duplicate submissions.

Supports idempotency keys via header:
Idempotency-Key: <unique-key>

If the same key is used, returns the original response.
"""
import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from fastapi import Header, HTTPException, status

logger = logging.getLogger(__name__)


@dataclass
class IdempotencyEntry:
    """Stored idempotency entry."""
    response_data: Dict[str, Any]
    status_code: int
    created_at: float = field(default_factory=time.time)


class IdempotencyService:
    """
    In-memory idempotency service.

    For production, use Redis or similar persistent storage.
    """

    def __init__(self, ttl_seconds: int = 86400):  # 24 hours
        self._entries: Dict[str, IdempotencyEntry] = {}
        self.ttl_seconds = ttl_seconds

    def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        cutoff = time.time() - self.ttl_seconds
        self._entries = {
            k: v for k, v in self._entries.items()
            if v.created_at > cutoff
        }

    def get(self, key: str) -> Optional[IdempotencyEntry]:
        """Get entry by idempotency key."""
        self._cleanup_expired()
        return self._entries.get(key)

    def set(self, key: str, response_data: Dict[str, Any], status_code: int) -> None:
        """Store idempotency entry."""
        self._cleanup_expired()
        self._entries[key] = IdempotencyEntry(
            response_data=response_data,
            status_code=status_code,
        )

    def has(self, key: str) -> bool:
        """Check if key exists."""
        self._cleanup_expired()
        return key in self._entries


# Singleton instance
idempotency_service = IdempotencyService()


def get_idempotency_key(
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
) -> Optional[str]:
    """
    FastAPI dependency for extracting idempotency key from header.
    """
    if idempotency_key:
        # Validate key format (simple UUID-like check)
        if len(idempotency_key) < 8 or len(idempotency_key) > 256:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Idempotency-Key format (8-256 characters)"
            )
        return idempotency_key
    return None
