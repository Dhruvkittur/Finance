"""
FinPilot AI — Redis Client
===========================
Async Redis client wrapper with:
- Connection pooling
- Pub/Sub for real-time notifications
- Caching helpers
- Session storage
- Rate limiting support
"""

import json
import logging
from typing import Any, Optional, Union
from datetime import timedelta

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Async Redis client with helper methods for common operations.
    Wraps redis.asyncio for use throughout the application.
    """

    def __init__(self):
        self._client: Optional[Redis] = None
        self._pubsub_client: Optional[Redis] = None

    async def connect(self) -> None:
        """Initialize the Redis connection pool."""
        self._client = await redis.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=settings.REDIS_DECODE_RESPONSES,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
        # Separate client for pub/sub (cannot run commands while subscribed)
        self._pubsub_client = await redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
        logger.info("Redis connection pool initialized")

    async def disconnect(self) -> None:
        """Close the Redis connections."""
        if self._client:
            await self._client.aclose()
        if self._pubsub_client:
            await self._pubsub_client.aclose()
        logger.info("Redis connections closed")

    async def ping(self) -> bool:
        """Health check ping."""
        if self._client:
            return await self._client.ping()
        return False

    @property
    def client(self) -> Redis:
        if not self._client:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._client

    # ── Cache Operations ──────────────────────────────────────────────────────

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from Redis, auto-deserializing JSON."""
        value = await self.client.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None,
    ) -> bool:
        """
        Set a value in Redis with optional TTL.

        Args:
            key: Redis key
            value: Value to store (auto-serialized to JSON)
            ttl: Time-to-live in seconds or timedelta
        """
        if not isinstance(value, str):
            value = json.dumps(value, default=str)

        if isinstance(ttl, timedelta):
            ttl = int(ttl.total_seconds())

        if ttl:
            return await self.client.setex(key, ttl, value)
        return await self.client.set(key, value)

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys."""
        return await self.client.delete(*keys)

    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        return bool(await self.client.exists(key))

    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on an existing key."""
        return await self.client.expire(key, ttl)

    async def ttl(self, key: str) -> int:
        """Get remaining TTL of a key."""
        return await self.client.ttl(key)

    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment a counter."""
        return await self.client.incrby(key, amount)

    # ── Hash Operations ───────────────────────────────────────────────────────

    async def hset(self, key: str, mapping: dict) -> int:
        """Set multiple hash fields."""
        serialized = {
            k: json.dumps(v, default=str) if not isinstance(v, str) else v
            for k, v in mapping.items()
        }
        return await self.client.hset(key, mapping=serialized)

    async def hgetall(self, key: str) -> dict:
        """Get all hash fields."""
        data = await self.client.hgetall(key)
        result = {}
        for k, v in data.items():
            try:
                result[k] = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                result[k] = v
        return result

    # ── List Operations ───────────────────────────────────────────────────────

    async def lpush(self, key: str, *values: Any) -> int:
        """Push values to the left of a list."""
        serialized = [json.dumps(v, default=str) for v in values]
        return await self.client.lpush(key, *serialized)

    async def lrange(self, key: str, start: int = 0, end: int = -1) -> list:
        """Get range from list."""
        items = await self.client.lrange(key, start, end)
        result = []
        for item in items:
            try:
                result.append(json.loads(item))
            except (json.JSONDecodeError, TypeError):
                result.append(item)
        return result

    # ── Pub/Sub ───────────────────────────────────────────────────────────────

    async def publish(self, channel: str, message: Any) -> int:
        """Publish a message to a channel."""
        if not isinstance(message, str):
            message = json.dumps(message, default=str)
        return await self.client.publish(channel, message)

    def pubsub(self):
        """Get a PubSub instance for subscriptions."""
        return self._pubsub_client.pubsub()

    # ── Rate Limiting ─────────────────────────────────────────────────────────

    async def check_rate_limit(
        self,
        identifier: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int, int]:
        """
        Check if an identifier (user_id or IP) has exceeded rate limit.

        Args:
            identifier: Unique identifier for rate limiting
            limit: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_allowed, current_count, remaining)
        """
        key = f"rate_limit:{identifier}"
        pipe = self.client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds)
        results = await pipe.execute()

        current_count = results[0]
        remaining = max(0, limit - current_count)
        is_allowed = current_count <= limit

        return is_allowed, current_count, remaining

    # ── Session Storage ───────────────────────────────────────────────────────

    async def store_session(self, session_id: str, data: dict, ttl: int = 3600) -> None:
        """Store user session data with TTL."""
        await self.set(f"session:{session_id}", data, ttl=ttl)

    async def get_session(self, session_id: str) -> Optional[dict]:
        """Retrieve user session data."""
        return await self.get(f"session:{session_id}")

    async def delete_session(self, session_id: str) -> None:
        """Invalidate a user session."""
        await self.delete(f"session:{session_id}")

    # ── Convenience Cache Patterns ─────────────────────────────────────────────

    async def cache_response(
        self,
        cache_key: str,
        data: Any,
        ttl: int = 300,
    ) -> None:
        """Cache an API response for a given TTL."""
        await self.set(f"cache:{cache_key}", data, ttl=ttl)

    async def get_cached_response(self, cache_key: str) -> Optional[Any]:
        """Retrieve a cached API response."""
        return await self.get(f"cache:{cache_key}")


# ── Global Redis Client Instance ──────────────────────────────────────────────

redis_client = RedisClient()
