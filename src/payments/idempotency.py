"""Idempotency key store to prevent duplicate payment processing.

Ensures that retried requests with the same idempotency key
return the same result without re-processing the payment.
"""

from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class IdempotencyEntry:
    """Stores the result of a processed request for idempotency.

    Attributes:
        key: The idempotency key.
        transaction_id: The resulting transaction ID.
        response: The cached response data.
        created_at: When the entry was created.
        expires_at: When the entry expires.
    """

    key: str
    transaction_id: str
    response: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(
        default_factory=lambda: datetime.utcnow() + timedelta(hours=24)
    )


class IdempotencyStore:
    """In-memory store for idempotency keys.

    Prevents duplicate payment processing by caching the results
    of previously processed requests, keyed by an idempotency key.

    Keys expire after a configurable TTL (default: 24 hours).
    """

    def __init__(self, ttl_hours: int = 24) -> None:
        self._store: dict[str, IdempotencyEntry] = {}
        self._ttl = timedelta(hours=ttl_hours)

    def get(self, key: str) -> Optional[IdempotencyEntry]:
        """Retrieve a cached result by idempotency key.

        Args:
            key: The idempotency key to look up.

        Returns:
            The cached entry if found and not expired, None otherwise.
        """
        entry = self._store.get(key)
        if entry is None:
            return None

        # Check expiration
        if datetime.utcnow() > entry.expires_at:
            del self._store[key]
            return None

        return entry

    def set(self, key: str, transaction_id: str, response: dict) -> IdempotencyEntry:
        """Store a result with an idempotency key.

        Args:
            key: The idempotency key.
            transaction_id: The transaction ID of the result.
            response: The response data to cache.

        Returns:
            The created IdempotencyEntry.
        """
        entry = IdempotencyEntry(
            key=key,
            transaction_id=transaction_id,
            response=response,
            expires_at=datetime.utcnow() + self._ttl,
        )
        self._store[key] = entry
        return entry

    def exists(self, key: str) -> bool:
        """Check if an idempotency key exists and is not expired.

        Args:
            key: The idempotency key to check.

        Returns:
            True if the key exists and has not expired.
        """
        return self.get(key) is not None

    def remove(self, key: str) -> bool:
        """Remove an idempotency key from the store.

        Args:
            key: The idempotency key to remove.

        Returns:
            True if the key was found and removed.
        """
        if key in self._store:
            del self._store[key]
            return True
        return False

    def cleanup_expired(self) -> int:
        """Remove all expired entries from the store.

        Returns:
            The number of entries removed.
        """
        now = datetime.utcnow()
        expired_keys = [
            key for key, entry in self._store.items() if now > entry.expires_at
        ]
        for key in expired_keys:
            del self._store[key]
        return len(expired_keys)

    @property
    def size(self) -> int:
        """Return the number of entries in the store."""
        return len(self._store)
